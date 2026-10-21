"""Reconcile changed declarations against facts in retained verification (B04/B23).

Procedure §§2, 8 and 11 require entry-specific reconciliation, without a new
request-date condition. This helper assesses facts only. Its caller must still
check source authority, receipt dates, reply outcome, dates and open disputes.
"""

import re


def _normal(value):
    return " ".join(str(value or "").casefold().split())


def _role_facts(reply):
    facts = []
    if reply.get("verified_role"):
        facts.append(("verified_role", reply["verified_role"]))
    credential = reply.get("verified_credential", "")
    match = re.fullmatch(r"(Employment|Affiliation|Degree|Residency|Fellowship|Internship)\s*[—–-]\s*(.+)", credential, re.IGNORECASE)
    if match:
        kind, value = match.groups()
        if kind.casefold() in {"residency", "fellowship", "internship"}:
            if not _normal(value).endswith(kind.casefold()):
                value += " " + kind
        facts.append(("verified_credential", value))
    return facts


def verified_role(reply: dict) -> str | None:
    """Return one unambiguous normalized role from structured reply evidence.

    Case and whitespace are normalized. ``Degree — Doctor of Medicine`` yields
    ``doctor of medicine``; ``Residency — Family Medicine`` yields
    ``family medicine residency`` (likewise fellowship/internship). Employment
    and affiliation prefixes are removed. Explicit ``verified_role`` is also
    considered; if it contradicts the credential label, return None. Unlabelled
    free text and notes yield no inferred role. This is a fact extraction helper,
    not source acceptance, currency or completeness approval.
    """
    values = {_normal(value) for _, value in _role_facts(reply)}
    return values.pop() if len(values) == 1 else None


def assess_revision(entry: dict, histories: list[dict], reply: dict) -> dict:
    """Return ``changed_fields``, ``missing_facts`` and ``conflicts``.

    ``entry`` is one current declared-history row. ``histories`` may contain
    multiple applications/revisions; only this application/entry's strictly
    lower revisions are compared. Each field uses its most recent differing
    prior value, so a later contact-only revision cannot hide an unsupported
    earlier role change. No predecessor means no revision changes to reconcile
    (the caller still verifies the original entry).

    ``changed_fields`` maps each changed nonidentity field to previous/current
    raw values, their revision numbers and an ``evidence`` list. Each evidence
    item records a reply field, extracted value and source reference.
    ``missing_facts`` and ``conflicts`` are lists of dictionaries containing
    field, declared value, reason and source_refs; conflicts also retain the
    verified value. Empty lists mean no additional revision-specific hold,
    never that the entire entry or reply has been verified.

    Contact changes are traced without invalidating credential facts. Dates
    are traced for the caller's existing date comparison. Changed organization,
    role, supervisor and other substantive fields need corresponding evidence.
    Explicit supplemental ``verified_role``/``verified_supervisor`` fields are
    supported. Clear credential labels can establish role; notes are preserved
    by the caller and are never mined for authority or guessed facts here.
    Request/receipt dates do not decide whether a fact matches a declaration.
    """
    revision = int(entry["revision"])
    prior = [row for row in histories
             if row.get("application_id") == entry.get("application_id")
             and row.get("entry_id") == entry.get("entry_id")
             and int(row["revision"]) < revision]
    result = {"changed_fields": {}, "missing_facts": [], "conflicts": []}
    if not prior:
        return result
    declaration_ref = "declared-history.csv#" + entry["entry_id"]
    reply_ref = "verification-replies.csv#" + reply.get("reply_id", "<unidentified>")
    refs = [declaration_ref, reply_ref]
    fields = set(entry).union(*(set(row) for row in prior))
    for field in sorted(fields):
        if field in {"application_id", "entry_id", "revision"}:
            continue
        different = [row for row in prior if row.get(field) != entry.get(field)]
        if not different:
            continue
        previous = max(different, key=lambda row: int(row["revision"]))
        current = entry.get(field)
        change = {"previous": previous.get(field), "current": current,
                  "previous_revision": int(previous["revision"]), "current_revision": revision,
                  "evidence": []}
        result["changed_fields"][field] = change
        if field.startswith("contact_") or field in {"verification_contact", "from_date", "to_date"}:
            continue
        facts = []
        if field == "role":
            facts = _role_facts(reply)
        elif field in {"supervisor", "supervisor_name"}:
            facts = [(key, reply[key]) for key in ("verified_supervisor", "verified_supervisor_name") if reply.get(key)]
        elif field == "organization":
            if reply.get("verified_organization"):
                facts.append(("verified_organization", reply["verified_organization"]))
            attester = reply.get("attester_organization", "")
            # A transmitting primary office can identify its own institution;
            # an equivalent/CVO's name alone cannot identify the verified one.
            if (_normal(attester) in {_normal(current), _normal(previous.get(field))}
                    and _normal(attester) and _normal(attester) in _normal(reply.get("received_from", ""))):
                facts.append(("attester_organization", attester))
        else:
            key = "verified_" + field
            if reply.get(key) not in (None, ""):
                facts.append((key, reply[key]))
        change["evidence"] = [{"field": key, "value": value, "source_ref": reply_ref} for key, value in facts]
        if not facts:
            result["missing_facts"].append({"field": field, "declared": current,
                "reason": "Retained reply does not establish the revised material fact",
                "source_refs": refs})
        for key, value in facts:
            if _normal(value) != _normal(current):
                result["conflicts"].append({"field": field, "declared": current,
                    "verified": value, "reason": f"Revised declaration differs from reply field {key}",
                    "source_refs": refs})
    return result
