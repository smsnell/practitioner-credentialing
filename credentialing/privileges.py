"""Verify certification facts and map the supplied privilege criteria."""

import calendar
from datetime import date
import re

from .policy import normalized


EQUIVALENTS = {
    'american board of medical specialties certification verification',
    'abms certification verification', 'certifacts',
    'american medical association physician profile', 'ama physician profile',
    'american osteopathic association physician profile', 'aoa physician profile',
    'american board of physician specialties', 'abps',
    'american nurses credentialing center', 'ancc',
    'national commission on certification of physician assistants', 'nccpa',
}
ELIGIBLE_GROUPS = {'PRIV-FM', 'PRIV-IM', 'PRIV-HOSP', 'PRIV-PED'}


def _received(row, app, as_of, before):
    received = row.get('received_date', '')
    return bool(received and received >= app['first_received_date']
                and (received < as_of if before else received <= as_of))


def _issuing_board(row):
    source, board = normalized(row.get('received_from', '')), normalized(row.get('board_name', ''))
    return bool(board and source in {board, 'certifying board ' + board})


def _accepted_source(row):
    source = normalized(row.get('received_from', ''))
    if 'applicant' in source or 'certificate image' in source:
        return False
    for prefix in ('designated equivalent source ', 'designated equivalent '):
        if source.startswith(prefix):
            source = source[len(prefix):]
    return _issuing_board(row) or source in EQUIVALENTS


def _eligibility_end(row):
    """Only issuing-board written candidacy with an explicit end date qualifies."""
    method = normalized(row.get('reply_method', ''))
    if not _issuing_board(row) or not any(term in method for term in ('portal', 'written', 'letter', 'email', 'fax', 'online', 'website')):
        return None
    notes = row.get('notes', '').casefold()
    if not re.search(r'\bcandidate in good standing\b', notes):
        return None
    if re.search(r'\b(?:not|no longer) (?:a )?candidate|not in good standing', notes):
        return None
    match = re.search(r'\b(?:board eligible|eligibility) (?:through|until|ends(?: on)?)\s+(\d{4}-\d{2}-\d{2})', notes)
    if not match:
        return None
    try:
        date.fromisoformat(match[1])
    except ValueError:
        return None
    return match[1]


def _whole_months(start, end):
    """Inclusive full calendar months only; partial months have no office rule."""
    if not start or not end:
        return None
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if last < first or first.day != 1 or last.day != calendar.monthrange(last.year, last.month)[1]:
        return None
    return (last.year - first.year) * 12 + last.month - first.month + 1


def _training_requirements(group):
    text = group['training'].casefold()
    months = re.search(r'(\d+) months', text)
    if not months:
        return [], None
    requirements = re.findall(r'(?:an? accredited) ([a-z ]+?) (residency|fellowship)', text)
    # Multiple residencies joined by "or" are alternatives in the same row.
    return requirements, int(months[1])


