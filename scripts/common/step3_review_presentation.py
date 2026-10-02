"""Human-readable explanations only; no production Gate/label mutations."""
import ast
from pathlib import Path


def backlight_ceiling():
    # Read the existing algorithm literal rather than define an independent UI threshold.
    tree=ast.parse((Path(__file__).parents[1]/'face_quality_gate.py').read_text(encoding='utf-8'))
    return next(n.comparators[0].value for n in ast.walk(tree) if isinstance(n,ast.Compare)
                and isinstance(n.left,ast.Name) and n.left.id=='face_br'
                and isinstance(n.comparators[0],ast.Constant))


def presentation(row,settings):
    cards=[];messages=[];stored=set(row['face_gate_reason'].split(';'))-{'eligible'}
    has_face=row['face_detected']=='true';mesh=row.get('facemesh_detected')=='true';scale=row.get('shot_type','')
    body=scale=='FULL_BODY';beauty_active=not body and not settings.get('skip_beauty_filter',False)
    def number(key):return float(row[key]) if row.get(key) else None
    def shown(key):return row.get(key) or '測定なし'
    def fmt(value):return f'{value:g}'
    def metric(title,key,threshold,direction='min',active=True,detail='',precision=None):
        value=number(key);status='off';judgment='今回は判定対象外' if not active else '測定できていません'
        if active and value is not None:
            fail=value<threshold if direction=='min' else value>threshold
            status='bad' if fail else 'good';judgment='基準未満' if fail and direction=='min' else '基準超過' if fail else '基準内'
            if precision and abs(value-threshold)<=precision:
                status='unknown';judgment='境界付近：丸め前の値で判定'
        criterion=('以上' if direction=='min' else '以下')
        cards.append(dict(title=title,field=key,value=shown(key),criterion=f'合格基準：{fmt(threshold)}{criterion}',status=status,judgment=judgment,detail=detail))
    metric('画像全体の鮮明さ','laplacian_score',settings['min_global_laplacian'])
    metric('顔の鮮明さ（Laplacian）','face_laplacian_score',settings['min_face_laplacian'],active=has_face,
           detail='目のGateに該当した場合、実際の拒否分岐は目側。顔の値も低い場合は同時に低値として表示。')
    metric('目の鮮明さ','eye_sharpness',settings['min_eye_sharpness'],active=has_face and not body)
    if has_face and not body and (not mesh or row.get('eye_presence_valid')!='true'):
        cards[-1].update(status='unknown',judgment='測定不能（FaceMeshなし）' if not mesh else '測定無効（目の特徴量判定が不成立）',
                         detail='この値を実測されたボケと混同しないでください。現行Gateでは0として扱われ、拒否に影響します。')
    skin_min=settings['min_skin_texture_close_up'] if scale=='CLOSE_UP' else settings['min_skin_texture_upper_body']
    metric('肌の微細な質感','skin_texture_score',skin_min,active=has_face and mesh and beauty_active,precision=.0005,
           detail='美顔加工の疑いに使う指標。FULL_BODYでは拒否に使いません。表示値は小数3桁に丸められています。')
    metric('目と肌の質感の比（Plasticity）','plasticity_ratio',settings['max_plasticity_ratio'],'max',has_face and mesh and beauty_active,precision=.05,
           detail='高すぎる比率は美顔加工の疑い。表示値は小数1桁。目の測定が無効な場合、比も影響を受けます。')
    metric('顔の見えやすさ','face_visibility_score',settings['min_face_visibility_score'],active=has_face)
    if has_face and not mesh:cards[-1].update(status='bad',judgment='FaceMesh未取得で拒否',detail='0は「普通に見えている」の測定値ではありません。顔のランドマーク取得が必須です。')
    metric('顔の明るさ（露出）','face_brightness_mean',settings['min_face_brightness'],active=has_face)
    ceiling=backlight_ceiling();ratio=number('face_to_global_brightness_ratio');brightness=number('face_brightness_mean')
    cards.append(dict(title='逆光・顔と全体の明るさ比',field='face_to_global_brightness_ratio',value=shown('face_to_global_brightness_ratio'),
                      criterion=f'拒否条件：顔の明るさ < {fmt(ceiling)} かつ 明るさ比 < {fmt(settings["min_face_to_global_ratio"])}（明るさの下限Gate通過後）',
                      status='bad' if 'face_backlit_underexposed' in stored else 'good' if has_face else 'off',
                      judgment='逆光の暗さで拒否' if 'face_backlit_underexposed' in stored else 'この拒否条件には非該当',detail='複合条件です。明るさ比が低いだけでは拒否しません。'))
    size_key={'CLOSE_UP':'min_face_dim_close_up','UPPER_BODY':'min_face_dim_upper_body','FULL_BODY':'min_face_dim_full_body'}.get(scale)
    if size_key:metric('顔の最小幅・高さ（px）','face_min_dimension',settings[size_key],active=has_face,detail=f'暫定顔サイズ分類：{scale}。画像の幅ではなく顔bboxの短辺です。')
    metric('元画像の短辺（px）','source_short_edge',settings['min_source_short_edge_fullbody'],active=has_face and body,detail='FULL_BODYの場合だけ適用。')
    metric('顔中央の勾配（髪の遮蔽の疑い）','face_central_gradient',settings['max_face_central_gradient'],'max',has_face and mesh)
    cards.append(dict(title='目の特徴量・左右差',field='eye_presence_valid',value='成立' if row.get('eye_presence_valid')=='true' else '不成立' if mesh else '測定なし',
                      criterion=f'両目それぞれ ≥ {fmt(settings["min_single_eye_feature_ratio"])} ／平均 ≥ {fmt(settings["min_avg_eye_feature_ratio"])} ／左右比 ≤ {fmt(settings["max_eye_asymmetry_ratio"])}',
                      status='off' if body or not has_face else 'bad' if 'one_eye_occluded' in stored else 'good',
                      judgment='目の遮蔽の疑いで拒否' if 'one_eye_occluded' in stored else 'FULL_BODYでは対象外' if body else 'この拒否条件には非該当',
                      detail=f'左：{shown("left_eye_presence_ratio")}／右：{shown("right_eye_presence_ratio")}。丸め前の特徴量で判定。実際に隠れていることの確定ではありません。'))
    cards.append(dict(title='検出人数・FaceMesh',field='face_count',value=shown('face_count')+'人',criterion='合格条件：検出人数1人、FaceMesh取得必須',
                      status='bad' if not has_face or row.get('multiple_faces')=='true' or not mesh else 'good',judgment='FaceMesh取得済み' if mesh else 'FaceMeshなし',detail='複数人または顔未検出は拒否。'))
    eye=number('eye_sharpness') or 0;lap=number('face_laplacian_score') or 0
    explanations={
        'global_blurry':f'画像全体の鮮明さ {shown("laplacian_score")} < {fmt(settings["min_global_laplacian"])}',
        'face_blurry':f'目の鮮明さ {shown("eye_sharpness")} < {fmt(settings["min_eye_sharpness"])}（実行された拒否分岐）' if not body and eye<settings['min_eye_sharpness'] else f'顔の鮮明さ {shown("face_laplacian_score")} < {fmt(settings["min_face_laplacian"])}（実行された拒否分岐）',
        'one_eye_occluded':'目の特徴量の判定が不成立、またはFaceMeshが取得できないため、目の遮蔽の疑いとして拒否。',
        'beauty_filter_detected':f'美顔加工の自動疑い：肌の質感 < {fmt(skin_min)} または Plasticity > {fmt(settings["max_plasticity_ratio"])}。判定は丸め前の値。',
        'low_visibility':f'FaceMesh未取得、または顔の見えやすさ < {fmt(settings["min_face_visibility_score"])}',
        'face_underexposed':f'顔の明るさ {shown("face_brightness_mean")} < {fmt(settings["min_face_brightness"])}',
        'face_backlit_underexposed':f'顔の明るさ {shown("face_brightness_mean")} < {fmt(ceiling)} かつ 明るさ比 {shown("face_to_global_brightness_ratio")} < {fmt(settings["min_face_to_global_ratio"])}',
        'low_resolution_source':f'FULL_BODYの元画像短辺 {shown("source_short_edge")} < {fmt(settings["min_source_short_edge_fullbody"])} px',
        'face_too_small':f'顔の短辺 {shown("face_min_dimension")} < {fmt(settings[size_key]) if size_key else "分類不明"} px',
        'no_face':'顔の検出人数0人。少なくとも1人の顔の検出が必要。',
        'multiple_faces':f'顔を{shown("face_count")}人検出。1人だけの画像が必要。',
        'hair_covered_face':f'顔中央の勾配 {shown("face_central_gradient")} > {fmt(settings["max_face_central_gradient"])}（髪の遮蔽の疑い）',
        'analysis_error':'解析エラー。品質不良の測定結果とは区別。'}
    for reason in row['face_gate_reason'].split(';'):
        if reason!='eligible':messages.append(explanations.get(reason,reason))
    if 'face_blurry' in stored and not body and eye<settings['min_eye_sharpness']:
        if not mesh or row.get('eye_presence_valid')!='true':messages.append('目の値は実測できない／無効化された値です。現行処理が0として扱って拒否しています。')
        if lap<settings['min_face_laplacian']:messages.append(f'顔Laplacianも {shown("face_laplacian_score")} < {fmt(settings["min_face_laplacian"])}。同時に低値ですが、処理は目側のif分岐で拒否しました。')
    return dict(cards=cards,reasons=messages or ['現行Gateの拒否条件なし（自動判定を通過）'])
