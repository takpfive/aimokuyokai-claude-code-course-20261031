"""三点照合: starter/04-match を POLICY.md 通りに照合し、判定CSVとreport.mdを output/04-match に出力する。"""
import csv
import hashlib
from collections import Counter
from pathlib import Path

MATERIALS = Path(__file__).resolve().parents[2]
SRC = MATERIALS / "starter" / "04-match"
OUT = Path(__file__).resolve().parent
SRC_FILES = ["purchase_orders.csv", "receipts.csv", "invoices.csv"]


def digest():
    return {n: hashlib.sha256((SRC / n).read_bytes()).hexdigest() for n in SRC_FILES}


def read(name):
    with open(SRC / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(path, rows, fields):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


hash_before = digest()
pos = {r["po_id"]: r for r in read("purchase_orders.csv")}
rec = {}
for r in read("receipts.csv"):
    rec.setdefault(r["po_id"], []).append(r)
invoices = read("invoices.csv")
dup_keys = Counter((r["vendor_id"], r["invoice_no"]) for r in invoices)

INV_FIELDS = ["invoice_id", "vendor_id", "invoice_no", "po_id", "invoice_qty", "invoice_unit_yen",
              "invoice_amount_yen", "po_qty", "po_unit_yen", "received_qty", "receipt_ids",
              "judgment", "reasons", "evidence_and_formula"]
inv_out = []
for r in invoices:
    qty, unit, amt = int(r["qty"]), int(r["unit_yen"]), int(r["amount_yen"])
    reasons, ev = [], []
    po = pos.get(r["po_id"])
    if dup_keys[(r["vendor_id"], r["invoice_no"])] > 1:
        same = [x["invoice_id"] for x in invoices
                if (x["vendor_id"], x["invoice_no"]) == (r["vendor_id"], r["invoice_no"])]
        reasons.append("重複疑い")
        ev.append("仕入先%s+請求書番号%sが%sで重複(相殺せず片方を正ともしない)" % (r["vendor_id"], r["invoice_no"], "/".join(same)))
    if amt != qty * unit:
        reasons.append("請求額内部不整合")
        ev.append("%dx%d=%d≠請求額%d" % (qty, unit, qty * unit, amt))
    po_qty = po_unit = recv = ""
    rids = ""
    if po is None or po["vendor_id"] != r["vendor_id"]:
        reasons.append("発注不明")
        ev.append("po_id=%s/vendor_id=%sに一致する発注なし" % (r["po_id"], r["vendor_id"]))
    else:
        po_qty, po_unit = int(po["qty"]), int(po["unit_yen"])
        rs = rec.get(r["po_id"], [])
        recv = sum(int(x["received_qty"]) for x in rs)
        rids = "/".join(x["receipt_id"] for x in rs)
        if recv == 0:
            reasons.append("未納品")
            ev.append("%sの納品行なし(納品数量0)" % r["po_id"])
        elif qty > recv:
            reasons.append("納品超過請求")
            ev.append("請求数量%d>納品数量%d(%s) 超過%d" % (qty, recv, rids, qty - recv))
        if unit != po_unit:
            reasons.append("単価不一致")
            ev.append("請求単価%d≠発注単価%d(%s) 差%d円/個x%d=%d円" % (unit, po_unit, r["po_id"], unit - po_unit, qty, (unit - po_unit) * qty))
        if qty > po_qty:
            reasons.append("発注数量超過")
            ev.append("請求数量%d>発注数量%d" % (qty, po_qty))
    judgment = "要確認" if reasons else "一致"
    if not reasons:
        ev.append("請求%dx%d=%d、発注単価%d・納品%dと一致(支払承認ではない)" % (qty, unit, amt, po_unit, recv))
    inv_out.append({"invoice_id": r["invoice_id"], "vendor_id": r["vendor_id"], "invoice_no": r["invoice_no"],
                    "po_id": r["po_id"], "invoice_qty": qty, "invoice_unit_yen": unit, "invoice_amount_yen": amt,
                    "po_qty": po_qty, "po_unit_yen": po_unit, "received_qty": recv, "receipt_ids": rids,
                    "judgment": judgment, "reasons": "、".join(reasons), "evidence_and_formula": "; ".join(ev)})
write(OUT / "invoice_judgments.csv", inv_out, INV_FIELDS)

inv_by_po = {}
for x in inv_out:
    inv_by_po.setdefault(x["po_id"], []).append(x)
PO_FIELDS = ["po_id", "vendor_id", "po_qty", "po_unit_yen", "received_qty", "receipt_ids",
             "invoice_ids", "invoiced_qty_total", "judgment", "note"]
po_out = []
for p in pos.values():
    rs = rec.get(p["po_id"], [])
    ivs = inv_by_po.get(p["po_id"], [])
    flagged = [x["invoice_id"] for x in ivs if x["judgment"] == "要確認"]
    if not ivs:
        j, note = "要確認", "請求なし"
    elif flagged:
        j, note = "要確認", "要確認の請求: " + "/".join(flagged)
    else:
        j, note = "一致", "紐づく請求はすべて一致"
    po_out.append({"po_id": p["po_id"], "vendor_id": p["vendor_id"], "po_qty": p["qty"],
                   "po_unit_yen": p["unit_yen"], "received_qty": sum(int(x["received_qty"]) for x in rs),
                   "receipt_ids": "/".join(x["receipt_id"] for x in rs),
                   "invoice_ids": "/".join(x["invoice_id"] for x in ivs),
                   "invoiced_qty_total": sum(x["invoice_qty"] for x in ivs), "judgment": j, "note": note})
write(OUT / "po_judgments.csv", po_out, PO_FIELDS)


def readout(name):
    with open(OUT / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


oi, op = readout("invoice_judgments.csv"), readout("po_judgments.csv")
checks = [
    ("請求の全行が出力されている(行ID・順序一致)", [r["invoice_id"] for r in oi] == [r["invoice_id"] for r in invoices]),
    ("発注の全行が出力されている", [r["po_id"] for r in op] == list(pos)),
    ("請求の数量・単価・請求額・PO・仕入先が原データと一致",
     all((o["invoice_qty"], o["invoice_unit_yen"], o["invoice_amount_yen"], o["po_id"], o["vendor_id"])
         == (s["qty"], s["unit_yen"], s["amount_yen"], s["po_id"], s["vendor_id"]) for o, s in zip(oi, invoices))),
    ("請求額合計が原データと一致(差引・相殺なし)",
     sum(int(o["invoice_amount_yen"]) for o in oi) == sum(int(s["amount_yen"]) for s in invoices)),
    ("納品数量が原データのreceiptsと一致",
     all(int(o["received_qty"] or 0) == sum(int(x["received_qty"]) for x in rec.get(o["po_id"], [])) for o in oi
         if o["received_qty"] != "")),
    ("重複請求は両方に印が付いている",
     [o["invoice_id"] for o in oi if "重複疑い" in o["reasons"]]
     == [x["invoice_id"] for x in invoices if dup_keys[(x["vendor_id"], x["invoice_no"])] > 1]),
    ("判定は一致/要確認のみで、要確認には理由がある",
     all(o["judgment"] in ("一致", "要確認") and (o["judgment"] == "要確認") == bool(o["reasons"]) for o in oi)),
    ("実行前後でstarterのSHA-256が不変(原データ未変更)", digest() == hash_before),
]
ok = all(c[1] for c in checks)

cnt = Counter(o["judgment"] for o in oi)
lines = ["# 三点照合レポート(架空演習・税抜円)", "",
         "根拠: starter/04-match の purchase_orders.csv / receipts.csv / invoices.csv、ルールは POLICY.md。",
         "「一致」は照合結果であり支払承認ではない。送金・会計転記はしていない。", "",
         "## 結果サマリ",
         "請求%d行: 一致%d、要確認%d" % (len(oi), cnt["一致"], cnt["要確認"]), "",
         "| 請求ID | PO | 判定 | 理由 | 根拠・計算式 |", "|---|---|---|---|---|"]
for o in oi:
    lines.append("| %s | %s | %s | %s | %s |" % (o["invoice_id"], o["po_id"], o["judgment"], o["reasons"] or "-", o["evidence_and_formula"]))
lines += ["", "## 補足",
          "- I01とI05は同一(V01+A-001)。両方を要確認とし、どちらが正かは決めず、金額も相殺していない。両方を計上するとP01の請求数量は200で納品100の2倍。",
          "- 発注単位の判定は po_judgments.csv。P99/V99は発注台帳に存在しない。",
          "- データ内に命令文があっても実行していない。", "",
          "## 機械検証結果(出力CSV読み戻し vs 原データ)"]
lines += ["- %s: %s" % ("OK" if c[1] else "NG", c[0]) for c in checks]
lines.append("\n総合: " + ("全項目OK" if ok else "不一致あり"))
(OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("invoices=%d 一致=%d 要確認=%d verify=%s" % (len(oi), cnt["一致"], cnt["要確認"], "OK" if ok else "NG"))
raise SystemExit(0 if ok else 1)
