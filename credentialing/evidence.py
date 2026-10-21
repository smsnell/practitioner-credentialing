"""Conservative, source-preserving education, experience and peer checks."""

import re
from datetime import date

from .dates import (UnsupportedBoundary, first_received_window, overlaps_window,
                    peer_current, peer_followups, worked_recently)
from .policy import person
from .revisions import assess_revision


EDUCATION = {"medical-school", "residency", "fellowship", "internship"}
EQUIVALENTS = {
    "ecfmg", "educational commission for foreign medical graduates",
    "fcvs", "fsmb fcvs", "federation credentials verification service",
    "ama physician profile", "american medical association physician profile",
    "aoa physician profile", "american osteopathic association physician profile",
    "national student clearinghouse",
}


def _normal(value):
    return " ".join(value.casefold().split())


def _available(row, as_of, before):
    received = row.get("received_date", "")
    return bool(received) and (received < as_of if before else received <= as_of)


def _source_accepted(row, entry, education):
    """Closed source categories; prose notes cannot grant source authority."""
    source = _normal(row.get("received_from", ""))
    role = _normal(row.get("attester_role", ""))
    organization = _normal(row.get("attester_organization", ""))
    employer = _normal(entry.get("organization", ""))
    credential = _normal(row.get("verified_credential", ""))
    material = credential + " " + _normal(row.get("notes", ""))
    if not source or "applicant" in source or any(
        word in material for word in ("photocopy", "certificate image", "diploma copy", "scanned certificate", "copy of the diploma")
    ):
        return False
    # The export identifies transmitting offices separately from individual roles.
    same_org = bool(organization and organization == employer and employer in source)
    if education:
        if source in EQUIVALENTS or organization in EQUIVALENTS and organization in source:
            return True
        if not same_org:
            return False
        if entry["entry_type"] == "medical-school":
            return ("registrar" in source and "registrar" in role) or ("dean" in source and "dean" in role)
        return ("graduate medical education office" in source and any(
            word in role for word in ("programme coordinator", "program coordinator", "director", "gme")
        )) or (any(word in source for word in ("programme director", "program director"))
               and "director" in role)
    if not same_org:
        # CVO authority must name both itself and the represented employer.
        return bool(organization and employer and employer in source and organization in source
                    and "retained" in source and ("cvo" in source or "credentials verification organization" in source))
    return (("medical staff office" in source and "medical staff" in role)
            or ("human resources" in source and ("human resources" in role or "hr" == role))
            or ("authorized" in source and "administrator" in source and "administrator" in role))


def _direct_work(text):
    text = _normal(text)
    if any(term in text for term in ("never worked", "not worked", "have not worked", "did not work", "only know", "membership")):
        return False
    if any(term in text for term in ("worked together", "worked in the same", "work together", "supervised", "directly worked")):
        return True
    return None


def _closure_recorded(attempt):
    """Recognize recorded closure facts, never infer them from silence."""
    if _normal(attempt.get("outcome", "")) in {"institution closed", "school closed", "programme closed", "employer dissolved"}:
        return True
    comment = _normal(attempt.get("comment", ""))
    return bool(re.search(
        r"\b(?:institution|school|programme|program|employer|organization) "
        r"(?:(?:has|is|was) )?(?:permanently )?(?:closed|dissolved)\b", comment))


def _accreditation_fact(text):
    """Recognize explicit facts, never accreditation from credential or source names."""
    text = _normal(text)
    if re.search(r'\b(?:not|never|no longer)\s+(?:currently\s+)?accredited\b|\bunaccredited\b|'
                 r'\baccreditation\s*(?::|is|was)?\s*(?:not|unknown|unverified|pending|revoked|expired)|'
                 r'\b(?:cannot|unable to)\s+(?:confirm|verify)\s+accreditation\b|'
                 r'\bno source establishes accreditation\b', text):
        return False
    for clause in re.split(r'[.;\n]', text):
        if re.search(r'\b(?:not|never|no|cannot|unable|unverified|unknown|pending|revoked|expired|unaccredited|uncertain)\b', clause):
            continue
        if re.search(r'accreditation\s*:\s*(?:currently\s+)?accredited\b|'
                     r'\b(?:school|institution|programme|program|residency|fellowship)\s+is\s+(?:currently\s+)?accredited\b', clause):
            return True
    return False


