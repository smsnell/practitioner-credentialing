"""Office rules evaluated from one closed export; no external writes or judgments.

Rich working results retain unknowns. Pre-dispatch holds use the owner-approved
Q07 semantic exception recorded in deliverables/rules.md; no notice is inferred.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import re

from .dates import uncovered_intervals, request_deadline, appointment_cycle_end, UnsupportedBoundary
from .documents import indexed_documents, for_application, document_conflicts, period, intake_notice
from .policy import registry, normalized, person
from .intake_evidence import evaluate_intake_documents
from .revisions import referees_for_revision
from .dispositions import clinical_dispositions

ELEMENTS = ('licensure', 'experience', 'gaps', 'education', 'certification', 'references')


def issue(element, kind, detail, rule, refs=(), owner='Medical Services Professional', due=None):
    return {'element': element, 'kind': kind, 'detail': detail, 'owner': owner,
            'due': due, 'rule': rule, 'source_refs': list(refs)}


def row_ref(table, row):
    for key in ('reply_id', 'entry_id', 'declaration_id', 'attempt_id', 'referee_id', 'request_id'):
        if key in row:
            return f'{table}.csv#{row[key]}'
    return f'{table}.csv#{row.get("application_id", "")}/revision-{row.get("revision", "")}'


def revision_rows(tables, table, app):
    return [r for r in tables[table] if r.get('application_id') == app['application_id']
            and r.get('revision') == app['revision']]


def before_cutoff(value, as_of, before=False):
    return bool(value) and (value < as_of if before else value <= as_of)


def licensed(app, tables, docs, as_of):
    issues, checks = [], []
    name = tuple(normalized(app[k]) for k in ('last_name', 'first_name', 'middle_name', 'birth_year'))
    matching = [r for r in tables['licence-lookup-wa']
                if tuple(normalized(r[k]) for k in ('lastname', 'firstname', 'middlename', 'birthyear')) == name
                and r['lookup_date'] <= as_of]
    observations = sorted(matching, key=lambda r: r['lookup_date'])
    wa = observations[-1] if observations else None
    declarations = [r for r in revision_rows(tables, 'declared-credentials', app)
                    if r['credential_class'] == 'licence']
    if not wa:
        issues.append(issue('licensure', 'outstanding', 'No Washington licence observation establishes the required current WA credential; an NPI is not a licence.', 'B11', [row_ref('applications', app)]))
    else:
        ref = f"licence-lookup-wa.csv#{wa['credentialnumber']}@{wa['lookup_date']}"
        reasons = []
        if wa['status'].casefold() != 'active':
            reasons.append('WA licence is not active')
        if not wa['expirationdate'] or wa['expirationdate'] < as_of:
            reasons.append('WA licence is expired or expiry is unknown')
        if not wa['firstissuedate'] or wa['firstissuedate'] > as_of:
            reasons.append('WA licence was not yet issued or issue date is unknown')
        if not any(normalized(r['number_declared']) == normalized(wa['credentialnumber']) and r['jurisdiction_or_board'] == 'WA' for r in declarations):
            issues.append(issue('licensure', 'discrepancy', 'Washington credential is not declared on this revision; applicant must reconcile and submit a numbered revision if changing declarations.', 'B04', [ref]))
        action = wa['actiontaken'].casefold()
        action_docs = [d for d in docs if wa['credentialnumber'] in d['text'] and
                       'board action' in d['title'].casefold() and
                       'washington state department of health' in d['fields'].get('from', '').casefold()]
        restricted = False
        if action in {'yes', 'pending'}:
            if not action_docs:
                issues.append(issue('licensure', 'outstanding', 'Obtain issuing-board action details; actiontaken alone does not describe the action.', 'B37', [ref]))
            else:
                for d in action_docs:
                    if re.search(r'supervision|monitoring|probation|stipulated|surrender|limitation', d['text'], re.I):
                        restricted = True
                        issues.append(issue('licensure', 'finding', 'Preserve issuing-board restriction/monitoring finding and obtain Clinical Director disposition; it remains in the leadership packet.', 'B12', [ref, d['path']], 'Clinical Director'))
                ppq = next((r for r in revision_rows(tables, 'application-disclosures', app) if r['question_code'] == 'PPQ-1'), None)
                if ppq and ppq['answer'].casefold() == 'no':
                    issues.append(issue('licensure', 'discrepancy', 'Board action contradicts the No disclosure in PPQ-1; preserve both and obtain applicant written resolution/new numbered revision.', 'B22', [ref, row_ref('application-disclosures', ppq)], 'Applicant'))
        for reason in reasons:
            issues.append(issue('licensure', 'outstanding', reason, 'B11', [ref]))
        checks.append({'jurisdiction': 'WA', 'observations': observations, 'selected': wa,
                       'active_and_current': not reasons, 'unrestricted': False if restricted else (True if action == 'no' else None),
                       'action_documents': [d['path'] for d in action_docs], 'failures': reasons})
    for dec in declarations:
        if dec['jurisdiction_or_board'] == 'WA':
            continue
        found = [r for r in tables['licence-lookup-other-states']
                 if r['board_state'] == dec['jurisdiction_or_board'] and
                 normalized(r['licence_number']) == normalized(dec['number_declared']) and r['lookup_date'] <= as_of]
        found.sort(key=lambda r: r['lookup_date'])
        record = found[-1] if found else None
        failures = []
        if not record:
            failures.append('No issuing-board verification for declared licence')
        elif 'board' not in record['verified_by'].casefold() and 'physician data center' not in record['verified_by'].casefold():
            failures.append('Source is not an accepted licensure authority')
        elif person(record['licensee_name']) not in {person(' '.join([app['last_name'], app['first_name'], app['middle_name']])), person(' '.join([app['last_name'], app['first_name']]))}:
            failures.append('Licence holder identity differs from declaration')
        if record and record['disciplinary_action'].casefold() not in {'none reported', 'none', 'no'}:
            issues.append(issue('licensure', 'finding', 'Preserve other-state board action: ' + record['disciplinary_action'], 'B12', [row_ref('declared-credentials', dec)], 'Clinical Director'))
        for failure in failures:
            issues.append(issue('licensure', 'outstanding', failure, 'B11', [row_ref('declared-credentials', dec)]))
        checks.append({'declaration': dec, 'observations': found, 'selected': record, 'failures': failures})
    return {'issues': issues, 'checks': checks, 'wa': wa}


def gaps_for(app, tables, docs, as_of, entry_checks, dispositions=()):
    history = revision_rows(tables, 'declared-history', app)
    schools = [r for r in history if r['entry_type'] == 'medical-school' and r['to_date']]
    issues, gaps = [], []
    if len(schools) != 1:
        issues.append(issue('gaps', 'outstanding', 'Exactly one dated professional-school completion anchor is required for gap calculation.', 'B15', [row_ref('applications', app)]))
        return {'gaps': gaps, 'issues': issues, 'basis': 'unavailable'}
    intervals = [(r['from_date'], r['to_date'] or None) for r in history if r['entry_type'] != 'medical-school']
    gaps = uncovered_intervals(schools[0]['to_date'], intervals, as_of)
    contested = [x for x in entry_checks if any('discrep' in str(f).casefold() or 'date' in str(f).casefold() for f in x.get('failures', []))]
    basis = 'declared timeline; provisional where source dates conflict' if contested else 'declared inclusive timeline'
    explanations = [(d, period(d)) for d in docs if period(d) and not document_conflicts(d, app)]
    for gap in gaps:
        explanation = [d for d, span in explanations if span[0] <= gap['start'] and span[1] >= gap['end']]
        gap['explanation_sources'] = [d['path'] for d in explanation]
        matching_dispositions = [d for d in dispositions if d['gap_period'] == (gap['start'], gap['end'])]
        gap['clinical_disposition_sources'] = [d['path'] for d in matching_dispositions if d['authorized']]
        gap['basis'] = basis
        label = f"Gap {gap['start']} through {gap['end']} ({gap['days']} inclusive days)"
        if not explanation:
            issues.append(issue('gaps', 'return-incomplete', label + ' lacks a written explanation covering the entire interval; queue incomplete return/request, not a fictional sent event.', 'B16', [row_ref('declared-history', schools[0])], 'Applicant'))
        if gap['days'] >= 180 and not any(d['gap_cleared'] for d in matching_dispositions):
            issues.append(issue('gaps', 'routed-to-clinical-director', label + ' requires a recorded Clinical Director disposition; explanation alone does not resolve it.', 'B16', gap['explanation_sources'], 'Clinical Director'))
    if contested:
        issues.append(issue('gaps', 'outstanding', 'Declared gap arithmetic is provisional pending entry reconciliation; it is not an authoritative corrected timeline.', 'B05', [x.get('entry_id', '') for x in contested]))
    return {'gaps': gaps, 'issues': issues, 'basis': basis}


def intake(app, tables, docs, as_of, reg, gap_result, entry_checks=None):
    missing, issues, notices = [], [], []
    entries = revision_rows(tables, 'declared-history', app)
    supplied = evaluate_intake_documents(app, docs, entries, entry_checks, as_of)
    if not supplied['signature']['established']:
        missing.append('application signature and date evidence')
    if not app['release_signed_date'] or app['release_signed_date'] > as_of:
        missing.append('signed and dated Larkhollow release')
    if not app['cv_received_date'] or app['cv_received_date'] > app['received_date']:
        missing.append('CV present at submission')
    requests = revision_rows(tables, 'privilege-requests', app)
    if not requests or not any(r['privilege_code'] in reg['groups'] for r in requests):
        missing.append('at least one published privilege requested')
    declarations = revision_rows(tables, 'declared-credentials', app)
    if not declarations:
        missing.append('declared held credentials')
    refs = referees_for_revision(app, tables, as_of)
    if len({r['referee_id'] for r in refs if r['referee_name']}) < 2:
        missing.append('two named referees')
    disclosures = revision_rows(tables, 'application-disclosures', app)
    for code in [f'PPQ-{n}' for n in range(1, 9)]:
        row = next((r for r in disclosures if r['question_code'] == code), None)
        if not row or row['answer'] not in {'Yes', 'No'}:
            missing.append('answer to ' + code)
        elif row['answer'] == 'Yes':
            if not row['applicant_comment']:
                missing.append('explanation for ' + code)
            issues.append(issue('intake', 'finding', 'High-risk Yes disclosure ' + code + ' requires recorded Clinical Director review and inclusion in leadership packet.', 'B22', [row_ref('application-disclosures', row)], 'Clinical Director'))
    if not entries:
        missing.append('declared history')
    for entry in entries:
        if entry['entry_type'] in {'employment', 'affiliation'} and not any(
                str(entry.get(key, '')).strip() for key in ('contact_name', 'contact_email', 'contact_phone', 'contact_address')):
            missing.append('contact for ' + entry['entry_id'])
    if any(not g['explanation_sources'] for g in gap_result['gaps']):
        missing.append('written explanation for every gap of at least 30 days')
    for doc in docs:
        notice = intake_notice(doc, app)
        if notice:
            gap_item = 'written explanation for every gap of at least 30 days'
            if gap_item in notice['requested_items'] and any(
                    not g['explanation_sources'] and g['start'] + ' to ' + g['end'] not in notice['body']
                    for g in gap_result['gaps']):
                # A letter naming one period cannot start a clock for other gaps.
                notice['requested_items'].remove(gap_item)
                notice['request_coverage_known'] = False
            computed = request_deadline(notice['date'])
            if notice['due_in_source'] and notice['due_in_source'] != computed:
                issues.append(issue('intake', 'discrepancy', 'Recorded deadline differs from request date +30; preserve both rather than selecting one.', 'B03', [doc['path']]))
            notice['due'] = notice['due_in_source'] or computed
            notices.append(notice)
    unrequested = []
    coverage_unknown = any(not n['request_coverage_known'] for n in notices)
    for item in missing:
        covering = [n for n in notices if item in n['requested_items']]
        if covering:
            # Preserve the original clock, including on partial/revised replies.
            first = min(covering, key=lambda n: n['date'])
            requested_item = 'current curriculum vitae' if item == 'CV present at submission' else item
            issues.append(issue('intake', 'outstanding', 'Await ' + requested_item + '; already requested in ' + first['path'] + '; original response deadline retained.', 'B03', [first['path']], 'Applicant', first['due']))
        else:
            unrequested.append(item)
    if not supplied['cv']['resolved']:
        issues.append(issue('reconciliation', 'outstanding', 'Obtain actual CV and reconcile CV, application and verification evidence; cv_received_date alone does not establish reconciliation.', 'B05', [row_ref('applications', app)] + supplied['cv']['source_refs']))
    for conflict in supplied['cv']['conflicts']:
        issues.append(issue('reconciliation', 'discrepancy', 'CV comparison requires written reconciliation: ' + str(conflict), 'B05', conflict['source_refs'], 'Applicant'))
    if unrequested:
        if coverage_unknown:
            detail = 'Review recorded notice coverage before dispatching any additional request for: ' + '; '.join(unrequested) + '; no additional dispatch or deadline inferred.'
        else:
            detail = 'Pending MSP dispatch of a written request for: ' + '; '.join(unrequested) + '; no response clock has started for these items.'
        issues.append(issue('intake', 'outstanding', detail, 'B44', [row_ref('applications', app)] + [n['path'] for n in notices]))
    if not app['release_signed_date'] or app['release_signed_date'] > as_of:
        issues.append(issue('intake', 'outstanding', 'Verification requests remain blocked until the signed release is received.', 'B01', [row_ref('applications', app)]))
    return {'missing': missing, 'issues': issues, 'notices': notices, 'document_evidence': supplied, 'referee_addresses': 'not assessable under export exception', 'release_present': bool(app['release_signed_date'] and app['release_signed_date'] <= as_of)}


def element_states(issues):
    states = {}
    for element in ELEMENTS:
        kinds = {i['kind'] for i in issues if i['element'] == element}
        # Multiple unresolved facts have no universal precedence; preserve all
        # internally. Only the explicit E4 mixed finding/discrepancy rule projects.
        if not kinds:
            states[element] = 'resolved'
        elif 'outstanding' in kinds or ('discrepancy' in kinds and 'finding' in kinds):
            states[element] = 'outstanding'
        elif len(kinds) > 1:
            states[element] = 'outstanding'
        else:
            states[element] = next(iter(kinds))
    return states


def presentable(issues):
    # A partial certification finding is routed with the packet immediately.
    # Other unresolved work (including absent CD dispositions) still blocks.
    return all(item['kind'] == 'finding' and (item['element'] == 'certification'
               or item.get('clinical_disposition_sources')) for item in issues)


def decision_conditions(doc):
    """Read explicit dated conditions, preserving source wording and due dates."""
    section = False
    conditions, failures = [], []
    for line in doc['text'].splitlines():
        if re.match(r'^\*\*Conditions:\*\*\s*$', line):
            section = True
            continue
        if line.startswith('## '):
            section = 'condition' in line.casefold()
            continue
        if section and re.match(r'^[-*] ', line.strip()):
            text = line.strip()[2:].strip()
            # A recorded due date takes precedence over another date in the
            # same condition (for example, the underlying licence expiry).
            dates = re.findall(r'\bdue\s+(\d{4}-\d{2}-\d{2})\b', text, re.IGNORECASE)
            if not dates:
                dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', text)
            if len(dates) != 1:
                failures.append('Condition lacks one unambiguous recorded due date: ' + text)
            else:
                conditions.append({'condition': text, 'due': dates[0]})
    if doc['fields'].get('outcome') == 'approved-with-conditions' and not conditions:
        failures.append('Conditional approval lacks parseable explicitly dated conditions; retain record for MSP review')
    return conditions, failures


def correspondence_conflicts(app, tables, docs):
    """Retain concrete conflicts in revision prose and indexed correspondence."""
    conflicts = []
    entries = revision_rows(tables, 'declared-history', app)
    claimed = re.search(r'\b(\d{4}) to (\d{4}) appointment\b', app.get('revision_reason', ''))
    if claimed:
        for entry in entries:
            prior = [r for r in tables['declared-history'] if r['application_id'] == app['application_id']
                     and r['entry_id'] == entry['entry_id'] and int(r['revision']) < int(app['revision'])]
            if prior and max(prior, key=lambda r: int(r['revision']))['organization'] != entry['organization']:
                if (entry['from_date'][:4], entry['to_date'][:4]) != claimed.groups():
                    conflicts.append(issue('reconciliation', 'discrepancy',
                        f"Revision prose names {claimed[1]}–{claimed[2]}, but changed {entry['entry_id']} covers {entry['from_date']} through {entry['to_date'] or 'current'}; reconcile intended entry without transferring verification.",
                        'B39/B43', [row_ref('applications', app), row_ref('declared-history', entry)], 'Applicant'))
    for doc in docs:
        span = period(doc)
        employer = re.search(r'started at (.+?) (?:at the|in |on )', doc['text'], re.I)
        if span and employer:
            following = sorted([e for e in entries if e['entry_type'] in {'employment', 'affiliation'}
                                and e['from_date'] > span[1]], key=lambda e: e['from_date'])
            if following and normalized(employer[1]) != normalized(following[0]['organization']):
                conflicts.append(issue('reconciliation', 'discrepancy',
                    f"Gap explanation names {employer[1]}, but {following[0]['entry_id']} declares {following[0]['organization']}; preserve both for applicant reconciliation.",
                    'B39/B43', [doc['path'], row_ref('declared-history', following[0])], 'Applicant'))
        issued = re.search(r'initially issued (\d{4}-\d{2}-\d{2})', doc['text'])
        if issued and 'certification' in doc['title'].casefold():
            for reply in tables['certification-replies']:
                if (reply['application_id'] == app['application_id'] and reply['received_date'] <= doc['index']['date']
                        and reply.get('board_name', '') in doc['text'] and reply.get('initial_certification_date')
                        and reply['initial_certification_date'] != issued[1]):
                    conflicts.append(issue('reconciliation', 'discrepancy',
                        f"Correspondence gives initial certification date {issued[1]}, but {reply['reply_id']} records {reply['initial_certification_date']}; retain both and ask MSP to reconcile.",
                        'B39', [doc['path'], row_ref('certification-replies', reply)]))
    return conflicts


def assess(app, tables, documents, as_of, reg, before=False):
    from .evidence import evaluate_replies
    from .privileges import evaluate_privileges
    # The previous day is used only for receipt/revision/doc cutoff; lookups keep
    # their explicit decision-day exception in licensed().
    receipt_cutoff = (date.fromisoformat(as_of) - timedelta(days=1)).isoformat() if before else as_of
    docs = for_application(documents, app['application_id'], as_of, before)
    dispositions = clinical_dispositions(app, docs, reg)
    evidence = evaluate_replies(app, tables, as_of, before, documents=docs)
    licence = licensed(app, tables, docs, as_of)
    gaps = gaps_for(app, tables, docs, receipt_cutoff, evidence['entry_checks'], dispositions)
    intake_result = intake(app, tables, docs, receipt_cutoff, reg, gaps, evidence['entry_checks'])
    privileges = evaluate_privileges(app, tables, as_of, reg, evidence['entry_checks'], before)
    issues = evidence['issues'] + licence['issues'] + gaps['issues'] + intake_result['issues'] + privileges['issues']
    issues.extend(correspondence_conflicts(app, tables, docs))
    for disposition in dispositions:
        for reason in disposition['reasons'] + disposition['evidence_reasons']:
            issues.append(issue('reconciliation', 'outstanding', reason, 'B16/B39/B40', [disposition['path']]))
        if not disposition['authorized']:
            continue
        for item in issues:
            if (item['kind'] == 'finding' and item['element'] == 'intake'
                    and any(code in item['detail'] for code in disposition['ppq_codes'])):
                item['clinical_disposition_sources'] = [disposition['path']]
                item['source_refs'].append(disposition['path'])
                item['detail'] = 'Retain high-risk finding and recorded Clinical Director disposition in leadership packet: ' + item['detail'].split(' requires recorded Clinical Director review')[0]
                item['owner'] = 'Medical Services Professional'
        if disposition['amendment_offered'] and app['received_date'] <= disposition['date']:
            for item in issues:
                if item['kind'] == 'eligibility-question':
                    item['detail'] = 'Recorded Clinical Director disposition offers amendment of the privilege request; await applicant choice. Underlying eligibility evidence remains outstanding.'
                    item['owner'] = 'Applicant'
                    item['source_refs'].append(disposition['path'])
    for doc in docs:
        for conflict in document_conflicts(doc, app):
            issues.append(issue('reconciliation', 'discrepancy', conflict, 'B39', [doc['path']], 'Applicant'))
    attempts = [r for r in tables['verification-attempts'] if r['application_id'] == app['application_id'] and r['attempt_date'] <= receipt_cutoff]
    for entry in evidence['entry_checks']:
        matching = [r for r in attempts if r['subject_ref'] == entry['entry_id']]
        if entry.get('in_scope') and not entry.get('accepted_reply_ids') and len(matching) >= 3:
            is_employment = entry.get('declared', {}).get('entry_type') in {'employment', 'affiliation', 'teaching'}
            issues.append(issue('experience' if is_employment else 'education', 'outstanding', f"{entry['entry_id']}: {len(matching)} recorded attempts without admissible resolution; continue requests, nonresponse is not impossibility." + (' Preserve the nonresponse red flag for leadership.' if is_employment else ''), 'B08', [row_ref('verification-attempts', r) for r in matching]))
    actions, seen = [], set()
    for item in issues:
        detail, due = item['detail'], item['due']
        if (not intake_result['release_present'] and item['element'] in ELEMENTS
                and item['owner'] == 'Medical Services Professional'
                and any(term in detail.casefold() for term in ('request', 'follow', 'obtain admissible verification', 'obtain admissible certification verification'))):
            detail = 'Hold verification outreach until signed release; ' + detail
            due = None
        key = (detail, item['owner'], due)
        if key not in seen:
            actions.append({'item': detail, 'owner': item['owner'], 'due': due})
            seen.add(key)
    return {'application': app, 'as_of': as_of, 'historical_before_decision': before,
            'elements': element_states(issues), 'packet_presentable': presentable(issues),
            'intake': intake_result, 'entry_checks': evidence['entry_checks'], 'peer_checks': evidence['peer_checks'],
            'licensure': licence, 'gaps': gaps, 'privileges': privileges, 'issues': issues,
            'clinical_dispositions': dispositions,
            'attempts': attempts, 'action_queue': actions, 'document_paths': [d['path'] for d in docs]}


def check_decision(doc, app, assessed, reg, prior):
    f = doc['fields']
    failures = []
    body, outcome, when = f.get('body', ''), f.get('outcome', ''), f.get('decision_date', '')
    if outcome not in reg['bodies'].get(body, []):
        failures.append('1 body/outcome authority: body is not authorized for the recorded outcome')
    roles = [r for r in reg['roles'] if person(r['name']) == person(f.get('signatory', '')) and normalized(r['role']) == normalized(f.get('role', ''))]
    authorized = any((not r['start'] or r['start'] <= when <= r['end']) and body in r['role'] for r in roles)
    if any(r['role'] == 'Vice-Chair, Governing Body' for r in roles) and when < reg['designation_date']:
        authorized = False  # Designation boundary explicitly unresolved in A/Q10.
    signed = next((line for line in doc['text'].splitlines() if line.startswith('Signed:')), '')
    if not authorized or not signed or person(f.get('signatory', '')) not in person(signed) or when not in signed:
        failures.append('2 signatory authority: role, term, designation or signed record not established by roster/evidence')
    if f.get('application') != app['application_id'] or f.get('revision') != app['revision']:
        failures.append('3 applicant/revision: decision does not match the applicable numbered revision')
    if not assessed['packet_presentable'] or app['received_date'] >= when:
        failures.append('4 prior presentability: required evidence/work was not resolved before this decision for its exact revision')
    if outcome not in {'recommended', 'approved'} and not f.get('reason'):
        failures.append('5 outcome/reason: this outcome requires a recorded reason')
    codes = [x.strip() for x in f.get('privileges', '').split(';') if x.strip()]
    if outcome in {'recommended', 'approved', 'approved-with-conditions'} and (not codes or any(x not in reg['groups'] for x in codes)):
        failures.append('5 outcome/reason: privilege codes absent or not published in the criteria')
    if f.get('criteria_version') != reg['criteria_version'] or when < reg['criteria_effective']:
        failures.append('6 criteria version: the recorded version is not established in force on decision date')
    if body == 'Governing Body' and outcome in {'approved', 'approved-with-conditions'}:
        eligible = [p for p in prior if p['admitted'] and p['fields'].get('body') == 'Executive Committee of the Medical Staff' and p['fields'].get('outcome') == 'recommended' and p['fields'].get('revision') == f.get('revision') and p['fields'].get('application') == f.get('application') and p['fields'].get('decision_date', '') < when]
        if not eligible:
            failures.append('7 recommendation: no separately valid prior Executive Committee recommendation for this revision')
    gb_prior = [p for p in prior if p['admitted'] and p['fields'].get('body') == 'Governing Body' and p['fields'].get('revision') == f.get('revision')]
    if body == 'Governing Body' and gb_prior and f.get('supersedes') != gb_prior[-1]['fields'].get('decision_id'):
        failures.append('8 duplicate/supersession: later Governing Body record lacks required explicit supersession')
    if outcome == 'approved-with-conditions':
        failures.extend('Conditions: ' + x for x in decision_conditions(doc)[1])
    if f.get('effective_date') and f['effective_date'] < when:
        failures.append('Effective-date backdate is unresolved under Q05; no activation is inferred')
    if document_conflicts(doc, app):
        failures.extend('Source conflict: ' + x for x in document_conflicts(doc, app))
    return failures


def terminal_status(docs, app, reg):
    dispositions = {d['path']: d for d in clinical_dispositions(app, docs, reg)}
    for d in reversed(docs):
        if document_conflicts(d, app):
            continue
        title, text, f = d['title'].casefold(), d['text'].casefold(), d['fields']
        if dispositions.get(d['path'], {}).get('terminal'):
            return 'discontinued', d['path']
        if 'withdraw' in title and person(f.get('from', '')) in {person(' '.join([app['first_name'], app['middle_name'], app['last_name']])), person(' '.join([app['first_name'], app['last_name']]))} and 'withdraw' in text:
            return 'withdrawn', d['path']
        if 'discontinu' in title:
            cd = next(r for r in reg['roles'] if r['role'] == 'Clinical Director')
            signatory = f.get('signatory', f.get('from', ''))
            if person(signatory) == person(cd['name']) and cd['start'] <= d['index']['date'] <= cd['end']:
                return 'discontinued', d['path']
    return None, None


def project(app, assessed, decisions, docs, reg, as_of):
    terminal, terminal_source = terminal_status(docs, app, reg)
    status = terminal
    missing = assessed['intake']['missing']
    notices = assessed['intake']['notices']
    active_requests = [n for n in notices if set(n['requested_items']) & set(missing)]
    if not status and missing:
        if any(n['returned'] for n in notices):
            status = 'returned-incomplete'
        elif active_requests:
            # Original request anchor never resets for partial/revised replies.
            # A fulfilled notice cannot expire newly identified, unrequested work.
            due = min(n['due'] for n in active_requests)
            status = 'ineligible-clock-expired' if as_of > due else 'intake-incomplete'
        elif all(n['request_coverage_known'] for n in notices):
            # Q07 owner exception: pending dispatch only, not an inferred clock.
            # Unknown notice coverage still needs review before classification.
            status = 'intake-incomplete'
    if not status and not missing:
        status = 'packet-presentable' if assessed['packet_presentable'] else 'in-verification'
        if any(not d['admitted'] for d in decisions):
            status = 'decision-inadmissible'
    approval, activation, conditions = None, None, []
    for d in decisions:
        f = d['fields']
        if not d['admitted'] or f.get('revision') != app['revision'] or f.get('body') != 'Governing Body':
            continue
        outcome = f['outcome']
        if outcome in {'approved', 'approved-with-conditions'}:
            effective = f.get('effective_date') or f['decision_date']
            end = appointment_cycle_end(effective)
            approval = f['decision_id']
            conditions = deepcopy(d.get('conditions', []))
            wa = assessed['licensure']['wa']
            if wa and effective <= wa['expirationdate'] <= end:
                condition = {'condition': 'Reverify Washington licence ' + wa['credentialnumber'] + ' before expiry; recorded due date is expiry under P Check 1.', 'due': wa['expirationdate']}
                if condition not in conditions:
                    conditions.append(condition)
            activation = {'active_at_export': effective <= as_of <= end, 'effective_date': effective,
                          'cycle_end': end, 'privileges': [x.strip() for x in f['privileges'].split(';') if x.strip()]}
            if not terminal and not missing:
                status = ('active-with-conditions' if conditions else 'active') if effective <= as_of else 'approved-not-yet-effective'
        elif not terminal and not missing:
            status = 'deferred' if outcome == 'deferred-pending-information' else 'denied'
    actions = assessed['action_queue'][:]
    for condition in conditions:
        if condition['due'] <= as_of:
            actions.append({'item': 'Unmet monitored condition requires Clinical Director review: ' + condition['condition'], 'owner': 'Clinical Director', 'due': condition['due']})
    if terminal:
        actions = [{'item': f'{terminal} recorded in {terminal_source}; retained unresolved evidence is historical, not active outreach.', 'owner': 'Medical Services Professional', 'due': None}]
    for decision in decisions:
        if decision['admitted']:
            continue
        decision_id, reason = decision['fields']['decision_id'], decision['failures'][0]
        if not any(action['owner'] in {'Medical Services Professional', 'MSP'}
                   and decision_id in action['item'] and reason in action['item'] for action in actions):
            existing = next((action for action in assessed['action_queue']
                             if action['owner'] in {'Medical Services Professional', 'MSP'}
                             and decision_id in action['item'] and reason in action['item']), None)
            actions.append(existing or {'item': f'Review refused decision {decision_id}: {reason}',
                                        'owner': 'Medical Services Professional', 'due': None})
    app_result = {'application_id': app['application_id'], 'revision': int(app['revision']), 'status': status,
                  'elements': assessed['elements'], 'packet_presentable': assessed['packet_presentable'],
                  'decisions': [{'decision_id': d['fields']['decision_id'], 'admitted': d['admitted'],
                                 'reason': d['failures'][0] if d['failures'] else None} for d in decisions],
                  'approval_decision_id': approval, 'activation': activation, 'monitored_conditions': conditions,
                  'action_queue': actions}
    return app_result


def process_batch(batch, sources, retained_history=None):
    tables, as_of = batch['tables'], batch['export_date']
    reg = registry(sources)
    docs = indexed_documents(batch)
    results, history, packets, limitations = [], {}, {}, []
    for app_id in sorted({r['application_id'] for r in tables['applications']}):
        previous = (retained_history or {}).get('applications', {}).get(app_id, {})
        revisions = sorted([r for r in tables['applications'] if r['application_id'] == app_id and r['received_date'] <= as_of], key=lambda r: int(r['revision']))
        if not revisions:
            raise ValueError('No revision received by export for ' + app_id)
        app = revisions[-1]
        assessments = [assess(r, tables, docs, min(as_of, revisions[i + 1]['received_date']) if i + 1 < len(revisions) else as_of, reg) for i, r in enumerate(revisions)]
        current = assessments[-1]
        decisions = []
        readiness_history = deepcopy(previous.get('readiness_history', []))
        retained_decisions = {d['fields']['decision_id']: d for d in previous.get('decisions', [])}
        for doc in for_application(docs, app_id, as_of):
            f = doc['fields']
            if not f.get('decision_id'):
                continue
            if f['decision_id'] in retained_decisions:
                # Received decisions and their original reasons are immutable;
                # later evidence cannot retroactively admit a refused record.
                decisions.append(deepcopy(retained_decisions[f['decision_id']]))
                continue
            when = f.get('decision_date', '')
            if not when or when > as_of:
                raise ValueError('Decision date missing or after closed export: ' + doc['path'])
            candidates = [r for r in revisions if r['received_date'] < when]
            assessed_app = candidates[-1] if candidates else revisions[0]
            historical = assess(assessed_app, tables, docs, when, reg, before=True)
            failures = check_decision(doc, assessed_app, historical, reg, decisions)
            decisions.append({'fields': f, 'source': doc['path'], 'received_index': doc['index'],
                              'admitted': not failures, 'failures': failures, 'conditions': decision_conditions(doc)[0],
                              'readiness_evidence': historical})
            readiness_history.append({'revision': int(assessed_app['revision']), 'before_decision': f['decision_id'],
                                      'decision_date': when, 'presentable': historical['packet_presentable'],
                                      'outstanding': [x['detail'] for x in historical['issues']]})
        result = project(app, current, decisions, for_application(docs, app_id, as_of), reg, as_of)
        results.append(result)
        if result['status'] is None:
            limitations.append({'application_id': app_id, 'revision': int(app['revision']), 'code': 'Q07',
                                'detail': 'Required intake evidence is missing without an established applicable intake status; schema has no pre-dispatch status. Retained diagnostic file is held; pending dispatch/coverage review creates no invented clock.'})
        prior_assessments = deepcopy(previous.get('assessments', []))
        assessments = prior_assessments + [a for a in assessments if a not in prior_assessments]
        history[app_id] = {'revisions': revisions, 'assessments': assessments, 'decisions': decisions,
                           'readiness_history': readiness_history, 'current_revision': int(app['revision']),
                           'first_received_date': app['first_received_date']}
        packets[app_id] = {'revision': int(app['revision']), 'presentable': current['packet_presentable'],
                           'kind': 'revision-bound evidence summary; not a presentation event',
                           'source_documents': current['document_paths'], 'findings_and_work': current['issues'],
                           'requested': revision_rows(tables, 'privilege-requests', app),
                           'supported': current['privileges']['supported'], 'unsupported': current['privileges']['unsupported'],
                           'current_experience': 'Reserved to clinical leadership; criteria travel with the packet.'}
    observed_rules = {'B01', 'B02', 'B03', 'B04', 'B14', 'B15', 'B23', 'B24', 'B25', 'B26', 'B27', 'B28', 'B35', 'B36', 'B39', 'B40', 'B43', 'B44', 'B45'}
    for record in history.values():
        for assessed in record['assessments']:
            for item in assessed['issues']:
                observed_rules.update(re.findall(r'B\d{2}', item['rule']))
    return {'applications': results, 'history': {'raw_tables': deepcopy(tables), 'raw_documents': deepcopy(batch['documents']),
            'input_hashes': batch['input_hashes'], 'registry': reg, 'applications': history}, 'packets': packets,
            'limitations': limitations, 'rules_used': sorted(observed_rules)}
