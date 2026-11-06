"""Attach model-listening receipts only to the exact reviewed asset hashes."""
import json
import hashlib
from pathlib import Path

def attach_content_reviews(records, project: Path):
    path=project/'reports/audio-content-review-20261024/final-review.json'
    if not path.exists():return records
    data=json.loads(path.read_text())
    rows={r['id']:r for r in data['resources']}
    for r in records:
        review=rows.get(r['id'])
        asset=project.parent/r['runtime_path']
        matches=asset.exists() and hashlib.sha256(asset.read_bytes()).hexdigest()==r['sha256']
        if review and matches and review['sha256']==r['sha256'] and review.get('model_review_completed'):
            r['audio_content_review']={k:review[k] for k in [
                'model_review_completed','review_type','model','receipt','conclusion','human_listening']}
            r['auditory_review']=True
            r['auditory_review_note']='Waveform-conditioned local audio model review completed; no human-listening claim. See audio_content_review and the linked receipt.'
        elif r.get('audio_content_review'):
            r.pop('audio_content_review',None)
            r['auditory_review']=False
            r['auditory_review_note']='Asset or receipt hash changed; model audio review must be repeated for the changed asset.'
    return records

def all_reviewed(records):
    return bool(records) and all(r.get('audio_content_review',{}).get('model_review_completed',False) for r in records)

def sync_runtime_review_metadata(records, path: Path):
    data=json.loads(path.read_text())
    entries=data.get('effects',data.get('tracks',{}))
    for record in records:
        entry=entries[record['id']]
        if entry.get('sha256')!=record['sha256']:
            raise ValueError('Runtime manifest hash mismatch: '+record['id'])
        entry['auditory_review']=record.get('auditory_review',False)
        entry['auditory_review_note']=record.get('auditory_review_note','')
        if record.get('audio_content_review'):
            entry['audio_content_review']=record['audio_content_review']
        else:entry.pop('audio_content_review',None)
    data['model_audio_review_completed']=all_reviewed(records)
    data['human_listening']=False
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def refresh_scene_review_status(project: Path):
    """Refresh presentation only; never re-encode or re-review unchanged audio."""
    report=project/'reports/audio-scene-review-20261024'
    final=project/'reports/audio-content-review-20261024/final-review.json'
    if not final.exists():return
    db={r['id']:r for r in json.loads(final.read_text())['resources']}
    data=json.loads((report/'review.json').read_text())
    for row in data['resources']:
        review=db.get(row['id'],{})
        fixture=project.parent/row['scene_fixture_path']
        digest=hashlib.sha256(fixture.read_bytes()).hexdigest()
        row['model_audio_review_completed']=bool(
            review.get('model_review_completed') and
            review.get('sha256')==data['asset_sha256_by_id'][row['id']] and
            review.get('scene_fixture_sha256')==row['scene_fixture_sha256']==digest)
        if row['model_audio_review_completed']:
            row['model_review_receipt']=review['scene_receipt']
    complete=all(r['model_audio_review_completed'] for r in data['resources'])
    data.update(model_audio_review_completed=complete,human_listening=False,
                signal_analyzer_has_audio_understanding=False,
                audio_input_supported=True,
                scope='Signal/timing analysis plus separately linked waveform-conditioned local model review; no human or iPhone listening claim.')
    (report/'review.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    if complete:
        p=report/'index.html';s=p.read_text()
        s=s.replace('当前模型不支持音频输入，未完成真正听觉验收。这里提供逐项信号／时序结果和可播放的场景样例，供听觉复核。',
                    '已完成 69 项本地模型音频输入审查。模型结论与信号指标分开记录，不声称人耳验收。')
        s=s.replace('逐首听审：未完成','本地模型音频审查：已完成').replace('逐条听审：未完成','本地模型音频审查：已完成')
        s=s.replace('<a href="tracks.md">69 条逐项检查表</a>',
                    '<a href="../audio-content-review-20261024/tracks.md">69 条模型审查与修改依据</a> · <a href="tracks.md">信号指标表</a>')
        p.write_text(s)
        p=report/'tracks.md';s=p.read_text().replace('本表为信号与时序检查，未完成真正听审。',
            '本表保留信号与时序指标；69 项本地模型音频审查已完成，详见 [修改依据](../audio-content-review-20261024/tracks.md)。')
        p.write_text(s.replace('| 待听审 |','| 模型已审 |'))
