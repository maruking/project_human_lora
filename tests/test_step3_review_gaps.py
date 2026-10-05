"""User-required review regressions; synthetic images/rows only, no inference."""
import csv
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from test_config import script_parser, ROOT
from test_step3_canonical_gate import clean
import test_image_metrics as metrics_fixtures
import face_quality_gate as gate
from common.revision_a import eye_metrics, pixel_metrics, face_mask, load_review_settings, FormalInventory
from common.step2_inputs import FormalSource, preflight_inputs
from common.metric_generation import preflight
from common.metric_report import measure_images
from common.step3_review import successful_review, is_review_copy, require_source, review_roots
from common.step3_audit import build_artifacts
from step3_revision_a_diagnostics import supplemental_inventory


class ReviewGateTests(unittest.TestCase):
    def setUp(self):
        self.args = script_parser('face_quality_gate', {}).parse_args([])
        self.settings, _, _ = load_review_settings(ROOT/'config/step3_revision_a.example.json')

    def apply(self, **kwargs):
        row = clean(); row.update(kwargs)
        return gate.apply_gate(row, self.args)

    def test_fullbody_large_invalid_eye_regression(self):
        r = self.apply(shot_type='FULL_BODY', face_min_dimension='300',
                       left_eye_presence_ratio='.01', right_eye_presence_ratio='.2', eye_presence_valid='false')
        self.assertEqual(r['eye_presence_gate_state'], 'APPLICABLE')
        self.assertIn('one_eye_occluded', r['face_gate_reason'])
        self.assertEqual(r['diagnostic_state'], 'REJECT')
        self.assertEqual((r['left_eye_presence_ratio'], r['right_eye_presence_ratio']), ('.01', '.2'))

    def test_recorded_case_fixture(self):
        fixture=json.loads((ROOT/'tests/fixtures/step3_large_fullbody_eye_presence.json').read_text(encoding='utf-8'))
        r=self.apply(**fixture['observed'])
        self.assertIn(fixture['expected_reason'],r['face_gate_reason'])
        self.assertEqual(r['diagnostic_state'],fixture['expected_review_state'])

    def test_presence_formula_keeps_minimum_average_asymmetry(self):
        from types import SimpleNamespace as NS
        image=np.full((100,200,3),(0,100,200),dtype=np.uint8)
        image[:,100:]=140
        points=[NS(x=.5,y=.5) for _ in range(468)]
        for i,x in ((33,.2),(133,.3),(263,.7),(362,.8)):points[i]=NS(x=x,y=.5)
        left,right,valid=gate.eye_presence_metrics(image,points,200,100)
        self.assertEqual((left,right),(0,1));self.assertFalse(valid)
        # Mean=.5 is high, but the individual minimum and asymmetry still fail.

    def test_actual_analysis_populates_shared_diagnostics(self):
        import test_step3_audit as fixtures
        from types import SimpleNamespace as NS
        import contextlib
        fixture=fixtures.Step3Tests();fixture.setUp()
        try:
            backend=fixtures.backend(1)
            backend.solutions.face_detection.FaceDetection=lambda **kw:fixtures.Backend(NS(detections=[NS(score=[.9],location_data=NS(relative_bounding_box=NS(xmin=.1,ymin=.1,width=.8,height=.8)))]))
            backend.solutions.face_mesh.FACEMESH_FACE_OVAL={(33,133),(133,291),(291,61),(61,33)}
            pts=fixtures.points(eye=.15)
            with patch.object(gate,'mp',backend), patch.object(gate,'matching_landmarks',return_value=pts), \
                 patch.object(gate,'central_face_gradient',return_value=0), \
                 patch.object(gate,'eye_presence_metrics',return_value=(.2,.2,True)), \
                 patch.object(gate,'anatomical_sharpness',return_value=(2,2)), \
                 patch.object(gate,'cheek_skin_texture_metrics',return_value=(1,2,False)), \
                 patch.object(gate,'visibility',return_value=(100,'none','',dict(facemesh_detected='true'))), \
                 patch.object(gate,'sharpness',return_value=(100,100)), contextlib.redirect_stdout(io.StringIO()):
                rows,_=gate.analyze_rows([dict(fixture.rows[0])],fixture.root,fixture.args)
            r=rows[0]
            self.assertEqual(r['face_gate_status'],'ok')
            self.assertAlmostEqual(r['eye_open_min'],.15)
            self.assertEqual(r['face_exposure_state'],'NORMAL')
            self.assertEqual(r['face_exposure_roi_method'],'FACEMESH_FACE_OVAL_CONVEX_HULL')
            self.assertEqual(r['diagnostic_state'],'BORDERLINE')
            self.assertEqual(r['face_eligible'],'true')
        finally:fixture.tearDown()

    def test_new_exposure_measurement_failure_is_not_a_hardreject(self):
        import test_step3_audit as fixtures
        import contextlib
        fixture=fixtures.Step3Tests();fixture.setUp()
        try:
            with patch.object(gate,'mp',fixtures.backend(1)), \
                 patch.object(gate,'pixel_metrics',side_effect=ValueError('empty diagnostic mask')), \
                 patch.object(gate,'visibility',return_value=(100,'none','',dict(facemesh_detected='true'))), \
                 patch.object(gate,'sharpness',return_value=(100,100)), contextlib.redirect_stdout(io.StringIO()):
                # Mock detected bbox at reliable scale; keep all approved Gate settings.
                with patch.object(gate,'face_box',return_value=(10,10,160,160)):
                    rows,_=gate.analyze_rows([dict(fixture.rows[0])],fixture.root,fixture.args)
            r=rows[0]
            self.assertEqual(r['face_gate_status'],'ok');self.assertEqual(r['face_eligible'],'true')
            self.assertEqual(r['face_gate_reason'],'eligible');self.assertEqual(r['diagnostic_state'],'BORDERLINE')
            self.assertEqual(r['face_exposure_state'],'UNKNOWN')
            self.assertEqual(r['review_measurement_unavailable'],'true')
        finally:fixture.tearDown()

    def test_small_fullbody_explicit_skip(self):
        r = self.apply(shot_type='FULL_BODY', face_min_dimension='100', eye_presence_valid='false')
        self.assertEqual(r['eye_presence_gate_state'], 'SKIPPED_INSUFFICIENT_SCALE')
        self.assertNotIn('one_eye_occluded', r['face_gate_reason'])
        self.assertEqual(r['face_eligible'], 'true')

    def test_scale_uses_config_threshold_inclusive(self):
        self.args.min_face_dim_upper_body = 120
        for dim, state in [('119', 'SKIPPED_INSUFFICIENT_SCALE'), ('120','APPLICABLE')]:
            self.assertEqual(self.apply(shot_type='FULL_BODY', face_min_dimension=dim)['eye_presence_gate_state'],state)

    def test_missing_mesh_or_individual_evidence_is_not_occlusion(self):
        for change in (dict(facemesh_detected='false'), dict(left_eye_presence_ratio='')):
            r=self.apply(**change)
            self.assertEqual(r['eye_presence_gate_state'], 'NOT_APPLICABLE_MISSING_MEASUREMENT')
            self.assertNotIn('one_eye_occluded',r['face_gate_reason'])

    def test_halfeye_shared_measurement_borderline_only(self):
        evidence=eye_metrics(.15,.35,self.settings)
        r=self.apply(**evidence)
        self.assertEqual(r['left_eye_open_ratio'],.15);self.assertEqual(r['right_eye_open_ratio'],.35)
        self.assertEqual(r['eye_open_min'],.15)
        self.assertEqual(r['diagnostic_state'],'BORDERLINE')
        self.assertEqual(r['face_eligible'],'true');self.assertEqual(r['face_gate_reason'],'eligible')

    def test_blink_diagnostic_only(self):
        r=self.apply(**eye_metrics(.05,.2,self.settings))
        self.assertEqual(r['half_eye_suspected'],'true');self.assertEqual(r['face_eligible'],'true')

    def test_exposure_shared_formula_borderline_only(self):
        gray=np.full((12,12),255,np.uint8);mask=np.full_like(gray,255)
        measured=pixel_metrics(gray,mask,None,self.settings)
        r=self.apply(**{k:measured[k] for k in ('face_highlight_clip_ratio','face_bright_region_ratio','face_dynamic_range','face_exposure_state')})
        self.assertEqual(r['face_highlight_clip_ratio'],1)
        self.assertEqual(r['face_dynamic_range'],0)
        self.assertEqual(r['diagnostic_state'],'BORDERLINE');self.assertEqual(r['face_eligible'],'true')

    def test_diagnostics_never_override_hardreject(self):
        r=self.apply(face_laplacian_canonical_192='30',eye_openness_state='BORDERLINE',face_exposure_state='OVEREXPOSED')
        self.assertEqual(r['diagnostic_state'],'REJECT');self.assertEqual(r['face_gate_reason'],'face_blurry')
        self.assertEqual(r['half_eye_suspected'],'true');self.assertEqual(r['overexposure_white_haze_suspected'],'true')

    def test_native_blur_alone_and_canonical_threshold_unchanged(self):
        r=self.apply(laplacian_score='0',face_laplacian_score='0')
        self.assertEqual(r['diagnostic_state'],'PASS')
        self.assertEqual(self.args.min_face_laplacian_canonical,36.901392)

    def test_face_mask_shared_roi(self):
        mask,method=face_mask(None,(2,3,5,4),12,12,())
        self.assertEqual(np.count_nonzero(mask),20);self.assertEqual(method,'BBOX_FALLBACK_NO_MESH')

    def test_measured_zero_diagnostic_not_counted_missing(self):
        from common.step3_audit import distribution
        records=distribution([self.apply(face_highlight_clip_ratio=0.0,face_dynamic_range=0.0)])
        for r in records:
            if r['metric'] in ('face_highlight_clip_ratio','face_dynamic_range'):
                self.assertEqual(r['count'],1);self.assertEqual(r['missing_count'],0)

    def test_summary_counts_and_full_rows(self):
        rows=[self.apply(),self.apply(eye_openness_state='BORDERLINE'),self.apply(face_laplacian_canonical_192='30')]
        for i,r in enumerate(rows):r.update(filename=f'sample/{i}.png',frame_id=f'sample/{i}.png')
        artifacts=build_artifacts(rows,['filename','frame_id'],dict(frame_count=3,video_count=1),'fixture',vars(self.args))
        summary=json.loads(artifacts['step3_summary.json'])
        self.assertEqual(summary['review_counts']['PASS'],1);self.assertEqual(summary['review_counts']['BORDERLINE'],1)
        self.assertEqual(summary['review_counts']['REJECT'],1);self.assertEqual(summary['review_counts']['eye_presence_applicable'],3)
        self.assertEqual(len(list(csv.DictReader(io.StringIO(artifacts['dataset.csv'].decode('utf-8-sig'))))),3)


class ReviewCopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.raw=self.root/'raw';self.reports=self.root/'reports'
        self.raw.mkdir();self.reports.mkdir();self.paths={};self.rows=[]
        for i,state in enumerate(('PASS','BORDERLINE','REJECT')):
            rel=Path('video')/f'{i}.png';src=self.raw/rel;src.parent.mkdir(exist_ok=True);src.write_bytes(bytes([i]))
            self.paths[i]=(src,rel);self.rows.append(dict(diagnostic_state=state,face_eligible=str(state!='REJECT').lower()))
        for group in ('passed','borderline'):
            p=self.reports/group;p.mkdir();(p/'stale.png').write_bytes(b'old')
        (self.reports/'evidence.csv').write_bytes(b'immutable')

    def test_current_groups_only_source_and_other_report_unchanged(self):
        with successful_review(self.rows,self.paths,self.reports,self.raw):pass
        self.assertEqual([p.relative_to(self.reports/'passed').as_posix() for p in (self.reports/'passed').rglob('*.png')],['video/0.png'])
        self.assertEqual([p.relative_to(self.reports/'borderline').as_posix() for p in (self.reports/'borderline').rglob('*.png')],['video/1.png'])
        self.assertEqual((self.reports/'evidence.csv').read_bytes(),b'immutable')
        self.assertEqual([p[0].read_bytes() for p in self.paths.values()],[b'\0',b'\1',b'\2'])

    def test_copy_failure_keeps_previous_groups(self):
        with patch('common.step3_review.shutil.copy2',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                with successful_review(self.rows,self.paths,self.reports,self.raw):self.fail('must not publish')
        for group in ('passed','borderline'):self.assertEqual((self.reports/group/'stale.png').read_bytes(),b'old')

    def test_successful_all_rejected_clears_stale_groups(self):
        with successful_review([self.rows[2]],{},self.reports,self.raw):pass
        for group in ('passed','borderline'):self.assertEqual(list((self.reports/group).iterdir()),[])

    def test_report_publication_failure_rolls_back_both_groups(self):
        with self.assertRaises(OSError):
            with successful_review(self.rows,self.paths,self.reports,self.raw):raise OSError('report write failed')
        for group in ('passed','borderline'):self.assertEqual((self.reports/group/'stale.png').read_bytes(),b'old')

    def test_second_directory_swap_failure_rolls_back(self):
        import os
        replace=os.replace
        def fail_second(src,dest):
            if Path(src).name=='new-borderline':raise OSError('swap blocked')
            return replace(src,dest)
        with patch('common.step3_review.os.replace',side_effect=fail_second):
            with self.assertRaises(OSError):
                with successful_review(self.rows,self.paths,self.reports,self.raw):pass
        for group in ('passed','borderline'):self.assertTrue((self.reports/group/'stale.png').exists())

    def test_overlap_and_escape_rejected(self):
        with self.assertRaises(ValueError):
            with successful_review(self.rows,self.paths,self.raw,self.raw):pass
        self.paths[0]=(self.paths[0][0],Path('../escape.png'))
        with self.assertRaises(ValueError):
            with successful_review(self.rows,self.paths,self.reports,self.raw):pass

    def test_all_cli_image_inputs_reject_temporary_review_sources(self):
        for module in ('score_blur','face_quality_gate','classify_face_pose','face_deduplication','evaluate_identity'):
            parser=script_parser(module,{})
            import contextlib
            option='--input' if module=='score_blur' else '--images'
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                parser.parse_args([option,str(self.reports/'passed')])

    def test_custom_configured_reports_roots_excluded(self):
        roots=review_roots({'paths':{'reports_dir':str(self.root/'custom-audit')}})
        for root in roots:
            self.assertTrue(is_review_copy(root/'v/x.png'))
            with self.assertRaises(ValueError):require_source(root)

    def test_formal_and_supplemental_scans_exclude_review_copies(self):
        supplement=self.raw/'stills';supplement.mkdir();(supplement/'real.png').write_bytes(b'real')
        copies=supplement/'reports/passed';copies.mkdir(parents=True);(copies/'copy.png').write_bytes(b'copy')
        for view in (FormalSource(self.raw,supplement),FormalInventory(self.raw,supplement)):
            self.assertFalse(any(is_review_copy(p) for p in view.rglob('*')))
        files,inventory=supplemental_inventory(supplement)
        self.assertEqual([p.name for p in files],['real.png'])
        self.assertEqual(set(inventory),{'real.png'})
        with self.assertRaises(ValueError):preflight_inputs(self.reports/'passed',self.root/'missing-manifests')

    def test_deleting_review_copies_does_not_change_formal_lineage(self):
        fixture=metrics_fixtures.MetricsTests();fixture.setUp()
        try:
            fixture.image();manifests=fixture.generation()
            before=preflight(fixture.input,manifests)
            for group in ('passed','borderline'):
                out=fixture.input/'reports'/group;out.mkdir(parents=True);(out/'copy.png').write_bytes(b'ignored')
            with_copies=preflight(fixture.input,manifests)
            shutil.rmtree(fixture.input/'reports/passed');shutil.rmtree(fixture.input/'reports/borderline')
            after=preflight(fixture.input,manifests)
            self.assertEqual(before[3],with_copies[3]);self.assertEqual(before[3],after[3])
            self.assertEqual(before[2],after[2])
        finally:fixture.doCleanups()

    def test_main_always_wires_review_without_copy_review_and_skips_failed_partial(self):
        import contextlib
        import hashlib
        from types import SimpleNamespace
        report=self.reports/'step2.csv';report.write_text('filename\nvideo/0.png\n',encoding='utf-8')
        sha=hashlib.sha256(report.read_bytes()).hexdigest()
        config={'paths':{'raw_frames_dir':str(self.raw),'reports_dir':str(self.reports),
                         'manifests_dir':str(self.root/'manifests')}}
        for failed,partial in ((False,False),(True,False),(False,True)):
            def analysis(rows,root,args):
                for r in rows:r.update(face_gate_status='error' if failed else 'ok',face_eligible='false' if failed else 'true')
                return rows,self.paths
            argv=['face_quality_gate.py','--report',str(report),'--output',str(self.reports/'result.csv')]
            if partial:argv+=['--limit','1']
            with patch.object(gate,'load_for_cli',return_value=config), patch.object(gate,'mp',SimpleNamespace(solutions=object())), \
                 patch.object(gate,'validate_input',return_value=({},dict(frame_count=1,video_count=1),sha)), \
                 patch.object(gate,'manifest_lock',side_effect=lambda p:contextlib.nullcontext()), \
                 patch.object(gate,'analyze_rows',side_effect=analysis), \
                 patch.object(gate,'build_artifacts',return_value={'dataset.csv':b'fixture'}), \
                 patch.object(gate,'publish') as publish, \
                 patch.object(gate,'successful_review',side_effect=lambda *a:contextlib.nullcontext()) as materialize, \
                 patch('sys.argv',argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(),1 if failed else 0)
                self.assertEqual(materialize.call_count,0 if failed or partial else 1)
                self.assertEqual(publish.call_count,1)


if __name__=='__main__':unittest.main()
