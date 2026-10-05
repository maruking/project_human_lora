"""Validate explicit, version-scoped feedback without using preferences as scores."""
CURRENT_RANKING_VERSION='best_rank_v2.2'


def confirmed_rejects(rows, history, feedback, summary):
    version=summary.get('version')
    if version!=CURRENT_RANKING_VERSION or summary.get('review_ranking_version')!=version:
        raise ValueError('Current review ranking version cannot be proven')
    if history.get('version')!=2 or version not in history.get('review_history',{}):
        raise ValueError('Authoritative current-version review history missing')
    group=history['review_history'][version]
    records=group['records']; rounds=group['rounds']
    if rounds!=summary.get('review_rounds') or any(
            r.get('publication_status')!='COMPLETE' or r.get('ranking_version')!=version for r in rounds):
        raise ValueError('Current review rounds differ from ranking summary or are incomplete')
    current={r['frame_id']:r for r in rows}
    if len(current)!=len(rows) or len({r['frame_id'] for r in records})!=len(records):
        raise ValueError('Ambiguous review frame identities')
    for record in records:
        row=current.get(record['frame_id'])
        if record.get('ranking_version')!=version or record.get('review_state') not in ('PENDING','REVIEW_REJECT'):
            raise ValueError('Invalid current-version review decision')
        if row is None or row.get('ranking_version')!=version or any(
                not record.get(k) or record[k]!=row.get(k) for k in ('image_sha256','dataset_generation_id')):
            raise ValueError('Review identity/hash/generation mismatch')
        if record.get('review_round') not in {r['review_round'] for r in rounds}:
            raise ValueError('Review decision lacks a completed round')
        # Feedback has no standalone ranking-output hash. Bind all stored, shared
        # immutable ranking columns to the hash-verified current output instead.
        if any(str(v)!=str(row[k]) for k,v in record.items() if k in row and
                not k.startswith(('review_','historical_','copy_')) and k!='shown_to_maru'):
            raise ValueError('Review record belongs to a different ranking output')
        if any(k not in record for k in ('best_score','global_rank')):
            raise ValueError('Review lacks ranking-output evidence')
    rejects={r['frame_id']:r for r in records if r['review_state']=='REVIEW_REJECT'}
    if len(records)!=summary.get('shown_count') or len(rejects)!=summary.get('review_reject_count'):
        raise ValueError('Current review counts differ from ranking summary')
    if len({r['frame_id'] for r in feedback})!=len(feedback) or {r['frame_id'] for r in feedback}!=set(rejects):
        raise ValueError('Reject feedback and version-scoped history disagree')
    for record in feedback:
        if any(str(record.get(k,''))!=str(rejects[record['frame_id']][k]) for k in
                ('ranking_version','frame_id','image_sha256','dataset_generation_id','review_state','review_round','best_score','global_rank')):
            raise ValueError('Reject feedback identity/decision/ranking mismatch')
    old=set()
    for old_version,old_group in history['review_history'].items():
        if old_version==version:continue
        for record in old_group['records']:
            row=current.get(record['frame_id'])
            if row and record.get('review_state')=='REVIEW_REJECT' and all(
                    record.get(k)==row.get(k) for k in ('image_sha256','dataset_generation_id')):
                old.add(row['frame_id'])
    return set(rejects),old-set(rejects)
