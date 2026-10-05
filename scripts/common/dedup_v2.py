"""Conservative duplicate graph; quality authority is stored STEP3 BEST only."""
from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import math

from face_deduplication import compute_phash, hamming_dist
from common.pose_composition import POSE_BINS, SCALE_BINS

VERSION = 'step5_dedup_v2'
RULE_KEYS = ('phash_threshold', 'temporal_phash_threshold', 'angle_threshold',
             'tight_angle_threshold', 'time_window')
FIELDS = ('step5_version', 'step5_status', 'dedup_cluster_id', 'dedup_role',
          'cluster_size', 'representative_frame_id', 'cluster_rank',
          'duplicate_evidence', 'exact_sha_duplicate', 'global_phash', 'face_phash',
          'global_phash_distance_to_representative', 'face_phash_distance_to_representative',
          'yaw_pitch_distance_to_representative', 'temporal_distance_to_representative',
          'cluster_max_pose_spread', 'cluster_chain_warning',
          'cluster_min_temporal_index', 'cluster_max_temporal_index',
          'cluster_max_global_phash_distance', 'cluster_max_face_phash_distance',
          'cluster_evidence_types', 'step5_error', 'duplicate_status', 'duplicate_group')
POOL_ROLES = ('UNIQUE', 'REPRESENTATIVE')


def eligible(row):
    return str(row.get('ranking_eligible', '')).lower() == 'true'


def number(value):
    if value in ('', None):
        return None
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Nonfinite number')
    return value


def ordering(row):
    return (-float(row['best_score']), int(row['global_rank']), row['frame_id'])


def pose(row):
    if row.get('step4_status') != 'MEASURED' or row.get('pose_bin') == 'NOT_EVALUABLE':
        return None
    yaw, pitch = number(row.get('yaw')), number(row.get('pitch'))
    return (yaw, pitch) if yaw is not None and pitch is not None else None


def angle(a, b):
    pa, pb = pose(a), pose(b)
    return math.dist(pa, pb) if pa is not None and pb is not None else None


def temporal(a, b):
    if a['input_kind'] == b['input_kind'] == 'formal_video' and a['video_id'] == b['video_id']:
        if a.get('temporal_index') and b.get('temporal_index'):
            return abs(int(a['temporal_index']) - int(b['temporal_index']))
    return None


def distance(a, b, key):
    return hamming_dist(a[key], b[key]) if a.get(key) is not None and b.get(key) is not None else None


def near_evidence(a, b, ha, hb, rules):
    """Exact SHA is handled separately; missing pose never becomes zero."""
    gap = angle(a, b)
    if gap is None:
        return []
    glob, face = distance(ha, hb, 'global'), distance(ha, hb, 'face')
    if glob is None:
        return []
    evidence = []
    if a['input_kind'] == b['input_kind'] == 'formal_video' and a['video_id'] == b['video_id']:
        dt = temporal(a, b)
        if (dt is not None and dt <= rules['time_window'] and gap <= rules['angle_threshold']
                and (glob <= rules['temporal_phash_threshold'] or
                     (face is not None and face <= rules['temporal_phash_threshold']))):
            evidence.append('VIDEO_TEMPORAL_NEAR')
        if gap <= rules['tight_angle_threshold'] and (glob <= rules['phash_threshold'] or
                (face is not None and face <= rules['phash_threshold'])):
            evidence.append('VIDEO_STRONG_SIMILARITY')
    elif a['input_kind'] == b['input_kind'] == 'supplemental_still':
        if gap <= rules['tight_angle_threshold'] and glob <= rules['phash_threshold'] and \
                face is not None and face <= rules['phash_threshold']:
            evidence.append('SUPPLEMENTAL_STILL_NEAR')
    return evidence


def stable_id(members):
    material = '\n'.join(sorted(row['frame_id'] for row in members))
    return 'DUP_' + hashlib.sha256(material.encode('utf-8')).hexdigest()


