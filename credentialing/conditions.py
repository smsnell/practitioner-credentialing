"""Read explicit condition satisfaction records without inferring completion.

This bounded input format requires labelled approval/condition/date bindings and
a rostered author's signed footer. Unrecognized or incomplete records remain
visible for MSP review; they do not establish that a condition is unmet forever.
"""

from copy import deepcopy
import re

from .documents import document_conflicts
from .intake_evidence import valid_date
from .policy import normalized


def _routine_wa_reverification(condition):
    """Recognize two explicit routine formats, without interpreting judgments."""
    if re.fullmatch(r"Reverify Washington licen[cs]e(?: [A-Za-z0-9-]+)?(?:\s*[—–-]\s*due \d{4}-\d{2}-\d{2})?", condition, re.IGNORECASE):
        return True
    return bool(re.fullmatch(r"Reverify Washington licence \S+ before expiry; recorded due date is expiry under P Check 1\.", condition))


def condition_satisfaction(app, approval_fields, conditions, docs, reg, as_of):
    """Return valid and rejected source records for this application's approval.

    ``matched_condition`` retains the exact original condition and due date.
    Callers may remove a condition from current monitoring only when a record's
    ``satisfied`` is true, while preserving both the condition and these records
    in history. This helper grants no privileges or clinical disposition.
    """
    records = []
    for doc in docs:
        fields, index = doc.get("fields", {}), doc.get("index", {})
        if not (fields.get("approval_decision_id") or fields.get("condition")
                or normalized(doc.get("title", "")) == "condition satisfaction"):
            continue
        if app["application_id"] not in (fields.get("application"), index.get("application_id")):
            continue
        failures = []
        for label in ("application", "revision", "approval_decision_id", "condition", "due", "date", "outcome", "recorded_by"):
            if not fields.get(label):
                failures.append("Missing required satisfaction field: " + label)
        if fields.get("application") != app["application_id"] or index.get("application_id") != app["application_id"]:
            failures.append("Satisfaction record application does not match")
        if str(fields.get("revision", "")) != str(app["revision"]) or fields.get("revision") != approval_fields.get("revision"):
            failures.append("Satisfaction record does not match the approval/application revision")
        if fields.get("approval_decision_id") != approval_fields.get("decision_id"):
            failures.append("Satisfaction record names a different approval decision")
        if (approval_fields.get("application") != app["application_id"]
                or approval_fields.get("body") != "Governing Body"
                or approval_fields.get("outcome") not in {"approved", "approved-with-conditions"}):
            failures.append("Named decision is not this application's Governing Body approval")
        matches = [condition for condition in conditions if fields.get("condition") == condition["condition"]
                   and fields.get("due") == condition["due"]]
        matched = deepcopy(matches[0]) if len(matches) == 1 else None
        if matched is None:
            failures.append("Satisfaction record does not name one exact condition and its due date")
        when, received = fields.get("date", ""), index.get("date", "")
        approval_date = approval_fields.get("decision_date", "")
        if not valid_date(when) or not valid_date(approval_date) or not approval_date <= when <= as_of:
            failures.append("Satisfaction date is invalid, before approval, or after export")
        if not valid_date(received) or not approval_date <= received <= as_of:
            failures.append("Satisfaction receipt date is invalid, before approval, or after export")
        if index.get("direction") != "inbound" or not doc.get("path") or index.get("document_path") != doc.get("path"):
            failures.append("Satisfaction record is not bound to indexed received evidence")
        failures.extend(document_conflicts(doc, app))
        if normalized(fields.get("outcome", "")) != "satisfied":
            failures.append("Satisfaction outcome must explicitly say satisfied")
        authors = []
        for role in reg["roles"]:
            combined = role["name"] + ", " + role["role"]
            identified = (normalized(fields.get("recorded_by", "")) == normalized(combined)
                          or (normalized(fields.get("recorded_by", "")) == normalized(role["name"])
                              and normalized(fields.get("role", "")) == normalized(role["role"])))
            if identified and (not fields.get("role") or normalized(fields["role"]) == normalized(role["role"])):
                authors.append(role)
        if len(authors) != 1:
            failures.append("Satisfaction author name and role are not bound to one roster entry")
        else:
            author = authors[0]
            if (not valid_date(when) or (author.get("start") and when < author["start"])
                    or (author.get("end") and when > author["end"])):
                failures.append("Satisfaction author did not hold the role on the recorded date")
            supported = (author["role"] == "Clinical Director" or
                         (author["role"] == "Medical Services Professional" and matched
                          and _routine_wa_reverification(matched["condition"])))
            if not supported:
                failures.append("Unsupported satisfaction evidence format; MSP review required (parser limitation, not an office authority restriction)")
            footer = next((line.strip() for line in reversed(doc.get("text", "").splitlines()) if line.strip()), "")
            expected = f"Signed: {author['name']}, {author['role']}, {when}."
            if normalized(footer) != normalized(expected):
                failures.append("Satisfaction record lacks the named author's signed name/role/date footer")
        records.append({"source": doc.get("path"), "fields": deepcopy(fields), "text": doc.get("text", ""),
                        "valid": not failures, "satisfied": not failures,
                        "matched_condition": matched, "failures": failures})
    return records
