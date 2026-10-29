"""Baseline: one agent holding every tool (used for the single- vs multi-agent comparison)."""
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from . import config
from .agent import REFUSAL, RULES
from .tools import (
    count_courses,
    draft_email,
    get_instructor_email,
    get_slot_timings,
    log_unanswered,
    lookup_timetable,
    search_documents,
)

single_agent = Agent(
    name="helpdesk_single",
    model=LiteLlm(model=config.CHAT_MODEL, timeout=config.LLM_TIMEOUT, num_retries=0),
    description="Single-agent academic helpdesk.",
    instruction=(
        "You are an academic helpdesk assistant. Tools: search_documents (rules, regulations, curriculum), "
        "lookup_timetable (slots), count_courses (how many courses), get_instructor_email + draft_email "
        "(email drafts, never sent), log_unanswered. Questions unrelated to academics at this institute "
        f"must be refused with: \"{REFUSAL}\"" + RULES
    ),
    tools=[search_documents, lookup_timetable, get_slot_timings, count_courses, get_instructor_email, draft_email, log_unanswered],
)