def annotate(rows, hashes, errors, rules, partial=False):
    outputs = [dict(row, **{key: '' for key in FIELDS}) for row in rows]
    for row in outputs:
        row['step5_version'] = VERSION
        row['exact_sha_duplicate'] = 'false'
        row['cluster_chain_warning'] = 'false'
        if not eligible(row):
            row.update(step5_status='NOT_APPLICABLE_STEP3_FATAL',
                       dedup_role='NOT_APPLICABLE_STEP3_FATAL', duplicate_status='not_applicable')
        elif row['frame_id'] not in hashes:
            row.update(step5_status='ERROR' if not partial or row['frame_id'] in errors else 'PARTIAL_NOT_ANALYZED',
                       dedup_role='ERROR', duplicate_status='error',
                       step5_error=errors.get(row['frame_id'], 'not_analyzed_limit'))
    valid = sorted((i for i, row in enumerate(rows) if eligible(row) and row['frame_id'] in hashes),
                   key=lambda i: rows[i]['frame_id'])
    parent = {i: i for i in valid}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    edges = []
    def edge(i, j, kinds):
        if kinds:
            parent[find(j)] = find(i)
            edges.append((i, j, kinds))

    exact = defaultdict(list)
    sources = defaultdict(list)
    for i in valid:
        row = rows[i]
        exact[row['image_sha256'].lower()].append(i)
        key = ('video', row['video_id']) if row['input_kind'] == 'formal_video' else ('still',)
        sources[key].append(i)
    for group in exact.values():
        for i, j in combinations(group, 2):
            edge(i, j, ['EXACT_DUPLICATE'])
    for group in sources.values():
        for i, j in combinations(group, 2):
            # Byte-identical edges already have definitive evidence.
            if rows[i]['image_sha256'].lower() == rows[j]['image_sha256'].lower():
                continue
            edge(i, j, near_evidence(rows[i], rows[j], hashes[rows[i]['frame_id']],
                                   hashes[rows[j]['frame_id']], rules))
    groups = defaultdict(list)
    for i in valid:
        groups[find(i)].append(i)
    incident = defaultdict(set)
    cluster_edges = defaultdict(list)
    for i, j, kinds in edges:
        incident[i].update(kinds)
        incident[j].update(kinds)
        cluster_edges[find(i)].extend(kinds)
    clusters = []
    for root, indices in groups.items():
        members = sorted(indices, key=lambda i: ordering(rows[i]))
        rep = members[0]
        cluster_id = stable_id([rows[i] for i in members])
        spreads = [angle(rows[i], rows[j]) for i, j in combinations(members, 2)]
        spread = max((v for v in spreads if v is not None), default=None)
        kinds = sorted(set(cluster_edges[root]))
        near_kinds = set(kinds) - {'EXACT_DUPLICATE'}
        bound = rules['angle_threshold'] if 'VIDEO_TEMPORAL_NEAR' in kinds else rules['tight_angle_threshold']
        warning = bool(near_kinds and spread is not None and spread > bound)
        same_video = (all(rows[i]['input_kind'] == 'formal_video' for i in members)
                      and len({rows[i]['video_id'] for i in members}) == 1)
        times = [int(rows[i]['temporal_index']) for i in members] if same_video else []
        max_glob = max(distance(hashes[rows[i]['frame_id']], hashes[rows[rep]['frame_id']], 'global')
                       for i in members)
        face_distances = [distance(hashes[rows[i]['frame_id']], hashes[rows[rep]['frame_id']], 'face')
                          for i in members]
        max_face = max((d for d in face_distances if d is not None), default=None)
        for rank, i in enumerate(members, 1):
            row, h = outputs[i], hashes[rows[i]['frame_id']]
            role = 'UNIQUE' if len(members) == 1 else 'REPRESENTATIVE' if rank == 1 else 'DUPLICATE_MEMBER'
            row.update(step5_status='MEASURED', dedup_cluster_id=cluster_id, dedup_role=role,
                       cluster_size=len(members), representative_frame_id=rows[rep]['frame_id'], cluster_rank=rank,
                       duplicate_evidence=';'.join(sorted(incident[i])) or 'NONE',
                       exact_sha_duplicate=str('EXACT_DUPLICATE' in incident[i]).lower(),
                       global_phash=f"{h['global']:016x}",
                       face_phash=f"{h['face']:016x}" if h.get('face') is not None else 'MISSING',
                       global_phash_distance_to_representative=distance(h, hashes[rows[rep]['frame_id']], 'global'),
                       face_phash_distance_to_representative=distance(h, hashes[rows[rep]['frame_id']], 'face'),
                       yaw_pitch_distance_to_representative=angle(rows[i], rows[rep]),
                       temporal_distance_to_representative=temporal(rows[i], rows[rep]),
                       cluster_max_pose_spread=spread, cluster_chain_warning=str(warning).lower(),
                       cluster_min_temporal_index=min(times) if times else None,
                       cluster_max_temporal_index=max(times) if times else None,
                       cluster_max_global_phash_distance=max_glob, cluster_max_face_phash_distance=max_face,
                       cluster_evidence_types=';'.join(kinds) or 'NONE', duplicate_group=cluster_id,
                       duplicate_status={'UNIQUE': 'unique', 'REPRESENTATIVE': 'representative',
                                         'DUPLICATE_MEMBER': 'duplicate'}[role])
        clusters.append([outputs[i] for i in members])
    return outputs, sorted(clusters, key=lambda c: c[0]['dedup_cluster_id']), edges


