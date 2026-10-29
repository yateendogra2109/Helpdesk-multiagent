# Academic Helpdesk Agent (Google ADK + Ollama + ChromaDB)

A multi-agent RAG helpdesk for IIT Jodhpur students. It answers questions about academic rules,
curriculum, course slots and the semester's courses, drafts (never sends) emails to course instructors,
cites the document each answer comes from, refuses questions it cannot ground in its data, and logs
every refused question to `logs/unanswered.csv` for a human to follow up.

## Architecture

```
helpdesk_orchestrator          routes the question, never answers by itself
 |- policy_agent    -> search_documents (ChromaDB RAG over data/docs)
 |- schedule_agent  -> lookup_timetable, get_slot_timings, count_courses (CSV lookups)
 `- email_agent     -> get_instructor_email, draft_email (draft only)
every agent          -> log_unanswered
```

`helpdesk/single_agent.py` is the single-agent baseline: one agent holding all the tools.
Models run through Ollama (`ollama_chat/qwen3:8b` by default) via ADK's LiteLLM connector;
embeddings are `nomic-embed-text`; the vector store is ChromaDB (cosine distance).

Design points worth knowing:
- Counting and lookups are tools over CSVs, not retrieval. The LLM never counts.
- `search_documents` drops chunks farther than `MAX_DISTANCE` (0.32, `helpdesk/config.py`), so out-of-scope
  questions get no context and the agent refuses. The value was chosen from measured distances:
  in-scope queries land at 0.24-0.30, out-of-scope at 0.34 and above.
- Markdown documents are chunked per section and every chunk carries the document title and section heading.
  This stops, for example, the superseded "Existing policy" paragraph of Circular 51 from sharing a chunk with the
  "Revised policy".
- Qwen3's thinking mode is turned off with `/no_think` (otherwise calls were slow and reasoning leaked into answers).

## Project layout

```
helpdesk/            agent.py (multi-agent, root_agent), single_agent.py, tools.py, config.py
ingest.py            chunk + embed data/docs into ChromaDB
evaluate.py          run questions.csv through an agent N times, with automatic first-pass checks
analyze.py           aggregate results/*.csv into results/summary.md
scripts/build_csvs.py  build courses.csv / timetable.csv from the department workbook
questions.csv        the 30 evaluation questions with expected answers, keywords and sources
data/docs/           documents indexed by RAG (see docs_manifest.csv)
data/csv/            courses, timetable, instructors, slot_system
data/pdfs, data/ss   raw inputs (workbook, curriculum PDFs, screenshots)
results/             evaluation outputs and summary.md
logs/unanswered.csv  questions the agent refused
REPORT.tex            findings (submission version); REPORT.md is an earlier draft
```

## Data

| File | Origin |
|---|---|
| `data/docs/*` | Public IIT Jodhpur documents: academic regulations, circulars, calendars, curricula; two scanned circulars and the slot chart were transcribed by hand. Listed in `docs_manifest.csv`. |
| `data/csv/instructors.csv` | 234 faculty names and emails copied from the public faculty directory pages. |
| `data/csv/courses.csv`, `timetable.csv` | Built by `scripts/build_csvs.py` from the department workbook `Finalized courses list .xlsx` (courses floated this semester) plus eight courses transcribed from `data/ss/current_courses.png` (the workbook has no CSE sheet). |
| `data/csv/slot_system.csv` | Slot letter to weekly meeting times, transcribed from the Slot System sheet (AY 2026-27 Semester I). |

Known data limits: only single-letter slots (A-K, N, U, V) can be resolved to clock times; other slot codes
(AZ, CA, T1, NG3, M-labs) are stored as given. Not every instructor in the workbook is in the faculty directory
(Physics, Mathematics, Electronics and some other faculty were not collected), so some courses have no instructor id.

## Setup (Windows + WSL, as used for this project)

Ollama runs on Windows; Python runs in WSL and reaches Ollama through mirrored networking.

1. Windows: install Ollama, then `ollama pull qwen3:8b` and `ollama pull nomic-embed-text`.
2. `%USERPROFILE%\.wslconfig`:
   ```
   [wsl2]
   networkingMode=mirrored
   memory=3GB
   swap=2GB
   ```
   then `wsl --shutdown`. The memory cap leaves RAM for the model (16 GB laptop); without it Ollama swapped and
   calls timed out.
3. In WSL:
   ```
   python3 -m venv ~/helpdesk-venv && source ~/helpdesk-venv/bin/activate
   pip install -r requirements.txt openpyxl
   cd /mnt/c/Users/<you>/Desktop/Autonomous_assgn_2
   python scripts/build_csvs.py     # only if the workbook changed
   python ingest.py --reset
   ```
   (On a plain Linux/macOS machine skip steps 2 and 3's WSL parts; set `OLLAMA_API_BASE` if Ollama is not on localhost.)

## Run

```
adk web                     # then pick "helpdesk"      (or: adk run helpdesk)
python evaluate.py --mode multi  --runs 3
python evaluate.py --mode single --runs 2
HELPDESK_MODEL=ollama_chat/<other-model> python evaluate.py --mode multi --runs 3   # swap the LLM (not run for the reported results)
python analyze.py           # writes results/summary.md
```

Environment variables: `HELPDESK_MODEL`, `HELPDESK_EMBED_MODEL`, `HELPDESK_MAX_DISTANCE`, `HELPDESK_LLM_TIMEOUT`.

## Evaluation method

`questions.csv` holds 30 questions: 13 policy, 6 schedule/count, 5 email, 6 out-of-scope. Each has an expected
answer, required keywords (`|` separates required terms, `/` separates alternatives), the expected source document and
whether the agent should refuse. `evaluate.py` scores automatically: accuracy (keywords present, or refusal for
should-refuse questions), groundedness (expected source cited) and refusal correctness. The automatic checks are a
first pass; the report states which answers were additionally reviewed by hand. Run-to-run changes are found by
comparing the same question across repeated runs (`analyze.py`).

## Results (Qwen3-8B)

Scores are automatic first-pass checks; the 25 answers marked wrong were then read by hand (details in the report).

| | Accuracy (after review) | Groundedness (excl. email) | Failed calls |
|---|---|---|---|
| Multi-agent, 3 runs | 86% (77/90) | 86% (49/57) | 0 |
| Single-agent, 2 runs | 87% (52/60) | 87% (33/38) | 2 |

- Out-of-scope questions (dining, transport, weather, hostel fee, code) were refused and logged in nearly every run; the one real leak was the cricket question in one multi-agent run.
- 16 of 30 questions changed correctness or tool path across the 3 multi-agent runs (10 of 30 across the 2 single-agent runs).
- Known weak spots: Q1 (the old attendance rule is retrieved before the revised one), Q10 (retrieval misses under the distance threshold) and Q11 (the model sometimes skips the search tool).

Raw answers are in `results/*.csv`, scores in `results/summary.md`, refused questions in `logs/unanswered.csv`.
