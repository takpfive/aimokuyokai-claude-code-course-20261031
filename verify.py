"""配布された架空ケースの期待値を、生成スクリプトと独立に確認する。"""
from pathlib import Path
import csv, hashlib
from collections import Counter

ROOT = Path(__file__).resolve().parent
def rows(path):
    with (ROOT / path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

mapping = rows('output/01-folder/対応表.csv')
assert len(mapping) == 6
for row in mapping:
    assert sha(ROOT / row['元パス']) == sha(ROOT / row['新パス']) == row['SHA-256']
assert Counter(r['判定'] for r in mapping) == {'移動可':4,'重複':1,'要確認':1}
assert len(list((ROOT/'starter/01-folder/inbox').glob('*.txt'))) == 6
print('PASS 01: 原本6件・コピー6件の内容一致、重複1件・要確認1件')

app = rows('starter/02-app/requests.csv')
assert len(app) == 8
assert Counter(r['status'] for r in app) == {'未対応':5,'対応中':2,'完了':1}
assert [r['id'] for r in app if r['status'] != '完了' and r['due'] < '2026-10-29'] == ['R03']
print('PASS 02: 初期8件、状態5/2/1、期限超過R03（UI操作はdocs/verification.md参照）')

daily=(ROOT/'output/daily-report.md').read_text()
assert all(f'E{i:02}' in daily for i in range(1,10))
assert '未送信' in daily and '未確認' in daily
print('PASS 03: 日報に根拠ID E01〜E09。意味の妥当性は目視確認も実施')

inv=rows('output/04-match/invoice_judgments.csv')
assert len(inv)==7 and len({r['invoice_id'] for r in inv})==7
assert Counter(r['judgment'] for r in inv)=={'要確認':6,'一致':1}
by={r['invoice_id']:r for r in inv}
assert all('重複' in by[i]['reasons'] for i in ['I01','I05'])
assert by['I04']['judgment']=='一致'
assert int(by['I02']['invoice_qty'])-int(by['I02']['received_qty'])==20
assert (int(by['I03']['invoice_unit_yen'])-int(by['I03']['po_unit_yen']))*int(by['I03']['invoice_qty'])==10000
print('PASS 04: 7行中6行が要確認、重複両行、数量差20、金額差10000円')

deliveries=rows('starter/05-campaign/deliveries.csv')
clicks=rows('starter/05-campaign/clicks.csv')
regs=rows('starter/05-campaign/registrations.csv')
sends={r['send_id']:r for r in deliveries}
active={}
for r in regs:
    if r['status']=='active': active.setdefault(r['recipient_id'],r)
assert len(active)==6
unattributed=[r for r in active.values() if not r['last_click_send_id']]
assert len(unattributed)==2
summary={r['scope']:r for r in rows('output/05-campaign/summary.csv')}
for v,raw,human,direct in [('A',9,2,2),('B',4,3,2)]:
    population={r['recipient_id'] for r in deliveries if r['variant']==v and r['delivered']=='true'}
    events=[r for r in clicks if sends[r['send_id']]['variant']==v]
    humans={sends[r['send_id']]['recipient_id'] for r in events if r['classification']=='human'}
    registrations=[r for r in active.values() if r['last_click_send_id'] and sends[r['last_click_send_id']]['variant']==v]
    assert (len(population),len(events),len(humans),len(registrations))==(10,raw,human,direct)
    out=summary['variant '+v]
    assert tuple(int(out[k]) for k in ['delivered_unique','raw_clicks','human_unique_clickers','direct_registrations'])==(10,raw,human,direct)
print('PASS 05: A/Bクリック9/4、人間2/3、直接申込2/2、未帰属2')

for name in ['ops.md','cost.md','decision.md','evidence.md']:
    assert (ROOT/'output/06-team'/name).stat().st_size>0
assert '結論保留' in (ROOT/'output/06-team/decision.md').read_text()
print('PASS 06: 2担当・相互レビュー・統合記録あり。Teams専用機能は未実演')
print('ALL CHECKS PASSED')