def evaluate_privileges(app, tables, as_of, registry, entry_checks, before=False):
    """Preserve all received certification records; support requires verified facts.

    ``entry_checks`` are the evidence evaluator's current-revision checks. Only
    explicitly verified accreditation and accepted replies can establish training.
    Clinical experience requirements travel to leadership and are not applied here.
    """
    result = {'certification_checks': [], 'supported': [], 'unsupported': [], 'issues': []}
    app_id, revision = app['application_id'], int(app['revision'])

    def issue(kind, detail, refs, rule='B20', owner='Medical Services Professional'):
        result['issues'].append({'element': 'certification', 'kind': kind, 'detail': detail,
                                 'owner': owner, 'due': None, 'rule': rule, 'source_refs': refs})

    def current(row):
        return row.get('application_id') == app_id and int(row.get('revision', 0)) == revision

    declarations = [row for row in tables.get('declared-credentials', [])
                    if current(row) and row.get('credential_class') == 'certification']
    accepted = []
    for declaration in declarations:
        declaration_id = declaration['declaration_id']
        rows = [dict(row) for row in tables.get('certification-replies', [])
                if row.get('application_id') == app_id and row.get('declaration_id') == declaration_id]
        check = {'declaration_id': declaration_id, 'declared': dict(declaration),
                 'verification_rows': rows, 'accepted_reply_ids': [], 'failures': []}
        result['certification_checks'].append(check)
        refs = ['declared-credentials.csv#' + declaration_id]
        rejected_issues = []
        for row in rows:
            # Future replies are retained as raw records and confer no knowledge.
            received = row.get('received_date', '')
            if not received or (received >= as_of if before else received > as_of):
                continue
            failures = []
            if not _received(row, app, as_of, before):
                failures.append('Reply predates first application receipt')
            if not _accepted_source(row):
                failures.append('Source is outside the closed accepted-source table or is applicant routed')
            if row.get('board_code') != declaration.get('jurisdiction_or_board'):
                failures.append('Verified board does not match the declared board')
            if normalized(row.get('board_name', '')) != normalized(declaration.get('issuer', '')):
                failures.append('Verified board name does not match the declared issuer')
            if not row.get('certification_status') or not row.get('certificate_specialty'):
                failures.append('Certification status or specialty is missing')
            if failures:
                check['failures'].extend(row['reply_id'] + ': ' + failure for failure in failures)
                issue('outstanding', declaration_id + ': ' + '; '.join(failures),
                      refs + ['certification-replies.csv#' + row['reply_id']], 'B20/B23')
                if not any('does not match' in failure for failure in failures):
                    rejected_issues.append(result['issues'][-1])
            else:
                check['accepted_reply_ids'].append(row['reply_id'])
        usable = [row for row in rows if row['reply_id'] in check['accepted_reply_ids']]
        if usable:
            latest_date = max(row['received_date'] for row in usable)
            latest = [row for row in usable if row['received_date'] == latest_date]
            facts = {(row.get('board_code'), row.get('certificate_specialty'), row.get('certification_status'),
                      row.get('initial_certification_date'), row.get('expiry_date'), row.get('notes')) for row in latest}
            if len(facts) > 1:
                check['failures'].append('Latest same-day certification replies conflict')
                issue('outstanding', declaration_id + ': latest same-day certification replies conflict', refs, 'B20/B40')
            else:
                accepted.extend(latest)
                complete = all(row.get('certification_status') != 'Active' or row.get('initial_certification_date')
                               for row in latest)
                if complete:
                    for retained_issue in rejected_issues:
                        retained_issue['kind'] = 'pending-work'
                        retained_issue['detail'] = ('Retain rejected material; qualifying evidence now establishes '
                                                    + declaration_id + '. Original assessment: ' + retained_issue['detail'])
                        retained_issue['source_refs'].extend('certification-replies.csv#' + row['reply_id'] for row in latest)
                for row in latest:
                    if row.get('certification_status') == 'Active' and not row.get('initial_certification_date'):
                        check['failures'].append(row['reply_id'] + ': initial certification date is unknown')
                        issue('outstanding', declaration_id + ': initial certification date is unknown; active status alone does not establish when certification began',
                              refs + ['certification-replies.csv#' + row['reply_id']], 'B20/B40')
        if not check['accepted_reply_ids']:
            check['failures'].append('No usable certification verification')
            issue('outstanding', declaration_id + ': obtain admissible certification verification', refs)

    verified_entries = []
    for check in entry_checks:
        declared = check.get('declared', {})
        if (not current(declared) or check.get('dates_verified') is not True
                or check.get('unresolved_discrepancy')):
            continue
        for row in check.get('verification_rows', []):
            if row.get('reply_id') in check.get('accepted_reply_ids', []) and _received(row, app, as_of, before):
                verified_entries.append((declared, row, check.get('accreditation_verified') is True))

    degree = any(accredited and declared.get('entry_type') == 'medical-school'
                 and any(term in normalized(row.get('verified_credential', ''))
                         for term in ('doctor of medicine', 'doctor of osteopathic medicine'))
                 and row.get('verified_to') and row['verified_to'] <= as_of
                 for declared, row, accredited in verified_entries)

    def training_matches(specialty, kind, months):
        matches = []
        for declared, row, accredited in verified_entries:
            credential = normalized(row.get('verified_credential', ''))
            # Whole words prevent e.g. child psychiatry satisfying psychiatry.
            expected = normalized(kind + ' ' + specialty)
            if declared.get('entry_type') != kind or credential != expected or not accredited:
                continue
            start, end = row.get('verified_from'), row.get('verified_to')
            if not start or not end or end < start or end > as_of:
                continue
            # CARD names a completed prior IM residency without a separate
            # duration minimum. Do not import PRIV-IM's group requirement.
            duration = _whole_months(start, end) if months is not None else None
            if months is None or duration is not None and duration >= months:
                matches.append(row)
        return matches

    def duration_note(requirements):
        # Q04 applies only to a matching, completed interval that actually
        # needs partial-month arithmetic, never merely to missing accreditation.
        for specialty, kind in requirements:
            for declared, row, _ in verified_entries:
                start, end = row.get('verified_from'), row.get('verified_to')
                if (declared.get('entry_type') == kind
                        and normalized(row.get('verified_credential', '')) == normalized(kind + ' ' + specialty)
                        and start and end and start <= end <= as_of
                        and _whole_months(start, end) is None):
                    return '; partial-month duration remains unresolved (Q04)'
        return ''

    requests = [row for row in tables.get('privilege-requests', []) if current(row)]
    unsupported_details = []
    for request in requests:
        code = request['privilege_code']
        refs = ['privilege-requests.csv#' + request['request_id'], 'C#' + code]
        group = registry['groups'].get(code)
        failures = []
        if not group:
            failures.append('Privilege group is not in the standing criteria')
        elif request.get('criteria_version_cited') != registry['criteria_version'] or as_of < registry['criteria_effective']:
            failures.append('Request does not cite the criteria version in force')
        else:
            if not degree:
                failures.append('Verified MD/DO degree from an accredited school is missing')
            certification = False
            for row in accepted:
                board_matches = any(row['board_code'] == board['code'] and (
                    board['specialty'] is None or normalized(row['certificate_specialty']) == normalized(board['specialty']))
                    for board in group['boards'])
                if not board_matches:
                    continue
                active = (row['certification_status'] == 'Active'
                          and (not row.get('expiry_date') or row['expiry_date'] >= as_of)
                          and bool(row.get('initial_certification_date'))
                          and row['initial_certification_date'] <= as_of)
                eligible_end = _eligibility_end(row)
                eligible = (row['certification_status'] in {'Not certified', 'Board eligible'}
                            and code in ELIGIBLE_GROUPS and eligible_end and eligible_end > as_of)
                if active or eligible:
                    certification = True
            if not certification:
                failures.append('No verified active matching certification or permitted issuing-board eligibility confirmation')
            requirements, months = _training_requirements(group)
            if not requirements:
                failures.append('Training requirement cannot be interpreted from the standing row')
            elif code == 'PRIV-CARD':
                fellowships = training_matches('cardiovascular disease', 'fellowship', months)
                residencies = training_matches('internal medicine', 'residency', None)
                if not any(residency['verified_to'] < fellowship['verified_from']
                           for residency in residencies for fellowship in fellowships):
                    failures.append('Verified accredited cardiovascular fellowship with complete required months and a completed preceding internal medicine residency are required' + duration_note([('cardiovascular disease', 'fellowship')]))
            elif not any(training_matches(specialty, kind, months) for specialty, kind in requirements):
                failures.append('Verified accredited specialty training with complete required months is missing' + duration_note(requirements))
        if failures:
            if code not in result['unsupported']:
                result['unsupported'].append(code)
            unsupported_details.append(code + ': ' + '; '.join(failures))
            missing = [failure for failure in failures if not failure.startswith('No verified active matching certification')]
            if missing:
                issue('outstanding', code + ': ' + '; '.join(missing), refs, 'B20/B40')
        elif code not in result['supported']:
            result['supported'].append(code)

    if not result['supported']:
        issue('eligibility-question', 'No verified evidence supports a requested privilege group; Clinical Director must decide eligibility. ' + '; '.join(unsupported_details),
              ['applications.csv#' + app_id, 'C#rule-6'], 'B21', 'Clinical Director')
    elif result['unsupported']:
        issue('finding', 'Unsupported requested privilege groups: ' + '; '.join(unsupported_details),
              ['applications.csv#' + app_id, 'C#rule-2'], 'B21', 'Clinical Director')
    return result