def _accreditation_denied(text):
    return bool(re.search(r'\b(?:not|never|no longer)\s+(?:currently\s+)?accredited\b|\bunaccredited\b|'
                          r'\baccreditation\s*:\s*(?:revoked|expired)\b', _normal(text)))


def _document_failures(doc, app, as_of, before):
    """Supported labelled evidence must independently bind identity and availability."""
    fields, index = doc.get('fields', {}), doc.get('index', {})
    failures = []
    if fields.get('application') != app['application_id'] or index.get('application_id') != app['application_id']:
        failures.append('Document application identity does not match')
    if fields.get('revision') and fields['revision'] != str(app['revision']):
        failures.append('Document revision does not match')
    if fields.get('applicant'):
        expected = {person(' '.join(app.get(key, '') for key in keys)) for keys in
                    (('first_name', 'middle_name', 'last_name'), ('first_name', 'last_name'))}
        if person(fields['applicant']) not in expected:
            failures.append('Document applicant name does not match')
    if index.get('direction') != 'inbound':
        failures.append('Document is not indexed as received evidence')
    if not doc.get('path') or index.get('document_path') != doc['path']:
        failures.append('Document path is not bound to its correspondence index')
    if index.get('date') != fields.get('received_date'):
        failures.append('Document receipt date conflicts with correspondence index')
    for name, value in (('index date', index.get('date')), ('received date', fields.get('received_date'))):
        try:
            valid = value and date.fromisoformat(value).isoformat() == value
        except ValueError:
            valid = False
        if not valid or value < app['first_received_date'] or (value >= as_of if before else value > as_of):
            failures.append('Document ' + name + ' is outside the verification window or missing')
    return failures


def _accreditation_documents(documents, app, entry, accepted_ids, as_of, before):
    records = []
    for doc in documents:
        fields = doc.get('fields', {})
        if fields.get('entry') != entry['entry_id'] and fields.get('reply') not in accepted_ids:
            continue
        failures = _document_failures(doc, app, as_of, before)
        if fields.get('entry') != entry['entry_id'] or fields.get('reply') not in accepted_ids:
            failures.append('Accreditation supplement is not bound to this entry and an accepted reply')
        source = {key: fields.get(key, '') for key in
                  ('received_from', 'attester_role', 'attester_organization', 'verified_credential')}
        source['notes'] = doc.get('text', '')
        if not _source_accepted(source, entry, True):
            failures.append('Accreditation supplement is not from an accepted official source')
        fact_text = 'Accreditation: ' + fields.get('accreditation', '') + '; ' + doc.get('text', '')
        denied = not failures and _accreditation_denied(fact_text)
        if not _accreditation_fact(fact_text):
            failures.append('Supplement does not state unambiguous accreditation')
        records.append({'path': doc.get('path'), 'accepted': not failures, 'failures': failures, 'denies_accreditation': denied})
    return records


def _peer_return_documents(documents, app, referee, reply, as_of, before):
    records = []
    for doc in documents:
        fields = doc.get('fields', {})
        if fields.get('referee') != referee['referee_id'] and fields.get('reply') != reply['reply_id']:
            continue
        failures = _document_failures(doc, app, as_of, before)
        if fields.get('referee') != referee['referee_id'] or fields.get('reply') != reply['reply_id']:
            failures.append('Return record is not bound to this referee and reply')
        binding_valid = not failures
        if _normal(fields.get('received_from', '')) != _normal(referee['referee_name']):
            failures.append('Return sender is not the named referee')
        if _normal(fields.get('return_method', '')) not in {'secure portal', 'letter', 'fax', 'email'}:
            failures.append('Direct return method is not established')
        returned = fields.get('return_date') or fields.get('received_date')
        if returned != reply['received_date'] or returned > fields.get('received_date', ''):
            failures.append('Return date is not bound to the original reply receipt')
        records.append({'path': doc.get('path'), 'accepted': not failures, 'failures': failures,
                        'applicant_route': binding_valid and 'applicant' in _normal(fields.get('received_from', ''))})
    return records


