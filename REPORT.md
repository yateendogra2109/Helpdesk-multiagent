# Academic Helpdesk Agent: Report

**Name:** Yateen  **Roll No.:** B23CS1082  **Course assignment:** Multi-agent Academic Helpdesk (Google ADK, Ollama, ChromaDB)

## 1. System

The helpdesk answers questions about IIT Jodhpur academic rules, curricula, the semester's courses and slots, drafts (never sends) emails to instructors, cites its source, and refuses and logs anything it cannot ground.

```
helpdesk_orchestrator            routes only, never answers itself
 |- policy_agent    -> search_documents   (ChromaDB RAG over 15 documents)
 |- schedule_agent  -> lookup_timetable, get_slot_timings, count_courses  (CSV tools)
 `- email_agent     -> get_instructor_email, draft_email  (draft only, sent=False)
all agents           -> log_unanswered  (logs/unanswered.csv, for a human)
```

- **Single-agent baseline** (`helpdesk/single_agent.py`): one agent holding all seven tools and the same rules.
- **Stack:** Google ADK 2.13, LiteLLM to Ollama (`qwen3:8b`), `nomic-embed-text` embeddings, ChromaDB (cosine). Python runs in WSL; Ollama runs on Windows (mirrored networking). The WSL VM is capped at 3 GB so the 8B model fits a 16 GB laptop.
- **Design choices:**
  1. Counting and lookups are tools over CSVs, so the LLM never counts. "How many courses did Economics float" calls `count_courses`.
  2. `search_documents` drops chunks farther than a cosine distance of 0.32. I measured in-scope queries at 0.24–0.30 and out-of-scope at 0.34 and above, so out-of-scope questions get no context and the agent refuses.
  3. Markdown documents are chunked per section with the title and heading on each chunk.
  4. The prompt forces one exact refusal sentence and a `log_unanswered` call.
  5. Qwen3's thinking mode is switched off with `/no_think`; otherwise calls were slow and reasoning leaked into answers.

## 2. Data

All files are listed with their source URL in `docs_manifest.csv`.

| Data | Content |
|---|---|
| 15 documents in `data/docs` (629 chunks) | Academic Regulations (2019 onwards), PG Regulations (2022), MS-by-Research Regulations, Joint Programmes in Medical Technologies, the continuation/graduation amendment, 4 academic calendars (AY 2024-25 to 2026-27 and Summer 2026), two curricula (BS Physics, B.Tech Systems Science), Circular 51 (attendance) and Circular 52 (exams), the slot system note, and a transcription of the section 11.3 credit-requirements table |
| `courses.csv` / `timetable.csv` | 614 courses floated in 2026-I across 19 departments, from the department workbook plus 8 courses transcribed from a screenshot. 584 have a slot, 411 an instructor link |
| `instructors.csv` | 234 faculty names and emails from the public faculty pages |
| `slot_system.csv` | Slot letter to weekly meeting times, transcribed from the slot chart |

Circulars 51 and 52 were scanned images with no extractable text. I rendered them and transcribed them by hand; the originals are kept in `data/scanned_originals/`. A company brochure was left out as irrelevant. Personal data is limited to public faculty emails.

**Limits.** There are 15 documents plus 4 tables, short of the suggested 20–30. The workbook has no CSE sheet, so CSL7650 (Autonomous Systems) has a slot but no instructor. Only letter slots (A–K, N, U, V) have clock times. The faculty list lacks Physics, Mathematics and Electronics. The assignment's example "CSL7570" does not exist; the real code is CSL7650.

## 3. Evaluation method

`questions.csv` has 30 questions: 13 policy, 6 schedule/count, 5 email, 6 out-of-scope (one email question, Q24, must be refused because the instructor is unknown). Each has an expected answer, keywords, expected source and a should-refuse flag. Ground truth was checked against the files and tools beforehand. `evaluate.py` runs each question in a fresh session and records the answer and the tools called. Three metrics are scored:

- **Accuracy:** keywords present, or a refusal for should-refuse questions.
- **Groundedness:** the expected source is cited.
- **Refusal correctness:** answered questions are not refused, and out-of-scope ones are refused.

Scores are automatic first-pass checks. I then read every answer the checks marked wrong (25 of 150), and adjusted only where the check was clearly mistaken (section 4). I did not read the answers the checks marked correct one by one. Multi-agent was run 3 times and single-agent 2 times (30 questions each; single-agent was cut from 3 runs to 2 for time). Model: Qwen3-8B at default temperature.

## 4. Results (Qwen3-8B)

| | Auto accuracy | Accuracy after review | Groundedness (all) | Groundedness (excl. email) | Failed calls |
|---|---|---|---|---|---|
| Multi-agent, 90 question-runs | 82% (74/90) | **86% (77/90)** | 74% (51/69) | 86% (49/57) | 0 |
| Single-agent, 60 question-runs | 85% (51/60) | **87% (52/60)** | 78% (36/46) | 87% (33/38) | 2 |

Review adjustments: refusals that say "I have no information" but not in the exact sentence (Q26 in all 5 runs, Q29 in multi run 1) were scored wrong by the keyword pattern; I counted them correct. The email groundedness check looks for the text "courses" in a drafted email, which a draft never contains, so I also give groundedness without the email questions. The 2 single-agent failed calls were one timeout (280 s) and one dropped connection to Ollama.

By category, automatic scores (multi / single): schedule 94% / 83%, email 87% / 100%, policy 77% / 77%, out-of-scope 78% / 92% (before the review adjustment above; after it, out-of-scope is 17/18 for multi-agent).

**Correct refusals.** Dining, campus transport, weather, hostel fee and "Python function" were refused and logged in nearly every run. Q24 (email for CSL7650, instructor unknown) was refused in all runs of both modes. The one real leak: multi run 3 answered the cricket question (wrongly, "Australia 2022") after logging it. The agent drafted correct emails to the right addresses for ENL7010, ENL4050 and LAL4050; every draft shows `sent=False`.

**Single vs multi.** The two are close: single-agent is 1 point higher after review (87% vs 86%) on 60 vs 90 question-runs, which is within the run-to-run noise measured below. Single-agent was better on email and on leaking fewer out-of-scope answers. Multi-agent was better on schedule questions (94% vs 83%), had no failed calls, and its sub-agents have narrower prompts and tool sets. The multi-agent hop adds a failure mode of its own: in several runs the orchestrator transferred to a sub-agent, and the sub-agent then refused or called `log_unanswered` without searching (Q11, Q8, Q20 in some runs). The runs also happened under different memory pressure, so I do not read the gap as an effect of the architecture. At this size Qwen3-8B handles one agent with seven tools about as well as three specialists.

## 5. Answers that change between runs

At default temperature the same question gives different results. 16 of 30 questions changed correctness or tool path across the 3 multi-agent runs, 10 of 30 across the 2 single-agent runs. Only 3 of 30 multi-agent and 7 of 30 single-agent questions gave word-for-word identical answers in every run.

- **Unstable policy questions:** Q1, Q6, Q7, Q8, Q10, Q11, Q13. Typically the first run was right and a later one refused or answered from the wrong clause (e.g. Q7 returned an empty answer in multi run 3).
- **Unstable schedule and email:** Q19 (HSL4010 slot: right in 2 of 3 multi runs and 1 of 2 single runs), Q15, Q20, Q23. A wrong run is usually a refusal even though the data exists. Q23 once claimed "the course code is either invalid or no instructor information exists" for HSL4010, whose instructor is in the data.
- **Unstable refusals:** Q26, Q27, Q29. Whether the model answers or refuses depends on the run.
- **Stable:** counts (Q17 and Q18), slot letters (Q14, Q16), the 10 open-elective credits (Q2) and the grounded email drafts.

Tool paths vary even when answers agree (for example Q15 used different tool sequences across runs), so checking the final text alone would hide real variation.

## 6. Failure analysis

The failures have different causes, and I did not tune the system after the runs, so these stand as findings.

1. **Q1 (attendance for the Major exam): retrieval ranking plus the model. The section-chunking fix did not fully work.** Circular 51 keeps the old and the revised rule in separate chunks, but "Existing policy" ranks first (distance 0.269) and "Revised policy" third (0.284). The model then blends them and states the 75% rule. It was wrong in 2 of 3 multi runs and 2 of 2 single runs, and refused once without searching. A fix would be to drop or down-rank superseded chunks.
2. **Q10 (extra credits from the sixth semester): retrieval miss.** The model's query returned nothing under the 0.32 threshold, so the agent refused. Runs that phrased the query differently found page 17 and answered correctly. A fixed threshold trades wrong refusals against leaked out-of-scope answers.
3. **Q11 (B grade points): model skipped retrieval.** The right chunk (page 8, distance 0.297) is retrieved when the model searches. In multi runs 2 and 3 it called `log_unanswered` directly instead.
4. **Q26 and Q29 (out-of-scope): mostly a scoring artefact.** The agent refused and logged, but paraphrased the refusal. The exact-sentence instruction is followed only some of the time.
5. **Wrong refusal when data exists (Q13, Q19, Q23).** The tool returned the data, but the model or sub-agent refused. This is the main weakness of an 8B model with tool use.
6. **Operational faults.** Multi run 2, Q6 repeated its refusal six times with stray `</think>` text, even with `/no_think`. Early evaluation hit timeouts of up to 570 s because Windows RAM was exhausted. Capping WSL at 3 GB and closing Docker removed them.

Other numeric answers were right and cited: 10 days to apply for a make-up exam, a 3-hour Major, 40% minimum weight, 14 semesters maximum.

## 7. Limitations

- **Model replacement not done.** The assignment asks for a second LLM. I could not run one: free disk was about 3.3 GB, too little for `qwen3:4b` (about 2.5 GB) with margin, and Llama 3.1 8B (4.9 GB) does not fit. The code supports it (`HELPDESK_MODEL=ollama_chat/qwen3:4b python evaluate.py`), but no results exist, so I make no claim about how a smaller or different model compares.
- Fewer documents than suggested (15, not 20–30). Calendars extract as jumbled table text and are hard for RAG.
- Partial instructor data; no CSE sheet; many slot codes (AZ, CA, T1, NG3, labs) have no clock times; Level is blank for courses without a code.
- Evaluation is small (30 questions, 2–3 runs). Scoring is mostly automatic; I reviewed only the answers it marked wrong (section 3), and I did not blind-score correct ones. Humanities is treated as the School of Liberal Arts, and Q18 asks for 400-level courses because the workbook has no elective flag.
- The multi-agent and single-agent runs were not under identical machine load.

## 8. Reproduce

`README.md` has the setup. In short: `ollama pull qwen3:8b nomic-embed-text`; in WSL `pip install -r requirements.txt`, `python ingest.py --reset`, then `adk web`, `python evaluate.py --mode multi --runs 3`, `python evaluate.py --mode single --runs 2`, `python analyze.py`. Raw answers are in `results/*.csv`, the scores in `results/summary.md`, and refused questions in `logs/unanswered.csv`.
