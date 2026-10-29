"""Run questions.csv through the agent and save answers, tool calls and auto-checks.

Usage:
  python evaluate.py --mode multi --runs 3
  python evaluate.py --mode single --runs 3
  HELPDESK_MODEL=ollama_chat/llama3.1:8b python evaluate.py --mode multi   # model comparison

Auto-checks are only a first pass; fill the manual columns (accuracy_manual, grounded_manual)
in the output CSV for the report.
"""
import argparse
import asyncio
import csv
import re
import uuid
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from helpdesk import config

REFUSAL_PAT = re.compile(r"don'?t know|do not know|cannot answer|can't answer|outside the scope", re.I)
THINK_PAT = re.compile(r"<think>.*?</think>", re.S)


def load_agent(mode):
    if mode == "single":
        from helpdesk.single_agent import single_agent
        return single_agent
    from helpdesk.agent import root_agent
    return root_agent


async def ask(runner, question):
    sid = uuid.uuid4().hex
    await runner.session_service.create_session(app_name="eval", user_id="u", session_id=sid)
    msg = types.Content(role="user", parts=[types.Part(text=question)])
    tools, answer = [], ""
    async for ev in runner.run_async(user_id="u", session_id=sid, new_message=msg):
        for call in ev.get_function_calls():
            tools.append(call.name)
        if ev.is_final_response() and ev.content and ev.content.parts:
            answer = "".join(p.text or "" for p in ev.content.parts if not getattr(p, "thought", False))
    return THINK_PAT.sub("", answer).strip(), tools


def autocheck(row, answer):
    """First-pass automatic scoring. Keywords: '|' separates required terms, '/' separates
    acceptable alternatives for one term. Sources use '/' for alternatives; file extensions are ignored."""
    low = answer.lower()
    refused = bool(REFUSAL_PAT.search(answer))
    should_refuse = row["should_refuse"].lower() == "true"
    kws = [k for k in row["expected_keywords"].split("|") if k]
    srcs = [Path(s).stem.lower() for s in row["expected_source"].split("/") if s]
    return {
        "refused": refused,
        "refusal_correct": refused == should_refuse,
        "keywords_ok": "" if should_refuse or not kws else
        all(any(alt.lower() in low for alt in k.split("/")) for k in kws),
        "cites_expected": "" if not srcs else any(s in low for s in srcs),
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["single", "multi"], default="multi")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--questions", default="questions.csv")
    args = ap.parse_args()

    runner = Runner(agent=load_agent(args.mode), app_name="eval", session_service=InMemorySessionService())
    questions = list(csv.DictReader(open(args.questions, encoding="utf-8")))
    model_tag = config.CHAT_MODEL.split("/")[-1].replace(":", "-")
    out = Path("results")
    out.mkdir(exist_ok=True)
    out_path = out / f"{args.mode}_{model_tag}.csv"

    fields = ["run", "id", "category", "question", "answer", "tools", "refused", "refusal_correct",
              "keywords_ok", "cites_expected", "accuracy_manual", "grounded_manual"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for run in range(1, args.runs + 1):
            for q in questions:
                try:
                    answer, tools = await ask(runner, q["question"])
                except Exception as e:  # a hung/failed model call must not kill the whole run
                    answer, tools = f"[ERROR] {type(e).__name__}: {str(e)[:200]}", []
                w.writerow({"run": run, "id": q["id"], "category": q["category"], "question": q["question"],
                            "answer": answer, "tools": ",".join(tools), **autocheck(q, answer),
                            "accuracy_manual": "", "grounded_manual": ""})
                f.flush()
                print(f"[run {run}] Q{q['id']} tools={tools}")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
