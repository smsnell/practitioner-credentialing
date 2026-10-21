"""Record the supplied Clinical Director dispositions without making judgments.

Callers provide documents already limited to the relevant assessment date. A
valid disposition is retained even when its specifically referenced evidence
is missing; authority and evidence sufficiency are separate facts.
"""

from datetime import date
import re

from .documents import document_conflicts, period
from .policy import normalized, person


def _valid_date(value):
    try:
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and bool(date.fromisoformat(value))
    except (TypeError, ValueError):
        return False


def _sentences(text):
    # Only the narrative is scanned for explicit dispositions. Labelled fields
    # and headings cannot supply an instruction such as discontinuation.
    prose = "\n".join(line for line in text.splitlines() if not line.startswith(("#", "**")))
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+|\n+", prose) if sentence.strip()]


def _authority(doc, app, reg):
    fields, index, reasons = doc["fields"], doc.get("index", {}), []
    for name in ("date", "application", "applicant", "recorded_by"):
        if not fields.get(name):
            reasons.append("Missing required disposition field: " + name)
    if index.get("application_id") != app["application_id"]:
        reasons.append("Correspondence application does not match assessed application")
    if not index.get("date"):
        reasons.append("Correspondence date is missing")
    else:
        reasons.extend(document_conflicts(doc, app))
    when = fields.get("date", "")
    if not _valid_date(when):
        reasons.append("Disposition date is not a valid recorded ISO date")
    role = next((item for item in reg["roles"] if item["role"] == "Clinical Director"), None)
    author = re.fullmatch(r"(.+),\s*Clinical Director", fields.get("recorded_by", ""), re.IGNORECASE)
    if role is None or author is None or person(author[1]) != person(role["name"]):
        reasons.append("Recorded by is not the rostered Clinical Director in that role")
    elif not _valid_date(when) or ((role.get("start") and when < role["start"]) or (role.get("end") and when > role["end"])):
        reasons.append("Clinical Director did not hold the role on the recorded disposition date")
    # The four supplied records use a standalone name and role as their footer.
    # A label claiming authorship alone is not the signed-record evidence.
    footer = [line.strip() for line in doc["text"].splitlines() if line.strip()]
    if (role is None or len(footer) < 2 or normalized(footer[-1]) != "clinical director"
            or person(footer[-2]) != person(role["name"])):
        reasons.append("Disposition lacks the rostered Clinical Director's name/role signature footer")
    return reasons


def _gap_evidence(app, doc, documents, gap, required_dates):
    qualifying = []
    expected_names = {person(" ".join([app["first_name"], app["last_name"]])),
                      person(" ".join([app["first_name"], app["middle_name"], app["last_name"]]))}
    for explanation in documents:
        index, fields = explanation.get("index", {}), explanation["fields"]
        when = index.get("date", "")
        explained = period(explanation)
        if (index.get("application_id") != app["application_id"] or index.get("direction") != "inbound"
                or not _valid_date(when) or when > doc["fields"].get("date", "")
                or explained is None or not all(_valid_date(value) for value in explained)
                or explained[0] > gap[0] or explained[1] < gap[1]
                or person(fields.get("from", "")) not in expected_names
                or document_conflicts(explanation, app)):
            continue
        if not required_dates or when in required_dates:
            qualifying.append(explanation)
    missing = [when for when in required_dates if not any(item["index"]["date"] == when for item in qualifying)]
    reasons = ["Specifically referenced applicant explanation missing or not qualifying: " + when for when in missing]
    if not required_dates and not qualifying:
        reasons.append("No qualifying applicant explanation covers the full disposed gap")
    return [item["path"] for item in qualifying], missing, reasons


def clinical_dispositions(app, docs, reg):
    """Return source records, authority checks, and narrowly explicit tags.

    `authorized` concerns roster/signature/identity/date only. `gap_cleared`
    additionally requires the recorded satisfactory judgment and every named
    explanation covering the entire disposed period. No tag verifies unrelated
    evidence, changes declarations, recommends appointment, or grants privileges.
    """
    records = []
    for doc in docs:
        title = doc.get("title", "")
        if not re.match(r"^Clinical Director['’]s disposition\b", title, re.IGNORECASE):
            continue
        if (doc.get("index", {}).get("application_id") != app["application_id"]
                and doc["fields"].get("application") != app["application_id"]):
            continue
        reasons = _authority(doc, app, reg)
        authorized = not reasons
        sentences = _sentences(doc["text"])
        terminal = any(re.match(r"^Discontinue the application\b", sentence, re.IGNORECASE) for sentence in sentences)
        amendment = any(re.match(r"^Offer the applicant the opportunity to amend the privilege request\b", sentence, re.IGNORECASE) for sentence in sentences)
        gap_match = re.search(r"\b(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})\b", title)
        gap = tuple(gap_match.groups()) if gap_match else None
        evidence_reasons, paths, missing = [], [], []
        if gap is not None and (not all(_valid_date(value) for value in gap) or gap[0] > gap[1]):
            evidence_reasons.append("Disposed gap period is invalid")
            gap = None
        required_dates = sorted(set(re.findall(r"\bexplanation of (\d{4}-\d{2}-\d{2})\b", doc["text"], re.IGNORECASE)))
        satisfactory = any(re.match(r"^(?:The )?explanation is sufficient\b", sentence, re.IGNORECASE) for sentence in sentences)
        if gap:
            paths, missing, gap_reasons = _gap_evidence(app, doc, docs, gap, required_dates)
            evidence_reasons.extend(gap_reasons)
        records.append({"path": doc["path"], "text": doc["text"], "topic": re.sub(r"^Clinical Director['’]s disposition\s*[—–-]?\s*", "", title, flags=re.IGNORECASE),
                        "date": doc["fields"].get("date"), "authorized": authorized, "reasons": reasons,
                        "terminal": "discontinued" if authorized and terminal else None,
                        "gap_period": gap, "required_explanation_dates": required_dates,
                        "ppq_codes": sorted(set(re.findall(r"\bPPQ-\d+\b", title + "\n" + doc["text"]))),
                        "amendment_offered": authorized and amendment, "gap_satisfactory": satisfactory,
                        "explanation_paths": paths, "missing_explanation_dates": missing,
                        "evidence_reasons": evidence_reasons,
                        "gap_cleared": bool(authorized and gap and satisfactory and paths and not evidence_reasons)})
    return records
