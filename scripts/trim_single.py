import csv
p = "results/single_qwen3-8b.csv"
rows = list(csv.DictReader(open(p, encoding="utf-8")))
keep = [r for r in rows if r["run"] in ("1", "2")]
w = csv.DictWriter(open(p, "w", newline="", encoding="utf-8"), fieldnames=list(rows[0].keys()))
w.writeheader(); w.writerows(keep); print(len(keep))
