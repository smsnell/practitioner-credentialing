"""Read the supplied standing registries; names and privilege mappings are data."""
import re


def cells(text):
    return [x.strip().lstrip('\ufeff') for x in text.splitlines() if x.strip()]


def normalized(value):
    return ' '.join(re.sub(r'[^\w]+', ' ', value.casefold()).split())


def person(value):
    words = normalized(value).split()
    return ' '.join(w for w in words if w not in {'dr', 'ms', 'mr', 'md', 'do', 'cpmsm'})


def source_text(sources, stem):
    for key, value in sources.items():
        if key in (stem, stem + '.md'):
            return value
    raise ValueError('Missing standing source: ' + stem)


def registry(sources):
    authority = source_text(sources, 'authority-roster')
    lines = cells(authority)
    start = lines.index('Who may record what') + 4
    bodies = {}
    for i in range(start, start + 9, 3):
        bodies[lines[i]] = [v.strip() for v in lines[i + 1].split(',')]
    start = lines.index('Individual authority') + 5
    roles = []
    for i in range(start, start + 24, 4):
        role, name, term, powers = lines[i:i + 4]
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', term)
        roles.append({'role': role, 'name': name, 'start': dates[0] if dates else None,
                      'end': dates[1] if dates else None, 'powers': powers})
    criteria = source_text(sources, 'privilege-criteria')
    version = re.search(r'Criteria version (\S+), in force from (\d{4}-\d{2}-\d{2})', criteria)
    if not version:
        raise ValueError('Unrecognized criteria version header')
    lines = cells(criteria)
    groups = {}
    for i, value in enumerate(lines):
        if re.fullmatch(r'PRIV-[A-Z]+', value):
            title, certification, training, experience = lines[i + 1:i + 5]
            boards = []
            for part in certification.split(';'):
                match = re.search(r'\(([A-Z]+)\)(?:,\s*(.*))?$', part.strip())
                if not match:
                    raise ValueError('Unrecognized board mapping: ' + part)
                boards.append({'code': match[1], 'specialty': match[2] or None})
            groups[value] = {'title': title, 'boards': boards, 'training': training,
                             'experience_for_leadership': experience}
    if len(groups) != 12 or len(roles) != 6 or len(bodies) != 3:
        raise ValueError('Standing registry shape does not match the supplied contract')
    designation = re.search(r'Designation of record\. On (\d{4}-\d{2}-\d{2})', authority)
    if not designation:
        raise ValueError('Missing recorded designee designation date')
    return {'bodies': bodies, 'roles': roles, 'designation_date': designation[1], 'criteria_version': version[1],
            'criteria_effective': version[2], 'groups': groups}
