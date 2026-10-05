import copy
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from common.config import load_config
from common.revision_b import select
from select_revision_b import artifacts, publish, read_csv, main, csv_bytes


class RevisionBTests(unittest.TestCase):
    def setUp(self):
        config=load_config(ROOT/'config/config.example.yaml')
        self.settings=config['step7_revision_b']
        self.pose=config['step4_pose']

    def row(self,i,group='A',pose='FRONT',shot='UPPER_BODY'):
        name=f'video{i%12:02d}/frame{i:03d}.png'
        return dict(frame_id=name,filename=name,video_id=f'video{i%12:02d}',temporal_index=str(i),
                    relative_path='work/frames_raw/'+name,selection_group=group,
                    selection_group_source='HUMAN_CONFIRMED',selection_review_status='CONFIRMED',
                    reserve_use_allowed='true' if group=='B' else 'false',selection_group_reason='human_review',
                    pose_bucket=pose,pose_status='ok',pose_yaw='0',shot_type=shot,
                    duplicate_group=f'g{i}',duplicate_status='unique',face_quality_score=str(i),
                    identity_passed='true',expression_bucket='NATURAL',image_sha256='fixturehash')

    def pool(self):
        return [self.row(i,pose=('FRONT','LEFT_3Q','LEFT_PROFILE')[i%3],
                         shot=('CLOSE_UP','UPPER_BODY','FULL_BODY')[(i//3)%3]) for i in range(90)]

    def simple_settings(self):
        settings=copy.deepcopy(self.settings)
        settings.update(angle_min={'FRONTAL':0,'THREE_QUARTER':0,'SIDE':1},
                        angle_max={'FRONTAL':45,'THREE_QUARTER':45,'SIDE':45},
                        composition_min={'CLOSE_UP':0,'UPPER_BODY':0,'FULL_BODY':0},
                        composition_max={'CLOSE_UP':45,'UPPER_BODY':45,'FULL_BODY':45},
                        pitch_min={'LOOKING_UP':0,'LOOKING_DOWN':0})
        return settings

    def test_primary_coverage_deterministic_and_full_audit(self):
        rows=self.pool()
        rows[0]['pose_bucket']='LOOKING_UP';rows[3]['pose_bucket']='LOOKING_DOWN'
        first,summary=select(rows,self.settings,self.pose,True)
        second,again=select(list(reversed(rows)),self.settings,self.pose,True)
        self.assertEqual(first,second);self.assertEqual(summary,again)
        self.assertEqual(len(first),90);self.assertEqual(summary['selected_count'],40)
        self.assertFalse(summary['remaining_shortages']);self.assertEqual(summary['B_promotions'],0)
        self.assertLessEqual(max(summary['distributions']['distribution_source'].values()),6)
        self.assertTrue(all(n==1 for n in summary['distributions']['selection_duplicate_group'].values()))

    def test_only_necessary_B_promotion_can_replace_redundant_A(self):
        rows=[self.row(i) for i in range(40)]+[self.row(100,'B','LEFT_PROFILE'),self.row(101,'B')]
        audit,summary=select(rows,self.simple_settings(),self.pose,True)
        self.assertEqual(summary['selected_count'],40);self.assertEqual(summary['B_promotions'],1)
        promoted=[r for r in audit if r['final_selection_role']=='BORDERLINE_PROMOTED']
        self.assertEqual(promoted[0]['frame_id'],rows[40]['frame_id'])
        self.assertIn('coverage:angle_bucket:SIDE',promoted[0]['promotion_reason'])
        self.assertEqual(next(r for r in audit if r['frame_id']==rows[41]['frame_id'])['final_selection_role'],'RESERVE')

    def test_unconfirmed_B_and_C_never_resurrect_for_shortage(self):
        rows=[self.row(i) for i in range(34)]+[self.row(100,'B','LEFT_PROFILE'),self.row(101,'C','LEFT_PROFILE')]
        rows[34].update(selection_group_source='PROVISIONAL_DIAGNOSTIC',selection_review_status='UNDECIDED',reserve_use_allowed='false')
        audit,summary=select(rows,self.simple_settings(),self.pose,True)
        self.assertEqual(summary['selected_count'],34)
        self.assertEqual(summary['remaining_shortages']['total_count'],1)
        self.assertTrue(all(r['selected']=='no' for r in audit if r['selection_group']!='A'))
        pending=next(r for r in audit if r['selection_group']=='B')
        self.assertEqual(pending['final_selection_role'],'REVIEW_PENDING_RESERVE')

    def test_minimum_count_B_fill_stops_at_35(self):
        settings=self.simple_settings();settings['angle_min']['SIDE']=0
        rows=[self.row(i) for i in range(34)]+[self.row(i,'B') for i in range(100,110)]
        audit,summary=select(rows,settings,self.pose,True)
        self.assertEqual(summary['selected_count'],35);self.assertEqual(summary['B_promotions'],1)
        self.assertEqual(next(r for r in audit if r['selected']=='yes' and r['selection_group']=='B')['promotion_reason'],'minimum_count_shortage')

    def test_duplicate_identity_missing_pose_and_expression_evidence(self):
        rows=self.pool()
        rows[1]['duplicate_group']=rows[0]['duplicate_group']
        rows[2]['identity_passed']='false';rows[3]['pose_status']='error';rows[4]['expression_bucket']='EXTREME'
        audit,summary=select(rows,self.settings,self.pose,True)
        for i in (2,3,4):
            self.assertEqual(next(r for r in audit if r['frame_id']==rows[i]['frame_id'])['selected'],'no')
        self.assertLessEqual(sum(r['selected']=='yes' for r in audit if r['duplicate_group']==rows[0]['duplicate_group']),1)
        rows[5]['expression_bucket']='UNKNOWN'
        _,summary=select(rows,self.settings,self.pose,False)
        self.assertEqual(summary['identity_safety'],'UNAVAILABLE_REQUIRES_HUMAN_REVIEW')

    def test_reject_conflict_and_invalid_group_fail(self):
        for change in ({'human_accept':'REJECT'},{'selection_group':'UNDECIDED'}):
            row=self.row(1);row.update(change)
            with self.assertRaises(ValueError): select([row],self.settings,self.pose,True)
        invalid=copy.deepcopy(self.settings);invalid['min_count']=30
        with self.assertRaises(ValueError): select([self.row(1)],invalid,self.pose,True)
        invalid=copy.deepcopy(self.settings);invalid['angle_min']={'FRONTAL':20,'THREE_QUARTER':24,'SIDE':12}
        with self.assertRaises(ValueError): select([self.row(1)],invalid,self.pose,True)

    def test_reports_empty_subsets_repeatability_and_publication_rollback(self):
        rows,summary=select([self.row(1,'C')],self.settings,self.pose,True)
        contents=artifacts(rows,summary,self.settings,{'fixture.csv':'hash'})
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder);run=publish(output,contents)
            self.assertEqual(run,publish(output,contents))
            self.assertEqual(len(read_csv(output/'step7_candidate_selection.csv')[0]),1)
            self.assertEqual(len((output/'step7_final_selected_35_45.csv').read_text(encoding='utf-8-sig').splitlines()),1)
            replace=__import__('select_revision_b').os.replace
            def fail_summary(src,dest):
                if Path(dest).name=='STEP7_SELECTION_SUMMARY.md': raise OSError('simulated locked report')
                return replace(src,dest)
            changed={name:body+b'\n' for name,body in contents.items()}
            with patch('select_revision_b.os.replace',side_effect=fail_summary),self.assertRaises(OSError): publish(output,changed)
            for name,body in contents.items(): self.assertEqual((output/name).read_bytes(),body)

    def test_minimal_end_to_end_joins_stale_sidecar_and_preservation(self):
        import test_image_metrics as fixtures
        fixture=fixtures.MetricsTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.image('video02','video02_001.png');fixture.image('video10','video10_001.png')
        manifests=fixture.generation()
        still=fixture.image('extra','portrait.png')
        self.assertEqual(fixture.run_with_stills(manifests,still.parent),0)
        formal,hash2=read_csv(fixture.root/'report.csv')
        summary2=json.loads((fixture.root/'step2_summary.json').read_text())
        generation=summary2['input_generation']['sha256']
        official={name:dict(row,face_eligible='true',face_gate_reason='eligible') for name,row in formal.items()}
        def write(name,records):
            fields=sorted(set().union(*(set(r) for r in records.values())))
            path=fixture.root/name;path.write_bytes(csv_bytes(list(records.values()),fields));return path
        step3=write('step3_dataset_report.csv',official)
        (fixture.root/'step3_summary.json').write_text(json.dumps(dict(status='PASS',partial=False,
            input_generation=summary2['input_generation'],step2_csv_sha256=hash2,step3_csv_sha256=hashlib.sha256(step3.read_bytes()).hexdigest())))
        groups={name:dict(frame_id=name,filename=name,selection_group='A',selection_group_source='HUMAN_CONFIRMED',
                  selection_review_status='CONFIRMED',reserve_use_allowed='false',dataset_generation_id=generation,
                  image_sha256=hashlib.sha256((fixture.input/name).read_bytes()).hexdigest()) for name in formal}
        name=still.relative_to(fixture.input).as_posix()
        groups[name]=dict(groups[next(iter(groups))],frame_id=name,filename=name,selection_group='B',
                          reserve_use_allowed='true',dataset_generation_id='supplemental-test',image_sha256=hashlib.sha256(still.read_bytes()).hexdigest())
        groups_path=write('groups.csv',groups)
        pose={name:dict(row,pose_status='ok',pose_bucket='FRONT',pose_yaw='0',shot_type='UPPER_BODY') for name,row in official.items()}
        pose[name]=dict(groups[name],pose_status='ok',pose_bucket='LEFT_PROFILE',pose_yaw='50',shot_type='FULL_BODY')
        pose_path=write('pose.csv',pose)
        duplicate={name:dict(row,duplicate_status='unique',duplicate_group='dup:'+name,face_quality_score='1') for name,row in pose.items()}
        duplicate_path=write('duplicate.csv',duplicate)
        identity={name:dict(row,identity_passed='true') for name,row in duplicate.items()}
        identity_path=write('identity.csv',identity)
        config=load_config(ROOT/'config/config.example.yaml')
        settings=config['step7_revision_b']
        settings.update(universe=str(fixture.root/'report.csv'),step2_summary=str(fixture.root/'step2_summary.json'),
                        step3=str(step3),selection_groups=str(groups_path),pose=str(pose_path),
                        duplicates=str(duplicate_path),identity=str(identity_path))
        config['paths'].update(raw_frames_dir=str(fixture.input),manifests_dir=str(manifests),reports_dir=str(fixture.root/'result'))
        def execute():
            with patch('select_revision_b.load_for_cli',return_value=config),patch.object(sys,'argv',['select_revision_b.py']),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                return main()
        self.assertEqual(execute(),2)  # Honest shortage; audit still published.
        result=fixture.root/'result/step7_candidate_selection.csv'
        self.assertEqual(len(read_csv(result)[0]),3)
        before=result.read_bytes()
        groups[next(iter(formal))]['dataset_generation_id']='stale'
        write('groups.csv',groups)
        self.assertEqual(execute(),1);self.assertEqual(result.read_bytes(),before)
        groups[next(iter(formal))]['dataset_generation_id']=generation
        write('groups.csv',groups)
        duplicate[next(iter(formal))]['face_gate_reason']='changed_historical_evidence'
        write('duplicate.csv',duplicate)
        self.assertEqual(execute(),1);self.assertEqual(result.read_bytes(),before)


if __name__=='__main__': unittest.main()