def evaluate_replies(app: dict, tables: dict, as_of: str, before: bool = False, documents=()) -> dict:
    """Evaluate supplied evidence; do not resolve exceptions or clinical findings.

    ``before`` applies a strict receipt cutoff for historical presentation.
    Raw declaration and reply dictionaries are copied into the result.
    """
    app_id, revision = app["application_id"], int(app["revision"])
    first_received = app["first_received_date"]
    result = {"entry_checks": [], "peer_checks": [], "issues": []}

    def issue(element, kind, detail, rule, refs, due=None, owner="Medical Services Professional"):
        result["issues"].append({"element": element, "kind": kind, "detail": detail,
                                 "owner": owner, "due": due, "rule": rule, "source_refs": refs})

    histories = [row for row in tables.get("declared-history", []) if row["application_id"] == app_id]
    current = [row for row in histories if int(row["revision"]) == revision]
    try:
        window = first_received_window(first_received)
    except UnsupportedBoundary as exc:
        window = None
        issue("experience", "outstanding", str(exc), "B14/Q10", ["applications.csv#" + app_id])
    for entry in current:
        education = entry["entry_type"] in EDUCATION
        element = "education" if education else "experience"
        entry_id = entry["entry_id"]
        refs = ["declared-history.csv#" + entry_id]
        in_scope = education or window is None or overlaps_window(
            entry["from_date"], entry.get("to_date") or None, window, as_of)
        rows = [dict(row) for row in tables.get("verification-replies", [])
                if row["application_id"] == app_id and row["entry_id"] == entry_id]
        in_scope = in_scope or any(_available(row, as_of, before) and (
            row.get("outcome") == "confirmed-with-discrepancy"
            or row.get("verified_from", "") != entry.get("from_date", "")
            or row.get("verified_to", "") != entry.get("to_date", "")) for row in rows)
        check = {"entry_id": entry_id, "accepted_reply_ids": [], "failures": [],
                 "declared": dict(entry), "verification_rows": rows, "in_scope": in_scope,
                 "dates_verified": False, "accreditation_verified": False if education else None,
                 "revision_mapping": None, "unresolved_discrepancy": False,
                 "secondary_route_candidate": False, "accreditation_source_refs": [],
                 "accreditation_evidence": []}
        attempts = [row for row in tables.get("verification-attempts", [])
                    if row.get("application_id") == app_id and row.get("subject_ref") == entry_id
                    and row.get("attempt_date") and (row["attempt_date"] < as_of if before else row["attempt_date"] <= as_of)]
        check["verification_attempts"] = [dict(row) for row in attempts]
        result["entry_checks"].append(check)
        if not in_scope:
            continue
        check['revision_mapping'] = {}
        for row in rows:
            if not _available(row, as_of, before):
                continue
            failures = []
            if row["received_date"] < first_received:
                failures.append("Reply predates first application receipt")
            mapping = assess_revision(entry, histories, row)
            if mapping['changed_fields']:
                check['revision_mapping'][row['reply_id']] = mapping
            if mapping['missing_facts']:
                failures.append('Reconcile revised facts not established by this retained reply: ' + ', '.join(x['field'] for x in mapping['missing_facts']))
            if mapping['conflicts']:
                check['unresolved_discrepancy'] = True
                failures.append('Revised material facts conflict with retained verification; preserve both for reconciliation')
                issue(element, 'discrepancy', f"{entry_id}: revised facts differ in {row['reply_id']}: {mapping['conflicts']}", 'B04/B05/B23', refs + ['verification-replies.csv#' + row['reply_id']])
            if not _source_accepted(row, entry, education):
                failures.append("Source is not an accepted direct source; MSP must assess any documented impossibility exception")
            if row.get("outcome") not in {"confirmed", "confirmed-with-discrepancy"}:
                failures.append("Reply does not confirm the entry")
            source_refs = refs + ["verification-replies.csv#" + row["reply_id"]]
            conflicts = {key: {"declared": entry.get(declared, ""), "verified": row.get(key, "")}
                         for key, declared in (("verified_from", "from_date"), ("verified_to", "to_date"))
                         if row.get(key, "") != entry.get(declared, "")}
            if conflicts or row.get("outcome") == "confirmed-with-discrepancy":
                check["unresolved_discrepancy"] = True
                failures.append("Verified dates/outcome conflict with declaration; retain both and obtain written reconciliation")
                issue(element, "discrepancy", f"{entry_id}: conflicting verification {row['reply_id']}: {conflicts}; {row.get('notes', '')}", "B04/B05", source_refs)
            check["failures"].extend(f"{row['reply_id']}: {failure}" for failure in failures)
            if failures:
                issue(element, "outstanding", f"{entry_id}: {'; '.join(failures)}", "B06/B07/B23", source_refs)
            else:
                check["accepted_reply_ids"].append(row["reply_id"])
                check["dates_verified"] = True
        if check["unresolved_discrepancy"]:
            check["dates_verified"] = False
        if not check["accepted_reply_ids"]:
            check["failures"].append("No usable verification reply")
            if any(_closure_recorded(attempt) for attempt in attempts):
                check["secondary_route_candidate"] = True
                issue(element, "outstanding", f"{entry_id}: recorded closure requires MSP assessment of documented impossibility and the possible most-recent-affiliation secondary route. Preserve the attempts; a single equivalent's no-record response does not establish that no equivalent holds the record. Obtain the required written verification account and exception determination before acceptance.",
                      "B07", refs + ["verification-attempts.csv#" + row["attempt_id"] for row in attempts])
            else:
                issue(element, "outstanding", f"{entry_id}: obtain admissible verification", "B17" if education else "B14", refs)
        if education:
            check['accreditation_source_refs'] = ['verification-replies.csv#' + row['reply_id']
                for row in rows if row['reply_id'] in check['accepted_reply_ids'] and _accreditation_fact(row.get('notes', ''))]
            check['accreditation_evidence'] = _accreditation_documents(
                documents, app, entry, check['accepted_reply_ids'], as_of, before)
            check['accreditation_source_refs'].extend(record['path'] for record in check['accreditation_evidence'] if record['accepted'])
            denials = ['verification-replies.csv#' + row['reply_id'] for row in rows
                       if row['reply_id'] in check['accepted_reply_ids'] and _accreditation_denied(row.get('notes', ''))]
            denials.extend(record['path'] for record in check['accreditation_evidence'] if record['denies_accreditation'])
            check['accreditation_verified'] = bool(check['accreditation_source_refs']) and not denials
            if denials:
                issue(element, 'discrepancy', f'{entry_id}: source reports absent/ceased accreditation; preserve and reconcile the evidence', 'B05/B40', refs + denials + check['accreditation_source_refs'])
            if not check['accreditation_verified']:
                check["failures"].append("Required accreditation evidence is not established")
                issue(element, "outstanding", f"{entry_id}: required accreditation evidence missing; a dates/credential reply does not establish accreditation", "B17/B40", refs)
        received_rows = [row for row in rows if _available(row, as_of, before)]
        refused = any(row.get("outcome", "").casefold() in {"refused", "refusal", "no response", "nonresponse"} for row in received_rows)
        if not education and not check["accepted_reply_ids"] and len(attempts) >= 3 and (not received_rows or refused):
            issue(element, "finding", f"{entry_id}: affiliation refusal/nonresponse after at least three attempts; preserve attempts and refer for review", "B08", refs + ["verification-attempts.csv#" + row["attempt_id"] for row in attempts])

    referees = [row for row in tables.get("peer-referees", [])
                if row["application_id"] == app_id and int(row["revision"]) == revision]
    for referee in referees:
        referee_id = referee["referee_id"]
        refs = ["peer-referees.csv#" + referee_id]
        replies = [row for row in tables.get("peer-reference-replies", [])
                   if row["application_id"] == app_id and row["referee_id"] == referee_id and _available(row, as_of, before)]
        if not replies:
            check = {"referee_id": referee_id, "reply_id": None, "eligible": None,
                     "provenance_verified": False, "usable": False, "failures": ["No peer reply received"], "reply": None}
            result["peer_checks"].append(check)
            requested = referee.get("first_request_date")
            due = None
            detail = f"{referee_id}: peer reply remains outstanding"
            if requested and requested <= as_of:
                followups = peer_followups(requested)
                check["followup_dates"] = followups
                attempts = sorted([row for row in tables.get("verification-attempts", [])
                    if row.get("application_id") == app_id and row.get("subject_ref") == referee_id
                    and row.get("attempt_date") and row["attempt_date"] > requested
                    and (row["attempt_date"] < as_of if before else row["attempt_date"] <= as_of)],
                    key=lambda row: (row["attempt_date"], row.get("attempt_id", "")))
                fulfilled = []
                for attempt in attempts:
                    if len(fulfilled) < 2 and attempt["attempt_date"] >= followups[len(fulfilled)]:
                        fulfilled.append({"due": followups[len(fulfilled)],
                                          "attempt_id": attempt["attempt_id"],
                                          "attempt_date": attempt["attempt_date"]})
                check["recorded_followups"] = fulfilled
                due = followups[len(fulfilled)] if len(fulfilled) < 2 else None
                if due:
                    detail += "; send the next unrecorded reminder"
                if as_of >= followups[-1]:
                    issue("references", "outstanding", f"{referee_id}: notify applicant and request an additional referee; original request remains open",
                          "B09", refs, followups[-1])
            issue("references", "outstanding", detail, "B09/B10", refs, due)
            continue
        for row in replies:
            failures, eligibility = [], True
            unknown = False
            if row["received_date"] < first_received:
                failures.append("Reply predates first application receipt")
                eligibility = False
            if not row.get("signature_date"):
                unknown = True
                failures.append("Missing signature date")
            else:
                try:
                    if not peer_current(row["signature_date"], as_of):
                        eligibility = False
                        failures.append("Signature is not current on presentation date")
                    if row["signature_date"] > row["received_date"]:
                        eligibility = False
                        failures.append("Signature is after receipt")
                    if not worked_recently(row.get("last_worked_together_end"), row["signature_date"]):
                        eligibility = False
                        failures.append("Last direct work is outside two years at signature or is future dated")
                except UnsupportedBoundary as exc:
                    unknown = True
                    failures.append(str(exc))
            related = row.get("related_or_partner", "")
            if related != "No":
                eligibility = False if related == "Yes" else eligibility
                unknown |= related not in {"Yes", "No"}
                failures.append("Related/spouse/partner status does not establish eligibility")
            if not row.get("referee_specialty_stated"):
                unknown = True
                failures.append("Missing stated discipline")
            elif _normal(row["referee_specialty_stated"]) != _normal(app["discipline"]):
                eligibility = False
                failures.append("Referee is not in the applicant's declared discipline")
            direct = _direct_work(row.get("relationship_stated", ""))
            if direct is not True:
                eligibility = False if direct is False else eligibility
                unknown |= direct is None
                failures.append("Direct work together is not established")
            eligible = False if not eligibility else None if unknown else True
            provenance = _peer_return_documents(documents, app, referee, row, as_of, before)
            provenance_refs = [record['path'] for record in provenance if record['accepted']]
            route_conflicts = [record['path'] for record in provenance if record['applicant_route']]
            provenance_verified = bool(provenance_refs) and not route_conflicts
            if route_conflicts:
                failures.append('Recorded applicant return route requires reconciliation; direct route is not established')
            elif not provenance_refs:
                failures.append("Direct referee-return provenance is not supplied")
            source_refs = refs + ["peer-reference-replies.csv#" + row["reply_id"]]
            result["peer_checks"].append({"referee_id": referee_id, "reply_id": row["reply_id"],
                "eligible": eligible, "provenance_verified": provenance_verified, "usable": eligible is True and provenance_verified,
                "provenance_source_refs": provenance_refs, "provenance_evidence": provenance,
                "failures": failures, "reply": dict(row)})
            if failures:
                issue("references", "outstanding", f"{referee_id}/{row['reply_id']}: {'; '.join(failures)}", "B18/B19/B38/B40", source_refs + provenance_refs)
    usable_referees = {row["referee_id"] for row in result["peer_checks"] if row['usable']}
    if len(usable_referees) < 2:
        issue("references", "outstanding", "At least two eligible current same-discipline peers with verified direct-return provenance are required", "B18/B19/B38", ["applications.csv#" + app_id])
    return result
