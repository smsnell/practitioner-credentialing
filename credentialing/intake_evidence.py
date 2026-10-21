"""Assess actual supplied application/CV documents, retaining comparison evidence.

Labelled Markdown is a supported input representation, not an office-mandated
form. Unrecognized representations stay outstanding for review. No attestation
substitutes for application signature or CV contents.
"""
from datetime import date
import re

from .documents import document_conflicts
from .policy import normalized, person
from .revisions import verified_role


def valid_date(value):
    try:
        return date.fromisoformat(value).isoformat() == value
    except (ValueError, TypeError):
        return False


def cv_rows(text):
    rows, headers = [], None
    required = {'entry', 'organization', 'role', 'from', 'to'}
    for line in text.splitlines():
        if not line.strip().startswith('|'):
            continue
        values = [v.strip() for v in line.strip().strip('|').split('|')]
        keys = [normalized(v) for v in values]
        if required <= set(keys):
            headers = keys
            continue
        if headers is None or all(re.fullmatch(r':?-+:?', v) for v in values):
            continue
        if len(values) != len(headers):
            return [], 'Malformed CV history row'
        rows.append(dict(zip(headers, values)))
    if not rows or len({r['entry'] for r in rows}) != len(rows):
        return [], 'CV history is absent, unsupported or has duplicate entry identifiers'
    return rows, None


def evaluate_intake_documents(app, docs, entries, entry_checks, as_of):
    result = {'signature': {'established': False, 'source_refs': [], 'rejected': []},
              'cv': {'resolved': False, 'source_refs': [], 'comparisons': [], 'failures': [], 'conflicts': []}}
    cvs = []
    for doc in docs:
        title = normalized(doc['title'])
        if title not in {'application', 'signed application', 'curriculum vitae', 'cv'}:
            continue
        fields, index = doc['fields'], doc['index']
        received = index.get('date', '')
        applicable = (index.get('application_id') == app['application_id']
                      and fields.get('application') == app['application_id']
                      and str(fields.get('revision')) == str(app['revision'])
                      and fields.get('applicant') and not document_conflicts(doc, app)
                      and index.get('document_path') == doc['path']
                      and index.get('direction') == 'inbound' and valid_date(received)
                      and app['first_received_date'] <= received <= as_of)
        if not applicable:
            result['signature' if title in {'application', 'signed application'} else 'cv'].setdefault('rejected', []).append(doc['path'])
            continue
        if title in {'application', 'signed application'}:
            signed = fields.get('signature_date', '')
            names = {person(' '.join(app[k] for k in ('first_name', 'middle_name', 'last_name'))),
                     person(' '.join(app[k] for k in ('first_name', 'last_name')))}
            if valid_date(signed) and signed <= received and person(fields.get('signature', '')) in names:
                result['signature']['established'] = True
                result['signature']['source_refs'].append(doc['path'])
            else:
                result['signature']['rejected'].append(doc['path'])
        else:
            cvs.append(doc)
    cv = result['cv']
    if not cvs:
        cv['failures'].append('Actual CV contents for this revision are not established by available documents')
        return result
    expected = {e['entry_id']: e for e in entries}
    for doc in cvs:
        cv['source_refs'].append(doc['path'])
        rows, error = cv_rows(doc['text'])
        if error:
            cv['failures'].append(doc['path'] + ': ' + error)
            continue
        actual = {r['entry']: r for r in rows}
        if actual.keys() != expected.keys():
            cv['failures'].append(doc['path'] + ': CV and application history coverage differs; reconcile missing/extra entries')
        for key in actual.keys() & expected.keys():
            row, declared = actual[key], expected[key]
            for field, other in [('organization', 'organization'), ('role', 'role'), ('from', 'from_date'), ('to', 'to_date')]:
                same = normalized(row[field]) == normalized(declared.get(other, ''))
                comparison = {'entry_id': key, 'field': field, 'cv': row[field], 'application': declared.get(other, ''),
                              'matches': same, 'source_refs': [doc['path'], 'declared-history.csv#' + key]}
                cv['comparisons'].append(comparison)
                if not same:
                    cv['conflicts'].append(comparison)
            for check in entry_checks or []:
                if check['entry_id'] != key:
                    continue
                for reply in check['verification_rows']:
                    if reply['reply_id'] not in check['accepted_reply_ids']:
                        continue
                    for field, other in [('from', 'verified_from'), ('to', 'verified_to')]:
                        same = row[field] == reply.get(other, '')
                        comparison = {'entry_id': key, 'field': field, 'cv': row[field], 'verified': reply.get(other, ''),
                                      'matches': same, 'source_refs': [doc['path'], 'verification-replies.csv#' + reply['reply_id']]}
                        cv['comparisons'].append(comparison)
                        if not same:
                            cv['conflicts'].append(comparison)
                    role = verified_role(reply)
                    if role is None:
                        cv['failures'].append(reply['reply_id'] + ': verified position/credential cannot be compared automatically; review source text')
                    else:
                        comparison = {'entry_id': key, 'field': 'role', 'cv': row['role'], 'verified': role,
                                      'matches': normalized(row['role']) == normalized(role),
                                      'source_refs': [doc['path'], 'verification-replies.csv#' + reply['reply_id']]}
                        cv['comparisons'].append(comparison)
                        if not comparison['matches']:
                            cv['conflicts'].append(comparison)
    # This clears only the performed CV comparison. Other source/element work
    # and all human dispositions remain independent holds, recalculated later.
    cv['resolved'] = bool(cv['comparisons']) and not cv['failures'] and not cv['conflicts']
    return result
