"""Tools exposed to the ADK agents. Docstrings are what the LLM sees, so keep them precise."""
import csv
import datetime as dt

import chromadb
import pandas as pd
import requests

from . import config

_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        _collection = client.get_or_create_collection(
            config.COLLECTION, metadata={"hnsw:space": "cosine"}
        )
    return _collection


def _embed_query(text: str) -> list[float]:
    r = requests.post(
        f"{config.OLLAMA_BASE}/api/embed",
        json={"model": config.EMBED_MODEL, "input": [text]},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["embeddings"][0]


def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(config.CSV_DIR / name, dtype=str).fillna("")


def search_documents(query: str) -> dict:
    """Search the official academic documents (rules, regulations, curriculum, circulars,
    office orders) and return the most relevant passages with their source file and page.

    Args:
        query: A self-contained search query describing the information needed.

    Returns:
        A dict with status and a list of results (text, source, page). If status is
        "no_relevant_documents", the documents do not contain the answer.
    """
    col = _get_collection()
    if col.count() == 0:
        return {"status": "no_relevant_documents", "results": []}
    res = col.query(query_embeddings=[_embed_query(query)], n_results=config.TOP_K)
    results = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        if dist <= config.MAX_DISTANCE:
            results.append({
                "text": doc,
                "source": meta["source"],
                "page": meta["page"],
                "distance": round(dist, 3),
            })
    if not results:
        return {"status": "no_relevant_documents", "results": []}
    return {"status": "ok", "results": results}


def lookup_timetable(query: str) -> dict:
    """Look up the slot, days/time and room of a course in the timetable (data/csv/timetable.csv).

    Args:
        query: A course code (e.g. "CSL7570") or part of the course name (e.g. "Autonomous Systems").

    Returns:
        A dict with status and matching timetable rows. Cite source "timetable.csv".
    """
    df = _csv("timetable.csv")
    q = query.strip().lower()
    mask = (df["course_code"].str.lower() == q) | df["course_name"].str.lower().str.contains(q, regex=False)
    rows = df[mask].head(10).to_dict("records")
    if not rows:
        return {"status": "not_found", "results": []}
    return {"status": "ok", "source": "timetable.csv", "results": rows}


def get_slot_timings(slot: str) -> dict:
    """Get the days and clock times when a timetable slot letter (A-K, N, U, V) meets.

    Args:
        slot: The slot letter, e.g. "D".

    Returns:
        A dict with the weekly meeting times. Cite source "slot_system.csv"
        (Slot System for B.Tech. 2nd year onwards, AY 2026-27 Semester I).
    """
    df = _csv("slot_system.csv")
    rows = df[df["slot"].str.upper() == slot.strip().upper()]
    if rows.empty:
        return {"status": "not_found"}
    return {"status": "ok", "source": "slot_system.csv", "slot": slot.strip().upper(),
            "meetings": rows[["day", "time"]].to_dict("records")}


def count_courses(department: str = "", level: str = "", semester: str = "", course_type: str = "") -> dict:
    """Count (and list) the courses floated, filtered by department, level, semester and type.
    Use this for any "how many courses ..." question; never count by yourself.

    Args:
        department: Department/school name, e.g. "Humanities", "Economics", "Mechanical" (empty = any).
        level: Course level such as "400" (empty = any).
        semester: Semester label, e.g. "2026-I". All data is for the current semester, so leave empty.
        course_type: e.g. "Elective" or "Core" (empty = any).

    Returns:
        A dict with the count and the matching courses. Cite source "courses.csv".
    """
    df = _csv("courses.csv")
    if department:
        d = department.strip().lower()
        df = df[df["department"].str.lower().str.contains(d, regex=False)]
    if level:
        df = df[df["level"] == str(level).strip()]
    if semester:
        df = df[df["semester"].str.lower() == semester.strip().lower()]
    if course_type:
        df = df[df["type"].str.lower().str.contains(course_type.strip().lower(), regex=False)]
    return {
        "status": "ok",
        "source": "courses.csv",
        "count": len(df),
        "courses": df[["course_code", "course_name", "department", "level", "type", "slot"]]
        .head(40).to_dict("records"),
    }


def get_instructor_email(course: str) -> dict:
    """Find the instructor(s) of a course and their email id.

    Args:
        course: A course code (e.g. "CSL7650") or the course name (e.g. "Autonomous Systems").

    Returns:
        A dict with the instructor name(s) and email(s). Cite sources "courses.csv" and
        "instructors.csv". If status is "instructor_unknown", the course exists but its
        instructor is not in the data.
    """
    courses = _csv("courses.csv")
    q = course.strip().lower()
    rows = courses[(courses["course_code"].str.lower() == q) | (courses["course_name"].str.lower() == q)]
    if rows.empty:
        rows = courses[courses["course_name"].str.lower().str.contains(q, regex=False)]
    if rows.empty:
        return {"status": "not_found"}
    row = rows.iloc[0]
    inst = _csv("instructors.csv")
    ids = [i for i in row["instructor_id"].split(";") if i]
    people = inst[inst["instructor_id"].isin(ids)]
    if people.empty:
        return {"status": "instructor_unknown", "course_code": row["course_code"],
                "course_name": row["course_name"], "source": "courses.csv"}
    return {
        "status": "ok",
        "course_code": row["course_code"],
        "course_name": row["course_name"],
        "instructors": people[["name", "email"]].rename(columns={"name": "instructor_name",
                                                                   "email": "instructor_email"}).to_dict("records"),
        "source": "courses.csv, instructors.csv",
    }


def draft_email(
    instructor_name: str,
    instructor_email: str,
    course_code: str,
    request_type: str,
    details: str,
    student_name: str = "[Your Name]",
    roll_number: str = "[Your Roll Number]",
) -> dict:
    """Create an email DRAFT for the student to review. The email is NOT sent.

    Args:
        instructor_name: Name of the course instructor (from get_instructor_email).
        instructor_email: Email id of the instructor (from get_instructor_email).
        course_code: The course code.
        request_type: One of "sick_leave", "makeup_exam", "other".
        details: Specifics supplied by the student (dates, number of days, reason, exam name).
        student_name: Student's name if known.
        roll_number: Student's roll number if known.

    Returns:
        A dict with to, subject and body of the draft.
    """
    subjects = {
        "sick_leave": f"Request for sick leave - {course_code}",
        "makeup_exam": f"Request for makeup exam - {course_code}",
    }
    purposes = {
        "sick_leave": "I am writing to request leave from the course due to ill health.",
        "makeup_exam": "I am writing to request permission to appear for a makeup examination.",
    }
    subject = subjects.get(request_type, f"Request regarding {course_code}")
    purpose = purposes.get(request_type, "I am writing to make the following request.")
    body = (
        f"Dear {instructor_name},\n\n"
        f"{purpose} {details}\n\n"
        "I will provide supporting documents (e.g. a medical certificate) if required, and "
        "will catch up on the missed material. Kindly grant me permission.\n\n"
        f"Thank you for your consideration.\n\nRegards,\n{student_name}\n{roll_number}"
    )
    return {"status": "draft_created", "sent": False, "to": instructor_email, "subject": subject, "body": body}


def log_unanswered(question: str, reason: str = "") -> dict:
    """Record a question the helpdesk cannot answer so a human can follow up.
    Call this whenever you refuse to answer because no source supports an answer.

    Args:
        question: The student's original question.
        reason: Short note on why it could not be answered.

    Returns:
        A confirmation dict.
    """
    config.LOG_DIR.mkdir(exist_ok=True)
    new = not config.UNANSWERED_LOG.exists()
    with open(config.UNANSWERED_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "question", "reason"])
        w.writerow([dt.datetime.now().isoformat(timespec="seconds"), question, reason])
    return {"status": "logged"}
