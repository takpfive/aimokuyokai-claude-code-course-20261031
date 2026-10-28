"""メール施策集計: starter/05-campaign を DEFINITIONS.md 通りに集計し、判定CSVとreport.mdを output/05-campaign に出力する。"""
import csv
import hashlib
from collections import defaultdict
from pathlib import Path

MATERIALS = Path(__file__).resolve().parents[2]
SRC = MATERIALS / "starter" / "05-campaign"
OUT = Path(__file__).resolve().parent
SRC_FILES = ["deliveries.csv", "clicks.csv", "registrations.csv"]
VARIANTS = ["A", "B"]


def digest():
    return {n: hashlib.sha256((SRC / n).read_bytes()).hexdigest() for n in SRC_FILES}


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(name, rows, fields):
    with open(OUT / name, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def pct(n, d):
    return "%d/%d=%.1f%%" % (n, d, 100 * n / d) if d else "分母0"


hash_before = digest()
deliveries = read(SRC / "deliveries.csv")
clicks = read(SRC / "clicks.csv")
regs = read(SRC / "registrations.csv")

# 配信母数: delivered=true のユニークrecipient_id
delivered = {}
for d in deliveries:
    if d["delivered"].strip().lower() == "true" and d["recipient_id"] not in delivered:
        delivered[d["recipient_id"]] = d
send_info = {d["send_id"]: d for d in deliveries}
variant_of = {rid: d["variant"] for rid, d in delivered.items()}

# クリック判定
click_out = []
human_by_recipient = defaultdict(list)
for c in clicks:
    s = send_info.get(c["send_id"])
    if s is None:
        note = "send_idが配信データになく集計対象外"
        rid = var = ""
    elif s["recipient_id"] not in delivered:
        rid, var, note = s["recipient_id"], s["variant"], "未配信のため集計対象外"
    else:
        rid, var = s["recipient_id"], s["variant"]
        if c["classification"] == "human":
            note = "human: 件数に加算、ユニーク人数に算入"
            human_by_recipient[rid].append(c["click_id"])
        elif c["classification"] == "unknown":
            note = "unknown: humanとみなさない(総クリック件数のみ)"
        else:
            note = "%s: humanではない(総クリック件数のみ)" % c["classification"]
    click_out.append({"click_id": c["click_id"], "send_id": c["send_id"], "recipient_id": rid, "variant": var,
                      "classification": c["classification"], "in_raw_click_count": "yes" if s else "no",
                      "counts_as_human_unique": "yes" if (c["classification"] == "human" and rid in human_by_recipient
                                                          and c["click_id"] == human_by_recipient[rid][0]) else "no",
                      "judgment": note})
write("click_judgments.csv", click_out, ["click_id", "send_id", "recipient_id", "variant", "classification",
                                         "in_raw_click_count", "counts_as_human_unique", "judgment"])

# 申込: active のみ、recipient_idで重複排除(先頭行を採用、後続は重複として除外)
reg_out, seen, valid = [], {}, []
for r in regs:
    rid = r["recipient_id"]
    if r["status"] != "active":
        j, attr, var = "除外: status=%s" % r["status"], "", ""
    elif rid in seen:
        j, attr, var = "除外: %sと同一recipient_idの重複" % seen[rid], "", ""
    else:
        seen[rid] = r["registration_id"]
        valid.append(r)
        sid = r["last_click_send_id"].strip()
        s = send_info.get(sid)
        if not sid:
            j, attr, var = "有効申込・未帰属(last_click_send_id空欄)", "unattributed", ""
        elif s is None or s["recipient_id"] != rid:
            j, attr, var = "有効申込・未帰属(last_click_send_idが本人の配信と不整合)", "unattributed", ""
        else:
            j, attr, var = "有効申込・直接帰属(%s)" % sid, "direct", s["variant"]
    reg_out.append({"registration_id": r["registration_id"], "recipient_id": rid, "status": r["status"],
                    "last_click_send_id": r["last_click_send_id"], "in_delivered_population": "yes" if rid in delivered else "no",
                    "attribution": attr, "attributed_variant": var, "judgment": j})
write("registration_judgments.csv", reg_out, ["registration_id", "recipient_id", "status", "last_click_send_id",
                                              "in_delivered_population", "attribution", "attributed_variant", "judgment"])

# 配信行ごと
send_out = []
for d in deliveries:
    cl = [c for c in clicks if c["send_id"] == d["send_id"]]
    send_out.append({"send_id": d["send_id"], "recipient_id": d["recipient_id"], "variant": d["variant"],
                     "delivered": d["delivered"],
                     "in_population": "yes" if delivered.get(d["recipient_id"]) is d else "no",
                     "raw_clicks": len(cl), "human_clicks": sum(c["classification"] == "human" for c in cl),
                     "click_ids": "/".join(c["click_id"] for c in cl),
                     "direct_registration_ids": "/".join(x["registration_id"] for x in reg_out
                                                         if x["attribution"] == "direct" and x["last_click_send_id"] == d["send_id"])})
write("send_judgments.csv", send_out, ["send_id", "recipient_id", "variant", "delivered", "in_population", "raw_clicks",
                                       "human_clicks", "click_ids", "direct_registration_ids"])

# 集計
def clicks_in(var):
    return [c for c in click_out if c["in_raw_click_count"] == "yes" and c["recipient_id"] in delivered
            and (var is None or c["variant"] == var)]


summary, ids = [], {}
for var in [None] + VARIANTS:
    label = "全体" if var is None else "variant " + var
    pop = [r for r, d in delivered.items() if var is None or d["variant"] == var]
    cs = clicks_in(var)
    hum = [c for c in cs if c["classification"] == "human"]
    hu = sorted({c["recipient_id"] for c in hum})
    direct = [x for x in reg_out if x["attribution"] == "direct" and (var is None or x["attributed_variant"] == var)]
    unattr = [x for x in reg_out if x["attribution"] == "unattributed"] if var is None else []
    ids[label] = {"pop": pop, "cs": cs, "hum": hum, "hu": hu, "direct": direct, "unattr": unattr}
    summary.append({"scope": label, "delivered_unique": len(pop), "raw_clicks": len(cs), "human_clicks": len(hum),
                    "human_unique_clickers": len(hu), "human_unique_click_rate": pct(len(hu), len(pop)),
                    "direct_registrations": len(direct), "direct_cvr": pct(len(direct), len(pop)),
                    "unattributed_registrations": len(unattr) if var is None else "variant別には配分しない"})
write("summary.csv", summary, list(summary[0].keys()))

# 機械検証
checks = []
checks.append(("配信の全行(%d)が出力されている" % len(deliveries), [r["send_id"] for r in send_out] == [d["send_id"] for d in deliveries]))
checks.append(("クリックの全行(%d)が出力されている" % len(clicks), [r["click_id"] for r in click_out] == [c["click_id"] for c in clicks]))
checks.append(("申込の全行(%d)が出力されている" % len(regs), [r["registration_id"] for r in reg_out] == [r["registration_id"] for r in regs]))
checks.append(("クリックのclassificationが原データと一致", all(o["classification"] == s["classification"] for o, s in zip(click_out, clicks))))
checks.append(("申込のstatus・last_click_send_idが原データと一致",
               all((o["status"], o["last_click_send_id"]) == (s["status"], s["last_click_send_id"]) for o, s in zip(reg_out, regs))))
checks.append(("配信行のvariant・recipient_idが原データと一致",
               all((o["variant"], o["recipient_id"]) == (s["variant"], s["recipient_id"]) for o, s in zip(send_out, deliveries))))
sm = {r["scope"]: r for r in read(OUT / "summary.csv")}
checks.append(("summaryのvariant別の合計が全体と一致(配信・クリック・human・直接帰属)",
               all(int(sm["全体"][k]) == int(sm["variant A"][k]) + int(sm["variant B"][k])
                   for k in ["delivered_unique", "raw_clicks", "human_clicks", "human_unique_clickers", "direct_registrations"])))
checks.append(("summary.csvの件数が原データからの独立再計算と一致",
               int(sm["全体"]["raw_clicks"]) == sum(1 for c in clicks if send_info[c["send_id"]]["recipient_id"] in delivered)
               and int(sm["全体"]["human_clicks"]) == sum(c["classification"] == "human" for c in clicks)
               and int(sm["全体"]["delivered_unique"]) == len({d["recipient_id"] for d in deliveries if d["delivered"] == "true"})))
checks.append(("申込の行数 = 有効 + 除外(取りこぼしなし)",
               len(reg_out) == len(valid) + sum(x["judgment"].startswith("除外") for x in reg_out)))
checks.append(("有効申込 = 直接帰属 + 未帰属", len(valid) == sum(x["attribution"] in ("direct", "unattributed") for x in reg_out)
               and len(valid) == int(sm["全体"]["direct_registrations"]) + int(sm["全体"]["unattributed_registrations"])))
checks.append(("実行前後でstarterのSHA-256が不変(原データ未変更)", digest() == hash_before))
ok = all(c[1] for c in checks)

g = ids["全体"]
L = ["# メール施策 集計レポート(架空演習)", "",
     "根拠: starter/05-campaign の deliveries.csv / clicks.csv / registrations.csv、定義は DEFINITIONS.md。", "",
     "## 集計結果(分母=delivered=trueのユニークrecipient_id)",
     "| 区分 | 配信母数 | クリック件数 | human件数 | ユニーク人間クリック | 直接帰属申込 | 直接帰属CVR |",
     "|---|---|---|---|---|---|---|"]
for r in summary:
    L.append("| %s | %s | %s | %s | %s (%s) | %s | %s |" % (r["scope"], r["delivered_unique"], r["raw_clicks"], r["human_clicks"],
             r["human_unique_clickers"], r["human_unique_click_rate"], r["direct_registrations"], r["direct_cvr"]))
L += ["", "## 根拠ID・計算式",
      "- 配信母数: S01〜S20(全てdelivered=true、recipient U01〜U20は重複なし)=20。A=S01〜S10、B=S11〜S20、各10。",
      "- クリック件数(全分類): C01〜C13=13。内訳 human 6(" + "/".join(c["click_id"] for c in g["hum"]) + ")、security 6(C04〜C09)、unknown 1(C13)。",
      "- 単純クリック件数とユニーク人間クリックは別物: A はhuman 3件(C01,C02,C03)だがU02が2回押下のためユニーク2人(U01,U02)。Bはhuman 3件・ユニーク3人(U11,U12,U13)。",
      "- ユニーク人間クリック 5/20=25.0%(A 2/10=20.0%、B 3/10=30.0%)。C13(unknown)はhumanとみなさず除外。security(C04〜C09)もhumanではないため含めない。",
      "- 申込: 全8行(J01〜J08)。J05(cancelled)とJ08(U01の重複、J01を採用)を除外 → 有効6人(J01,J02,J03,J04,J06,J07)。",
      "- 直接帰属: J01(S01→A)、J02(S02→A)、J03(S11→B)、J04(S12→B)=4。A 2/10=20.0%、B 2/10=20.0%、全体 4/20=20.0%。",
      "- 未帰属: J06(U14、last_click_send_id空欄。U14はS14でB配信済みだが勝手にBへ帰属させない)、J07(U99、空欄・配信データにも不在)=2。variant別には配分しない。",
      "- CVRの分母は配信母数(クリック者ではない)。除外は申込J05・J08のみで、配信・クリックの除外はなし。", "",
      "## 解釈の限界(勝者は断定しない)",
      "- 標本は各群10人と小さく、無作為割付の証拠もない。クリックはBが多く、直接帰属申込は同数(2対2)で、指標により向きが異なる。",
      "- 因果効果や統計的な勝者は断定できない。未帰属2件の扱い次第で結果が変わりうる(J06はB配信済み)。", "",
      "## 機械検証結果(出力CSV読み戻し vs 原データ)"]
L += ["- %s: %s" % ("OK" if c[1] else "NG", c[0]) for c in checks]
L.append("\n総合: " + ("全項目OK" if ok else "不一致あり"))
(OUT / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("delivered=%d human_unique=%d direct=%d verify=%s" % (len(g["pop"]), len(g["hu"]), len(g["direct"]), "OK" if ok else "NG"))
raise SystemExit(0 if ok else 1)