def distributions(rows):
    return dict(pose={key: sum(r['pose_bin'] == key for r in rows) for key in POSE_BINS},
                face_scale={key: sum(r['face_scale_bin'] == key for r in rows) for key in SCALE_BINS})


def summarize(rows, clusters, edges, partial=False):
    before = [r for r in rows if eligible(r)]
    after = [r for r in rows if r['dedup_role'] in POOL_ROLES]
    roles = Counter(r['dedup_role'] for r in rows)
    sizes = [len(c) for c in clusters]
    edge_counts = Counter(kind for _, _, kinds in edges for kind in kinds)
    before_d, after_d = distributions(before), distributions(after)
    retention = {key: dict(before_count=before_d['pose'][key], after_count=after_d['pose'][key],
                          retention_ratio=after_d['pose'][key]/before_d['pose'][key] if before_d['pose'][key] else None,
                          status='POSE_RETENTION_WARNING' if after_d['pose'][key] < before_d['pose'][key] else 'NO_REDUCTION',
                          rare_pose_context=key.startswith('PROFILE_')) for key in POSE_BINS}
    cross = []
    for p in POSE_BINS:
        for s in SCALE_BINS:
            b = [r for r in before if r['pose_bin'] == p and r['face_scale_bin'] == s]
            a = [r for r in after if r['pose_bin'] == p and r['face_scale_bin'] == s]
            cross.append(dict(pose_bin=p, face_scale_bin=s, before_count=len(b), after_count=len(a),
                              retention_ratio=len(a)/len(b) if b else None,
                              representative_count=sum(r['dedup_role'] == 'REPRESENTATIVE' for r in a),
                              unique_count=sum(r['dedup_role'] == 'UNIQUE' for r in a)))
    source_summary = []
    by_source = defaultdict(list)
    for r in before:
        by_source[(r['input_kind'], r['video_id'] if r['input_kind'] == 'formal_video' else r['source_id'])].append(r)
    for (kind, source), members in sorted(by_source.items()):
        source_summary.append(dict(input_kind=kind, source_id=source, eligible_members=len(members),
            resulting_clusters=len({r['dedup_cluster_id'] for r in members if r['dedup_cluster_id']}),
            duplicate_members=sum(r['dedup_role'] == 'DUPLICATE_MEMBER' for r in members),
            representative_unique_count=sum(r['dedup_role'] in POOL_ROLES for r in members),
            largest_cluster=max((int(r['cluster_size']) for r in members if r['cluster_size']), default=0),
            best_step3_score=max(float(r['best_score']) for r in members)))
    summary = dict(step5_version=VERSION, publication_status='PARTIAL' if partial else 'FAILED' if roles['ERROR'] else 'COMPLETE',
        total_rows=len(rows), ranking_eligible_count=len(before), fatal_not_applicable_count=len(rows)-len(before),
        total_analyzed=sum(sizes), roles=dict(roles), total_clusters=len(clusters),
        unique_clusters=sum(n == 1 for n in sizes), multi_member_clusters=sum(n > 1 for n in sizes),
        exact_duplicate_count=sum(r['exact_sha_duplicate'] == 'true' for r in rows),
        near_duplicate_count=sum(bool(set(r['duplicate_evidence'].split(';')) &
                                     {'VIDEO_TEMPORAL_NEAR','VIDEO_STRONG_SIMILARITY','SUPPLEMENTAL_STILL_NEAR'}) for r in rows),
        duplicate_member_ratio=roles['DUPLICATE_MEMBER']/len(before) if before else None,
        cluster_sizes=dict(size_1=sum(n == 1 for n in sizes), size_2=sum(n == 2 for n in sizes),
                           size_3_5=sum(3 <= n <= 5 for n in sizes), size_6_plus=sum(n >= 6 for n in sizes),
                           largest_cluster=max(sizes, default=0)), evidence_edges=dict(edge_counts),
        exact_sha_clusters=sum('EXACT_DUPLICATE' in c[0]['cluster_evidence_types'] for c in clusters),
        chain_warning_clusters=sum(c[0]['cluster_chain_warning'] == 'true' for c in clusters),
        before=before_d, after=after_d, pose_retention=retention, sources=source_summary,
        warning_policy='Any observed pose-count reduction is highlighted for review; no magnitude threshold, quota or automatic protection.',
        count_semantics='Evidence counts are incident rows, not disjoint duplicate classes; edge types can overlap.',
        final_training_selection=False, quotas_applied=False)
    return summary, cross
