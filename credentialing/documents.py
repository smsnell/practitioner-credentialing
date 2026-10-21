"""Extract labelled fields without allowing source prose to direct execution."""
import re
from .policy import normalized, person


def parse_document(path, text, index=None):
    fields = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        match = re.match(r'^\*\*(.+?):\*\*\s*(.*?)\s*$', line)
        if match:
            key = normalized(match[1]).replace(' ', '_')
            if key in fields:
                raise ValueError(f'Duplicate field {key} in {path}:{line_no}')
            fields[key] = match[2].strip()
    return {'path': path, 'fields': fields, 'text': text, 'index': index or {},
            'title': next((x.lstrip('# ').strip() for x in text.splitlines() if x.startswith('# ')), '')}


def indexed_documents(batch):
    result = []
    for row in batch['tables']['correspondence']:
        path = row['document_path']
        result.append(parse_document(path, batch['documents'][path], row))
    return result


def for_application(documents, app_id, as_of, before=False):
    return [d for d in documents if d['index']['application_id'] == app_id
            and d['index']['date'] <= as_of
            and (not before or d['index']['date'] < as_of)]


def document_conflicts(doc, app):
    fields, conflicts = doc['fields'], []
    if fields.get('application') and fields['application'] != app['application_id']:
        conflicts.append('Document application differs from correspondence index')
    # Office correspondence commonly omits the middle name; preserve names,
    # accepting only exact first/last plus optional declared middle name.
    expected = {person(' '.join([app['first_name'], app['middle_name'], app['last_name']])),
                person(' '.join([app['first_name'], app['last_name']]))}
    for field in ('applicant',):
        if fields.get(field) and person(fields[field]) not in expected:
            conflicts.append(f'{field} identity conflicts with application: {fields[field]}')
    if fields.get('date') and fields['date'] != doc['index']['date']:
        conflicts.append('Document date differs from correspondence index')
    if 'period_explained' in fields:
        if fields.get('from') and person(fields['from']) not in expected:
            conflicts.append('Applicant explanation sender conflicts with application identity')
    return conflicts


def period(doc):
    match = re.fullmatch(r'(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', doc['fields'].get('period_explained', ''))
    return tuple(match.groups()) if match else None


def intake_notice(doc, app):
    """Recognize recorded MSP correspondence, not a pending action or interview promise."""
    if doc['index'].get('direction') != 'outbound' or document_conflicts(doc, app):
        return None
    text, title = doc['text'].casefold(), doc['title'].casefold()
    if 'medical services professional' not in text:
        return None
    returned = title.startswith('application returned as incomplete')
    if not returned and 'missing items on your application' not in title:
        return None
    match = re.search(r'(?:by|due on) (\d{4}-\d{2}-\d{2})', doc['text'])
    # Recognize the supplied notice templates' explicit requests. Mentioning
    # an item elsewhere in a letter is not evidence that it was requested.
    requested = []
    if ('two items are missing from your application' in text
            and 'the larkhollow authorization and release, signed and dated; and a current curriculum vitae.' in text):
        requested = ['signed and dated Larkhollow release', 'CV present at submission']
    elif returned and 'please send a written explanation naming the period it covers, or a corrected application.' in text:
        requested = ['written explanation for every gap of at least 30 days']
    return {'date': doc['index']['date'], 'due_in_source': match[1] if match else None,
            'returned': returned, 'path': doc['path'], 'body': doc['text'],
            'requested_items': requested, 'request_coverage_known': bool(requested)}
