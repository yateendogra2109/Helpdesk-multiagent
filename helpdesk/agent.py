"""Multi-agent helpdesk: orchestrator -> policy / schedule / email agents.
`root_agent` is what `adk run helpdesk` / `adk web` picks up.
"""
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from . import config
from .tools import (
    count_courses,
    draft_email,
    get_instructor_email,
    get_slot_timings,
    log_unanswered,
    lookup_timetable,
    search_documents,
)

REFUSAL = "I don't know the answer to that based on the available academic documents."

RULES = f"""
Rules you must always follow:
- Answer ONLY from the output of your tools. Never use outside knowledge or guess.
- Cite the source of every fact in the form (Source: <file name>, page <n>) or (Source: <csv name>).
- If your tools return nothing relevant, reply exactly: "{REFUSAL}" and call log_unanswered
  with the student's question. Do not try to be helpful with a guess.
- If a document describes an "existing" or old policy and a "revised" policy that supersedes it,
  answer only from the revised policy and mention that it replaced the old one.
- When refusing, send only that exact sentence. Do not add suggestions or explanations.
/no_think
"""


def _model():
    return LiteLlm(model=config.CHAT_MODEL, timeout=config.LLM_TIMEOUT, num_retries=0)


policy_agent = Agent(
    name="policy_agent",
    model=_model(),
    description="Answers questions on academic rules, regulations, attendance, exams, grading, "
                "degree requirements, curriculum, credits, circulars and office orders.",
    instruction="You answer questions about academic rules, regulations and curriculum. "
                "Always call search_documents first." + RULES,
    tools=[search_documents, log_unanswered],
)

schedule_agent = Agent(
    name="schedule_agent",
    model=_model(),
    description="Answers questions about course slots, timetable, rooms, and how many courses "
                "a department has floated.",
    instruction="You answer timetable and course-offering questions. Use lookup_timetable for slots "
                "get_slot_timings for the days/times of a slot letter, and count_courses for counting "
                "questions." + RULES,
    tools=[lookup_timetable, get_slot_timings, count_courses, log_unanswered],
)

email_agent = Agent(
    name="email_agent",
    model=_model(),
    description="Finds a course instructor's email and drafts emails for sick leave or makeup exam requests.",
    instruction="You draft emails to course instructors. Call get_instructor_email with the course code or name, "
                "then draft_email using its output and the details the student gave. "
                "Show the full draft to the student and state it has NOT been sent. "
                "Never ask the student for more details: if the name, roll number or dates are unknown, "
                "write the draft with placeholders such as [Your Name]. "
                "If the course code is missing or unknown, refuse." + RULES,
    tools=[get_instructor_email, draft_email, log_unanswered],
)

root_agent = Agent(
    name="helpdesk_orchestrator",
    model=_model(),
    description="Academic helpdesk entry point.",
    instruction=(
        "You are the Academic Helpdesk orchestrator. Do not answer questions yourself; "
        "transfer to exactly one specialist:\n"
        "- policy_agent: rules, regulations, attendance, exams, degree requirements, curriculum, credits.\n"
        "- schedule_agent: course slots, timetable, number of courses floated.\n"
        "- email_agent: writing an email/leave/makeup request to a course instructor.\n"
        f"If the question is about anything else (campus life, dining, travel, general knowledge), "
        f"call log_unanswered with the question and reply exactly: \"{REFUSAL}\"\n/no_think"
    ),
    sub_agents=[policy_agent, schedule_agent, email_agent],
    tools=[log_unanswered],
)
