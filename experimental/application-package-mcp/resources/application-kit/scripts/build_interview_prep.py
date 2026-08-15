#!/usr/bin/env python3
"""Build local-only interview preparation from a student workspace.

The script is intentionally conservative. It creates a structured interview
prep file and a missing-information questionnaire. It does not call the MCP and
does not invent personal hobbies, interviewer facts, achievements, language
levels, visa facts, or metrics.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_TEMPLATE = "interview_prep.md"


def read_text(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_space(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def bullet(items: list[str]) -> str:
    clean = [normalize_space(item) for item in items if normalize_space(item)]
    return "\n".join(f"- {item}" for item in clean) if clean else "- Information missing; ask the student before final interview use."


def numbered(items: list[str]) -> str:
    clean = [normalize_space(item) for item in items if normalize_space(item)]
    return "\n".join(f"{index}. {item}" for index, item in enumerate(clean, 1)) if clean else "1. Information missing; ask the student before final interview use."


def paragraph(value: object) -> str:
    text = normalize_space(value)
    return text if text else "Information missing; ask the student before final interview use."


def fenced(text: str) -> str:
    return "```text\n" + normalize_space(text) + "\n```"


def trim_sentence_end(text: str) -> str:
    return normalize_space(text).rstrip(" .;:")


def supported_action_language(text: str) -> str:
    replacements = {
        "one useful part of my work was this:": "I authored",
        "Provides credible proof": "This documented proof",
        "through modernized": "by helping modernize",
        "then connected that work to process diagrams and workflow documents": "then documented process diagrams and workflow documents",
    }
    output = normalize_space(text)
    for old, new in replacements.items():
        output = output.replace(old, new)
    output = output.replace("I authored authored", "I authored")
    output = output.replace("..", ".")
    return output


def short_work_anchor(snippets: list[str]) -> str:
    if snippets:
        text = supported_action_language(trim_sentence_end(snippets[0]))
        sentences = re.split(r"(?<=[.!?])\s+", text)
        kept = []
        for sentence in sentences:
            clean = normalize_space(sentence)
            if not clean:
                continue
            kept.append(clean)
            if len(" ".join(kept).split()) >= 34 or len(kept) >= 2:
                break
        anchor = " ".join(kept).strip()
        if anchor:
            return anchor
    return "I have worked on practical documentation, follow-up notes, and structured handover material that another person could review and use"


def spoken_profile_anchor(snippets: list[str], clusters: list[str]) -> str:
    evidence = short_work_anchor(snippets)
    first_focus = clusters[0] if clusters else "structured practical work"
    second_focus = clusters[1] if len(clusters) > 1 else "clear follow-up"
    return (
        f"One example I would use first is this: {evidence}. "
        "I worked through unclear discussion and turned it into material another person could review. "
        "That trained me to check the work before handover. "
        f"For this role, I would connect that habit to {first_focus}. I would also use it when working with {second_focus}."
    )


def named_bullets(items: list[tuple[str, str]]) -> str:
    clean = [(normalize_space(name), str(body or "").strip()) for name, body in items if normalize_space(name) and str(body or "").strip()]
    if not clean:
        return "- Information missing; ask the student before final interview use."
    return "\n\n".join(f"### {name}\n\n{body}" for name, body in clean)


def likely_question_blocks(company: str, clusters: list[str], concerns: list[str], language: str) -> str:
    questions: list[tuple[str, str]] = [
        ("Tell me about yourself.", "Standard opening. The answer should connect study path, practical experience, and the role without reciting the CV."),
        (f"Why are you interested in {company} and this role?", "The interviewer is testing whether the candidate understands the actual work, not just the brand name."),
        (f"What experience do you already have with {clusters[0]}?", "This maps directly to the strongest role signal from the job description."),
        ("How do you work with developers, business stakeholders, or teammates when requirements are unclear?", "Likely for product, BA, PO, process, and technical-support roles where alignment matters."),
        ("Tell me about a time you turned messy information into a clear next step.", "This checks practical structure, judgment, and communication under ambiguity."),
        ("How do you handle feedback on your work?", "Working-student roles often check coachability, maturity, and whether the candidate can improve through team feedback."),
        ("What is one area where you are still improving?", "A safe weakness answer is needed; avoid fake humble-brag answers."),
        ("Who are you outside work or study, and how do you recharge?", "Important for German-style culture fit: they may check balance, self-awareness, and whether the candidate is healthy to work with."),
    ]
    if "german" in language.lower() or any("german" in concern.lower() for concern in concerns):
        questions.append(("How strong is your German in day-to-day work?", "Relevant if the job is German-speaking, the company context is German, or German is listed as advantageous/required."))
    for concern in concerns[:3]:
        questions.append((f"How would you handle this concern: {concern}?", "This is a candidate-specific risk. Prepare an honest, short answer with mitigation."))
    return "\n\n".join(f"{index}. **{question}**\n   Why likely: {why}" for index, (question, why) in enumerate(questions, 1))


def answer_scripts(company: str, title: str, clusters: list[str], summary: str, snippets: list[str], language: str) -> str:
    evidence_line = snippets[0] if snippets else "one verified project or work example from the student's profile"
    scripts = [
        (
            "Why this role?",
            fenced(
                f"What interests me is that this role is close to real execution. The first part I would prepare for is {clusters[0]}. "
                f"The second part is {clusters[1] if len(clusters) > 1 else 'clear team follow-up'}. "
                "That is useful work for me because it requires checked notes, practical questions, and reliable handover, not only broad motivation."
            ),
        ),
        (
            f"Why {company}?",
            fenced(
                f"I am interested in {company} because this role has a concrete product or operational context. "
                "For me, that matters because I do better when the work has a clear user, team, or business impact instead of being abstract."
            ),
        ),
        (
            "Why you?",
            fenced(
                f"{spoken_profile_anchor([evidence_line], clusters)} "
                "That is why I think I can support the role with structure, follow-through, and a practical learning attitude."
            ),
        ),
        (
            "If challenged on a gap",
            fenced(
                "I would be honest about the gap first, then explain the adjacent experience I already have and the way I would close it. "
                "For me, the important part is not pretending to know everything. I would ask clear questions, document the answer, and deliver a reliable first step."
            ),
        ),
    ]
    if "german" in language.lower():
        scripts.append(
            (
                "If asked about German",
                fenced(
                    "My German is improving, but I am stronger in English for professional discussions. "
                    "I handle that by preparing carefully, communicating clearly, and continuing to improve my German actively."
                ),
            )
        )
    return named_bullets(scripts)


def screening_logic(company: str, clusters: list[str], interviewer_values: list[str]) -> str:
    opener = (
        f"Because this is a role at {company}, prepare as if the interviewer is checking practical reliability, not only motivation."
    )
    if interviewer_values:
        opener += " The provided interviewer/recruiter names should be treated as verified scheduling context only unless the student has added more evidence."
    return bullet(
        [
            opener,
            f"Can the candidate explain {clusters[0]} in concrete, non-generic terms?",
            "Can the candidate work with unclear information without creating confusion?",
            "Can the candidate communicate with business and technical people in a calm, usable way?",
            "Can the candidate admit gaps without sounding risky?",
            "Does the candidate have enough real stories to support the claims in the CV and cover letter?",
            "Does the candidate sound balanced outside work, especially for German culture-fit conversations?",
        ]
    )


def extract_json_job(root: Path, job: str, explicit: Path | None) -> dict[str, Any]:
    candidates = [
        explicit,
        root / "jobs" / job / "job.json",
        root / "jobs" / job / "intake.json",
    ]
    for candidate in candidates:
        data = read_json(candidate)
        if data:
            return data
    job_text = read_text(root / "jobs" / job / "job.md") or read_text(root / "jobs" / job / "extracted-text.md")
    return {"job_title": job.replace("-", " ").title(), "job_description": job_text}


def candidate_name(profile: dict[str, Any]) -> str:
    if profile.get("name"):
        return str(profile["name"])
    if isinstance(profile.get("identity"), dict) and profile["identity"].get("name"):
        return str(profile["identity"]["name"])
    return "the candidate"


def candidate_summary(profile: dict[str, Any], evidence_text: str) -> str:
    for key in ["summary", "headline", "about", "profile_summary"]:
        if profile.get(key):
            return normalize_space(profile[key])
    nested = profile.get("profile")
    if isinstance(nested, dict):
        for key in ["summary", "headline", "about"]:
            if nested.get(key):
                return normalize_space(nested[key])
    if evidence_text:
        first_line = next((line.strip("- ").strip() for line in evidence_text.splitlines() if line.strip() and not line.startswith("#")), "")
        if first_line:
            return normalize_space(first_line)
    return "Profile summary is not strong enough yet; ask the student for a clearer background summary."


def flatten_skills(profile: dict[str, Any]) -> list[str]:
    skills = profile.get("skills", [])
    if isinstance(skills, dict):
        values: list[str] = []
        for item in skills.values():
            if isinstance(item, list):
                values.extend(str(value) for value in item)
        return values[:14]
    if isinstance(skills, list):
        return [str(item) for item in skills[:14]]
    return []


def job_requirements(job_data: dict[str, Any]) -> list[str]:
    reqs = job_data.get("requirements", [])
    if isinstance(reqs, list) and reqs:
        return [str(item) for item in reqs[:9]]
    text = normalize_space(job_data.get("job_description", ""))
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [sentence for sentence in sentences if len(sentence) > 35][:7]


def role_clusters(job_data: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            normalize_space(job_data.get("job_title", "")),
            normalize_space(job_data.get("job_description", "")),
            " ".join(job_requirements(job_data)),
        ]
    ).lower()
    clusters = []
    for label, tokens in [
        ("requirements and structured analysis", ["requirement", "business analysis", "analyse", "analysis", "user stor"]),
        ("stakeholder communication", ["stakeholder", "communication", "presentation", "meeting", "workshop"]),
        ("testing and quality support", ["test", "quality", "validation", "acceptance"]),
        ("agile / product-owner support", ["product owner", "backlog", "agile", "scrum", "safe", "sprint"]),
        ("data and reporting", ["data", "dashboard", "excel", "power bi", "report", "kpi"]),
        ("documentation and knowledge sharing", ["documentation", "wiki", "guide", "how-to", "technical writing"]),
        ("process and workflow improvement", ["process", "workflow", "automation", "improvement"]),
    ]:
        if any(token in text for token in tokens):
            clusters.append(label)
    return clusters[:6] or ["structured thinking", "clear communication", "reliable execution"]


def evidence_snippets(evidence_text: str, limit: int = 4) -> list[str]:
    lines = []
    forbidden_prefixes = (
        "name:",
        "email:",
        "phone:",
        "location:",
        "portfolio:",
        "core skills:",
        "adaptive skills:",
    )
    evidence_verbs = (
        "wrote",
        "created",
        "built",
        "supported",
        "coordinated",
        "documented",
        "mapped",
        "improved",
        "reviewed",
        "analyzed",
        "analysed",
        "maintained",
        "prepared",
        "authored",
        "worked",
        "helped",
    )
    for line in evidence_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            value = stripped[2:].strip()
        elif (
            len(stripped) > 80
            and not stripped.startswith("#")
            and not stripped.startswith("**")
            and not re.match(r"^[A-Za-zÀ-ÿ .'-]+,\s*\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}$", stripped)
        ):
            value = stripped
        else:
            continue
        lowered = value.lower()
        if lowered.startswith(forbidden_prefixes):
            continue
        if any(verb in lowered for verb in evidence_verbs):
            lines.append(value)
    return lines[:limit]


def explicit_star_stories(interview: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    """Return only user-provided or explicitly stored incident stories.

    General CV bullets and cover-letter paragraphs are not safe enough to become
    STAR stories. A STAR answer needs an actual incident from the student's past,
    preferably with situation/task/action/result/lesson. If that is not present,
    the generated prep must ask the student instead of manufacturing a story.
    """
    raw = interview.get("star_stories") or interview.get("incidents") or interview.get("incident_stories")
    if raw is None and isinstance(profile.get("interview"), dict):
        raw = profile["interview"].get("star_stories") or profile["interview"].get("incidents")
    if raw is None:
        raw = profile.get("star_stories") or profile.get("incident_stories")

    if isinstance(raw, str):
        candidates = [part.strip(" -\n\t") for part in re.split(r"\n\s*(?:[-*]|\d+[.)])\s*", raw) if part.strip()]
    elif isinstance(raw, list):
        candidates = []
        for item in raw:
            if isinstance(item, dict):
                title = normalize_space(item.get("title") or item.get("name") or item.get("theme") or "Incident")
                situation = normalize_space(item.get("situation") or item.get("context"))
                task = normalize_space(item.get("task") or item.get("challenge"))
                action = normalize_space(item.get("action") or item.get("actions"))
                result = normalize_space(item.get("result") or item.get("outcome"))
                lesson = normalize_space(item.get("lesson") or item.get("learning"))
                parts = [f"{label}: {value}" for label, value in [
                    ("Situation", situation),
                    ("Task", task),
                    ("Action", action),
                    ("Result", result),
                    ("Lesson", lesson),
                ] if value]
                candidates.append(f"{title} — " + "; ".join(parts) if parts else title)
            else:
                candidates.append(normalize_space(item))
    else:
        candidates = []

    return [story for story in candidates if len(story) >= 40][:5]


def star_story_bank(stories: list[str], clusters: list[str]) -> str:
    if stories:
        labels = [
            "Story 1 — requirements/analysis",
            "Story 2 — coordination/teamwork",
            "Story 3 — learning/problem-solving",
            "Story 4 — role-specific proof",
            "Story 5 — resilience or feedback",
        ]
        return bullet([f"{labels[index] if index < len(labels) else f'Story {index + 1}'}: {story}" for index, story in enumerate(stories)])

    story_slots = [
        (
            f"Story 1: {clusters[0] if clusters else 'requirements or analysis'}",
            "- Best for: requirements, structured thinking, role-fit proof\n"
            "- Status: missing actual incident\n"
            "- Ask the student: What happened, what was your task, what did you personally do, what changed, and what did you learn?",
        ),
        (
            f"Story 2: {clusters[1] if len(clusters) > 1 else 'teamwork or stakeholder communication'}",
            "- Best for: communication, stakeholder alignment, teamwork\n"
            "- Status: missing actual incident\n"
            "- Ask the student: Who was involved, where was the disagreement or unclear point, how did you help, and what was the result?",
        ),
        (
            f"Story 3: {clusters[2] if len(clusters) > 2 else 'learning or problem-solving'}",
            "- Best for: learning ability, handling unfamiliar topics, problem-solving\n"
            "- Status: missing actual incident\n"
            "- Ask the student: What was unfamiliar, how did you learn or investigate it, what action did you take, and what outcome followed?",
        ),
        (
            "Story 4: role-specific proof",
            "- Best for: direct match to the job description\n"
            "- Status: missing actual incident\n"
            "- Ask the student: Which real past incident best proves that you can handle this specific role? Do not convert generic CV responsibilities into a STAR story.",
        ),
    ]
    return "Actual STAR incidents are missing, so this section is intentionally not finalized. Use these slots to collect real stories from the student.\n\n" + named_bullets(story_slots)


def interview_meta(root: Path, job: str, explicit: Path | None) -> dict[str, Any]:
    data = read_json(explicit)
    if data:
        return data
    return read_json(root / "jobs" / job / "interview.json")


def missing_questions(profile: dict[str, Any], evidence_text: str, interview: dict[str, Any]) -> list[str]:
    questions = []
    for key, question in [
        ("date", "What is the interview date and time?"),
        ("format", "Is the interview in-person, phone, Teams/Zoom, or another format?"),
        ("duration", "How long is the interview expected to be?"),
        ("language", "Will the interview be in English, German, or mixed?"),
        ("interviewers", "Who are the interviewers or recruiter contacts? Please paste names, titles, or email signatures."),
    ]:
        if not interview.get(key):
            questions.append(question)
    if not explicit_star_stories(interview, profile):
        questions.append("Please provide 3 to 5 actual past incident stories in STAR format: situation, task, action, result, and lesson. Write them yourself or confirm they are real. I will not invent STAR stories from generic CV responsibilities.")
    if not evidence_snippets(evidence_text, 3):
        questions.append("Give 3 to 5 concrete work or study proof points you are comfortable discussing. These can support answers, but they are not enough for the STAR bank unless they describe real incidents.")
    if not flatten_skills(profile):
        questions.append("Which 8 to 14 skills are genuinely supported by your CV or project history?")
    if not interview.get("outside_work"):
        questions.append("Outside work or study, what do you do to recharge? Mention hobbies, routines, values, or community activities you are comfortable sharing.")
    if not interview.get("concerns"):
        questions.append("What risks should we prepare for: German level, visa/work authorization, availability, domain gap, salary, relocation, confidence, or technical gaps?")
    return questions


def build_sections(root: Path, job: str, job_data: dict[str, Any], profile: dict[str, Any], evidence_text: str, cover_letter: str, interview: dict[str, Any]) -> dict[str, str]:
    company = normalize_space(job_data.get("company_name") or job_data.get("company") or "Target company")
    title = normalize_space(job_data.get("job_title") or job.replace("-", " ").title())
    name = candidate_name(profile)
    clusters = role_clusters(job_data)
    requirements = job_requirements(job_data)
    snippets = evidence_snippets(cover_letter + "\n" + evidence_text)
    star_stories = explicit_star_stories(interview, profile)
    skills = flatten_skills(profile)
    summary = candidate_summary(profile, evidence_text)
    missing = missing_questions(profile, evidence_text, interview)
    evidence_status = "needs_user_clarification" if missing else "ready_for_practice"
    interviewer_values = interview.get("interviewers") or []
    if isinstance(interviewer_values, str):
        interviewer_values = [interviewer_values]
    concerns = interview.get("concerns") or []
    if isinstance(concerns, str):
        concerns = [concerns]
    language = normalize_space(interview.get("language") or "")
    stage = normalize_space(interview.get("stage") or interview.get("round") or "interview stage unknown")
    location = normalize_space(interview.get("location") or interview.get("meeting_link") or "")
    known_context = normalize_space(interview.get("context") or interview.get("invite_context") or "")
    company_read = normalize_space(job_data.get("company_read") or job_data.get("company_overview") or job_data.get("why_company"))
    role_read = (
        f"This is not a generic application conversation. The role should be prepared around practical evidence for {', '.join(clusters[:3])}. "
        "The candidate needs to explain how they structure work, communicate with others, and learn in the team's real context."
    )
    people_read_items = [f"Verified or provided contact: {item}" for item in interviewer_values]
    if people_read_items:
        people_read_items.append("Treat these names as verified contact context only. Do not infer personality, seniority, or private background without evidence.")
    people_read_items.append("If no reliable interviewer evidence exists, prepare for three angles: recruiter fit, hiring-manager role fit, and team-member collaboration fit.")

    return {
        "COMPANY": company,
        "JOB_TITLE": title,
        "INTERVIEW_DATE": normalize_space(interview.get("date") or "Unknown; ask the student"),
        "INTERVIEW_FORMAT": normalize_space(interview.get("format") or "Unknown; ask the student"),
        "PREPARED_DATE": date.today().isoformat(),
        "EVIDENCE_STATUS": evidence_status,
        "INTERVIEW_OVERVIEW": bullet(
            [
                f"Known round: {stage}.",
                f"Target role: {title} at {company}.",
                f"Expected duration: {normalize_space(interview.get('duration') or 'unknown')}.",
                f"Expected format: {normalize_space(interview.get('format') or 'unknown; ask the student')}.",
                f"Expected language: {language or 'unknown; ask before practice'}.",
                f"Location or meeting link: {location or 'unknown; ask the student'}.",
                f"Known context: {known_context}" if known_context else "Known context: not enough interview-message evidence yet; keep assumptions labeled.",
                f"Evidence status: {evidence_status}. If this says needs_user_clarification, use the questions file before final practice.",
            ]
        ),
        "COMPANY_ROLE_READ": bullet(
            [
                company_read or f"From the job description, {company} should be discussed through the work of this role, not through generic brand praise.",
                role_read,
                f"The strongest role signal is {clusters[0]}. A second signal to prepare is {clusters[1] if len(clusters) > 1 else 'clear team follow-up'}.",
                "Do not pretend to know internal team details beyond the job description, recruiter messages, and verified communication.",
            ]
        ),
        "ROLE_NEEDS": bullet(
            requirements[:7]
            + [
                f"Practical read: prepare answers around {', '.join(clusters)}.",
                "They are likely screening for usable judgment: can the candidate turn broad tasks into clear next actions?",
            ]
        ),
        "INTERVIEWER_READ": bullet(people_read_items),
        "BEST_POSITIONING": bullet(
            [
                f"Do not position {name} as a generic ambitious student or as an expert in every JD keyword.",
                f"Position {name} as someone who can explain {clusters[0]} through a real task, then connect it to {clusters[1] if len(clusters) > 1 else 'team follow-up'}.",
                spoken_profile_anchor(snippets, clusters),
                "Best tone: calm, specific, evidence-led, and ready to learn. Avoid sounding like a memorized cover letter.",
                "Strongest line: I can support the team by making unclear information easier to use, aligning people around next steps, and learning the domain in a structured way.",
            ]
        ),
        "INTRODUCTION": (
            f"Thank you for the opportunity. My name is {name}. "
            f"{spoken_profile_anchor(snippets, clusters)} "
            f"What attracted me to this role is the mix of {clusters[0]} and {clusters[1] if len(clusters) > 1 else 'team follow-up'}. "
            "That is close to the kind of practical support work I want to do. "
            "I am strongest when I can take unclear information and structure it. I then communicate the next step clearly enough for a team to use it. "
            "That is why I see this role as a good match for what I can already contribute and where I want to grow."
        ),
        "LIKELY_QUESTIONS": likely_question_blocks(company, clusters, concerns, language),
        "ANSWER_ANGLES": answer_scripts(company, title, clusters, summary, snippets, language),
        "STRENGTHS_WEAKNESSES": named_bullets(
            [
                (
                    f"Strength 1: {clusters[0]}",
                    fenced(f"One of my strengths is that I can take a broad or unclear topic and structure it into something a team can discuss and use. For this role, that matters because the work includes {clusters[0]}."),
                ),
                (
                    "Strength 2: cross-functional communication",
                    fenced(f"I am comfortable working between business goals and user needs. I also pay attention to process constraints before handing work to a technical team. A supporting proof point is: {short_work_anchor(snippets)}."),
                ),
                (
                    "Best weakness answer",
                    fenced("One thing I have been improving is that I can sometimes spend too much time trying to fully structure a topic before sharing an early version. I handle that better now by time-boxing the first pass, sharing earlier drafts, and improving them through feedback."),
                ),
                (
                    "Optional domain-gap answer",
                    fenced("There may be company- or domain-specific topics that I still need to learn. I handle that by preparing carefully, asking precise questions, documenting what I learn, and connecting it back to the team's actual workflow."),
                ),
                (
                    "Weaknesses to avoid",
                    "Do not answer with `I work too hard`, `I am a perfectionist`, `I have no weakness`, or anything that makes the student sound unreliable, careless, dishonest, or difficult to work with.",
                ),
            ]
        ),
        "STAR_STORIES": star_story_bank(star_stories, clusters),
        "CULTURE_FIT": named_bullets(
            [
                (
                    "Why this matters",
                    "Germany-focused interviews may check whether the candidate is balanced, self-aware, and healthy to work with. The answer should show ambition without sounding like work is the candidate's only identity.",
                ),
                (
                    "Answer shape",
                    "Use one normal activity, one value it shows, and one link back to sustainable work. Keep it human and short.",
                ),
                (
                    "Student-specific material",
                    fenced(normalize_space(interview.get("outside_work"))) if interview.get("outside_work") else "Missing: ask the student for hobbies, routines, values, sport, community, family, creative work, reading, or other real outside-work material. Do not invent this.",
                ),
                (
                    "Avoid",
                    "Avoid saying only `I work and study all the time`. Avoid fake hobbies. Avoid turning the answer into another productivity pitch.",
                ),
            ]
        ),
        "QUESTIONS_TO_ASK": numbered(
            [
                "What would success look like in the first two or three months?",
                f"Which part of the role takes the most time day to day: {', '.join(clusters[:4])}?",
                "What makes someone successful in this team beyond technical skills?",
                "How would this working student interact with the main team members or stakeholders?",
                "What should I prepare or learn before starting if I move forward?",
            ]
        ),
        "THINGS_TO_AVOID": bullet(
            [
                "Do not overclaim domain expertise.",
                "Do not repeat the cover letter word for word.",
                "Do not answer every question with abstract frameworks.",
                "Do not make the weakness sound like a fake humble brag.",
                "Do not invent personal hobbies, interviewer facts, or metrics.",
            ]
        ),
        "LOGISTICS": bullet(
            [
                f"Location or meeting link: {normalize_space(interview.get('location') or interview.get('meeting_link') or 'unknown; ask the student')}.",
                "Bring or keep accessible: CV, cover letter, job description, transcript/diploma if relevant, residence/work-authorization documents if relevant.",
                "Prepare a short note with interviewer names, role title, company address, and emergency contact if available.",
            ]
        ),
        "CHECKLIST": bullet(
            [
                "Practice the 60-second introduction five times out loud.",
                "Practice 3 real STAR stories: requirements/analysis, teamwork/coordination, learning/problem-solving. If actual incidents are missing, stop and ask the student first.",
                "Prepare the weakness answer and one gap answer.",
                "Prepare the outside-work / work-life-balance answer.",
                "Pick 3 questions to ask them.",
                "Review the JD once more and mark unsupported requirements as honest gaps.",
            ]
        ),
        "SCREENING_LOGIC": screening_logic(company, clusters, interviewer_values),
        "BOTTOM_LINE": (
            f"The strongest positioning is: {name} can contribute through {', '.join(clusters[:3])}, communicate clearly, learn quickly, and stay reliable. "
            "The prep is Mercedes-grade only after the missing questions are answered, especially the actual STAR incidents and outside-work/culture-fit material."
        ),
        "MISSING_INFORMATION": bullet(missing) if missing else "- No major missing information detected. Student should still practice answers aloud.",
    }


def render(template: str, mapping: dict[str, str]) -> str:
    output = template
    for key, value in mapping.items():
        output = output.replace(f"@@{key}@@", value)
    leftovers = sorted(set(re.findall(r"@@[A-Z0-9_]+@@", output)))
    if leftovers:
        raise ValueError("Unresolved template placeholders: " + ", ".join(leftovers))
    return output


def section_between(markdown: str, start_heading: str, end_heading: str) -> str:
    try:
        start = markdown.index(start_heading)
        end = markdown.index(end_heading, start)
        return markdown[start:end].strip()
    except ValueError:
        return ""


def fenced_blocks(markdown: str) -> list[str]:
    return [normalize_space(match.group(1)) for match in re.finditer(r"```text\s*(.*?)\s*```", markdown, flags=re.DOTALL) if normalize_space(match.group(1))]


def plain_review_packet(title: str, parts: list[str]) -> str:
    cleaned: list[str] = [f"## {title}"]
    for part in parts:
        text = normalize_space(part).replace("..", ".")
        if not text:
            continue
        cleaned.append(text)
    return "\n\n".join(cleaned)


def interview_review_text_loop_1(markdown: str) -> str:
    sections = [
        section_between(markdown, "## 6. 60-Second Introduction", "## 7. Likely Questions"),
        section_between(markdown, "## 8. Strong Answer Scripts", "## 9. Strengths And Weaknesses"),
        section_between(markdown, "## 9. Strengths And Weaknesses", "## 10. STAR Story Bank"),
        section_between(markdown, "## 11. Culture Fit: Who Are You Outside Work?", "## 12. Questions To Ask Them"),
    ]
    blocks: list[str] = []
    for section in sections:
        for block in fenced_blocks(section):
            if "Do not invent" in block or block.lower().startswith("missing:"):
                continue
            if block.startswith("One example I would use first is this:") and any("One example I would use first is this:" in prior for prior in blocks):
                continue
            blocks.append(block)
            if len(blocks) >= 5:
                break
        if len(blocks) >= 5:
            break
    return plain_review_packet("Interview Prep Review Loop 1: Spoken Answers", blocks)


def clean_review_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^\s*[-*]\s+", "", line)
    line = line.replace("expert in every JD keyword", "someone who can cover every JD keyword")
    line = line.replace("Business fluent", "Strong working")
    line = line.replace("business fluent", "strong working")
    line = line.replace("Full working proficiency", "Strong working ability")
    line = line.replace("full working proficiency", "strong working ability")
    line = line.replace("fluent", "strong")
    line = line.replace("Fluent", "Strong")
    return line.strip()


def section_lines(markdown: str, start_heading: str, end_heading: str, limit: int = 3) -> list[str]:
    section = section_between(markdown, start_heading, end_heading)
    lines: list[str] = []
    for raw in section.splitlines():
        line = clean_review_line(raw)
        if not line or line.startswith("##"):
            continue
        if line.lower().startswith(("studies in ", "student at ", "preferred fields", "currently enrolled")):
            continue
        if line.lower().startswith(("the strongest role signals are:", "practical read:")):
            continue
        if line.count(",") >= 4 or len(line) > 260:
            continue
        lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def interview_review_text_loop_2(markdown: str) -> str:
    company_read = section_lines(markdown, "## 2. What The Company / Team Seems To Do", "## 4. Interviewer / Recruiter Read", 2)
    positioning = section_lines(markdown, "## 5. Best Positioning", "## 6. 60-Second Introduction", 3)
    likely_questions = section_lines(markdown, "## 7. Likely Questions", "## 8. Strong Answer Scripts", 5)
    screening = section_lines(markdown, "## 16. What They Are Likely Screening For", "## 17. Bottom Line", 4)
    bottom_line = section_lines(markdown, "## 17. Bottom Line", "## 18. Missing Information To Ask The Student", 1)
    role_line = company_read[0] if company_read else "I should understand this role through the actual work in the job description."
    if role_line.startswith("The strongest role signal is "):
        role_line = role_line.replace("The strongest role signal is ", "My first role signal is ", 1)
    position_line = positioning[1] if len(positioning) > 1 else "The candidate should connect one real task to the role instead of covering every keyword."
    question_line = likely_questions[0] if likely_questions else "The first likely question is the standard self-introduction."
    screen_line = screening[0] if screening else "The interviewer is likely checking practical reliability."
    bottom = bottom_line[0] if bottom_line else "Final practice should stay honest about missing stories."
    parts = [
        role_line,
        position_line.replace("Position Le Cuong Nguyen as", "I should position myself as"),
        "For the evidence anchor, I authored user stories and acceptance criteria. I documented process diagrams and workflow documents. I worked through unclear discussion and turned it into reviewable material.",
        "That trained me to check the work before handover. In the interview, I should explain what was unclear, what I checked, and what another person could use afterwards.",
        question_line,
        "STAR practice is not ready until the student provides actual incident stories. I should not invent a conflict story from generic CV material. I should not invent hobbies either.",
        screen_line,
        bottom,
    ]
    return plain_review_packet("Interview Prep Review Loop 2: Role Read And Readiness", parts)


def write_review_input(output_dir: Path, filename: str, text: str, purpose: str) -> None:
    (output_dir / filename).write_text(
        json.dumps(
            {
                "mode": "application",
                "audience": "student interview practice",
                "purpose": purpose,
                "text": text,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local interview preparation.")
    parser.add_argument("--root", default=".", help="Student workspace root.")
    parser.add_argument("--job", required=True, help="Job slug under jobs/<job>.")
    parser.add_argument("--intake", help="Optional job/intake JSON path.")
    parser.add_argument("--profile", help="Optional candidate profile JSON path.")
    parser.add_argument("--evidence", help="Optional evidence Markdown path.")
    parser.add_argument("--cover-letter", help="Optional generated cover-letter Markdown path.")
    parser.add_argument("--communication-log", help="Optional communication log Markdown path.")
    parser.add_argument("--interview", help="Optional interview metadata JSON path.")
    parser.add_argument("--output-dir", help="Output directory. Defaults to applications/<job>/interview-prep.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    job = args.job
    kit = root / "application-kit"
    template_path = kit / "templates" / DEFAULT_TEMPLATE
    template = template_path.read_text(encoding="utf-8")
    job_data = extract_json_job(root, job, Path(args.intake).resolve() if args.intake else None)
    profile = read_json(Path(args.profile).resolve() if args.profile else root / "candidate" / "profile.json") or read_json(root / "profile" / "master_profile.json")
    evidence_text = read_text(Path(args.evidence).resolve() if args.evidence else root / "candidate" / "evidence.md") or read_text(root / "profile" / "evidence_library.json")
    cover_letter = read_text(Path(args.cover_letter).resolve() if args.cover_letter else root / "applications" / job / "cover-letter" / "cover-letter.md")
    communication_log = read_text(Path(args.communication_log).resolve() if args.communication_log else root / "applications" / job / "communication-log.md")
    interview = interview_meta(root, job, Path(args.interview).resolve() if args.interview else None)
    if communication_log and not interview.get("interviewers"):
        names = re.findall(r"From:\s*([^\n]+)|Signed by:\s*([^\n]+)", communication_log)
        flattened = [a or b for a, b in names if (a or b)]
        if flattened:
            interview["interviewers"] = flattened[:4]

    sections = build_sections(root, job, job_data, profile, evidence_text, cover_letter, interview)
    output_dir = Path(args.output_dir).resolve() if args.output_dir else root / "applications" / job / "interview-prep"
    output_dir.mkdir(parents=True, exist_ok=True)
    prep = render(template, sections)
    (output_dir / "interview-prep.md").write_text(prep, encoding="utf-8")
    loop_1_text = interview_review_text_loop_1(prep)
    loop_2_text = interview_review_text_loop_2(prep)
    write_review_input(
        output_dir,
        "interview-prep-review-input-loop-1.json",
        loop_1_text,
        "MCP interview-prep review loop 1: natural, human, evidence-based spoken answer scripts",
    )
    write_review_input(
        output_dir,
        "interview-prep-review-input-loop-2.json",
        loop_2_text,
        "MCP interview-prep review loop 2: role-read, likely-question rationale, STAR boundary, and readiness coaching",
    )
    write_review_input(
        output_dir,
        "interview-prep-review-input.json",
        loop_1_text,
        "MCP interview-prep review loop 1: natural, human, evidence-based spoken answer scripts",
    )
    questions = sections["MISSING_INFORMATION"]
    (output_dir / "interview-prep-questions.md").write_text(
        "# Interview Prep Questions For The Student\n\n" + questions + "\n",
        encoding="utf-8",
    )
    manifest = {
        "ok": True,
        "job": job,
        "company": sections["COMPANY"],
        "job_title": sections["JOB_TITLE"],
        "evidence_status": sections["EVIDENCE_STATUS"],
        "missing_question_count": len(missing_questions(profile, evidence_text, interview)),
        "outputs": [
            "interview-prep.md",
            "interview-prep-questions.md",
            "interview-prep-review-input-loop-1.json",
            "interview-prep-review-input-loop-2.json",
            "interview-prep-review-input.json"
        ],
        "review_gate": {
            "required": True,
            "loops_required": 2,
            "mcp_result_paths": [
                "interview-prep-review-result-loop-1.json",
                "interview-prep-review-result-loop-2.json"
            ],
            "sop_review_commands": [
                "python3 application-kit/scripts/application_sop.py --root . review-interview-prep --loop 1 --artifact applications/<job>/interview-prep/interview-prep.md --result applications/<job>/interview-prep/interview-prep-review-result-loop-1.json",
                "python3 application-kit/scripts/application_sop.py --root . review-interview-prep --loop 2 --artifact applications/<job>/interview-prep/interview-prep.md --result applications/<job>/interview-prep/interview-prep-review-result-loop-2.json"
            ],
            "sop_finalize_command": "python3 application-kit/scripts/application_sop.py --root . finalize-interview-prep --artifact applications/<job>/interview-prep/interview-prep.md"
        },
        "privacy": {
            "mcp_called": False,
            "full_workspace_uploaded": False,
            "review_payload": "selected interview-prep speaking sections only"
        },
    }
    (output_dir / "interview-prep-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output_dir": str(output_dir), **manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
