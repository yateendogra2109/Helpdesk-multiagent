"""Aggregate the CSVs in results/ into results/summary.md.

For every results/<mode>_<model>.csv it reports, per category and overall:
  accuracy      keyword check passed (answerable questions) / refusal correct (should-refuse questions)
  groundedness  expected source cited in the answer (answerable questions with a source)
  refusal       out-of-scope questions correctly refused, and answerable ones wrongly refused
  errors        model calls that failed (timeouts)
and the questions whose outcome or tool path changed between runs of the same configuration.

These are automatic first-pass scores; for the report, review the answers and fill the
accuracy_manual / grounded_manual columns in the result CSVs.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUESTIONS = {r["id"]: r for r in csv.DictReader(open(ROOT / "questions.csv", encoding="utf-8"))}


def truthy(v):
    return str(v).strip().lower() == "true"


def correct(row):
    q = QUESTIONS[row["id"]]
    if row["answer"].startswith("[ERROR]"):
        return False
    if q["should_refuse"].lower() == "true":
        return truthy(row["refused"])
    return truthy(row["keywords_ok"]) and not truthy(row["refused"])


def grounded(row):
    q = QUESTIONS[row["id"]]
    if q["should_refuse"].lower() == "true" or not q["expected_source"]:
        return None
    return truthy(row["cites_expected"])


def pct(n, d):
    return f"{100 * n / d:.0f}% ({n}/{d})" if d else "n/a"


def summarise(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    lines = []
    runs = sorted({r["run"] for r in rows}, key=int)
    by_cat = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
    lines.append(f"Runs: {len(runs)}; question-runs: {len(rows)}")
    lines.append("")
    lines.append("| Category | Accuracy | Groundedness (correct citation) | Wrongly refused / wrongly answered |")
    lines.append("|---|---|---|---|")
    for cat in [*sorted(by_cat), "ALL"]:
        rs = rows if cat == "ALL" else by_cat[cat]
        acc = sum(correct(r) for r in rs)
        g = [grounded(r) for r in rs if grounded(r) is not None]
        wrong_refuse = sum(1 for r in rs if QUESTIONS[r["id"]]["should_refuse"].lower() != "true" and truthy(r["refused"]))
        wrong_answer = sum(1 for r in rs if QUESTIONS[r["id"]]["should_refuse"].lower() == "true" and not truthy(r["refused"]))
        lines.append(f"| {cat} | {pct(acc, len(rs))} | {pct(sum(g), len(g))} | {wrong_refuse} refused / {wrong_answer} answered |")
    errors = sum(1 for r in rows if r["answer"].startswith("[ERROR]"))
    lines.append("")
    lines.append(f"Failed model calls (timeouts): {errors}")

    per_q = defaultdict(list)
    for r in rows:
        per_q[r["id"]].append(r)
    unstable = []
    for qid, rs in per_q.items():
        outcomes = {correct(r) for r in rs}
        paths = {r["tools"] for r in rs}
        answers = {r["answer"].strip() for r in rs}
        if len(rs) > 1 and (len(outcomes) > 1 or len(paths) > 1):
            unstable.append((qid, outcomes, paths, len(answers)))
    lines.append("")
    if len(runs) > 1:
        lines.append(f"Questions whose correctness or tool path changed across runs: {len(unstable)} of {len(per_q)}")
        lines.append("")
        lines.append("| Q | Question | Correct per run | Distinct tool paths |")
        lines.append("|---|---|---|---|")
        for qid, _, paths, _ in sorted(unstable, key=lambda x: int(x[0])):
            marks = " ".join("Y" if correct(r) else "N" for r in sorted(per_q[qid], key=lambda r: int(r["run"])))
            lines.append(f"| {qid} | {QUESTIONS[qid]['question'][:70]} | {marks} | {len(paths)} |")
        identical = sum(1 for rs in per_q.values() if len({r['answer'].strip() for r in rs}) == 1)
        lines.append("")
        lines.append(f"Questions with word-for-word identical answers in every run: {identical} of {len(per_q)}")

    lines.append("")
    lines.append("Questions answered incorrectly in at least one run:")
    lines.append("")
    for qid in sorted(per_q, key=int):
        bad = [r for r in per_q[qid] if not correct(r)]
        if bad:
            lines.append(f"- Q{qid} ({len(bad)}/{len(per_q[qid])} runs wrong): {QUESTIONS[qid]['question'][:80]}")
    return "\n".join(lines)


def main():
    files = sorted((ROOT / "results").glob("*.csv"))
    out = ["# Evaluation summary (automatic scores)", ""]
    for f in files:
        out += [f"## {f.stem}", "", summarise(f), ""]
    (ROOT / "results" / "summary.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
