"""Token-free invitations and read-only checks for a master-account group."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from config import validate_config, save_config
from notion_client import NotionClient

ANALYSIS_ACCOUNT = 'User_Analysis_Requests_Database'


def database_id(value):
    if not isinstance(value, str):
        raise ValueError('Database IDs must be text.')
    value = value.strip()
    if value.startswith(('https://', 'http://')):
        parsed = urlsplit(value)
        if not (parsed.hostname == 'notion.so' or (parsed.hostname or '').endswith('.notion.so') or
                parsed.hostname == 'notion.site' or (parsed.hostname or '').endswith('.notion.site')):
            raise ValueError('Use a Notion database URL or its database ID.')
        value = parsed.path.rstrip('/').split('/')[-1]
    match = re.search(r'([0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})$', value)
    if not match:
        raise ValueError('Use a 32-character Notion database ID or the original database URL.')
    return match.group(1).replace('-', '').lower()


def validate_invitation(data):
    allowed = {'format', 'version', 'group_name', 'timezone', 'participants'}
    if not isinstance(data, dict) or set(data) != allowed or data.get('format') != 'qol-group' or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('Choose a QOL group invitation (version 1), not a private account config.')
    group_name = data['group_name']
    if not isinstance(group_name, str) or not group_name.strip() or len(group_name) > 100:
        raise ValueError('The group needs a name of 1–100 characters.')
    try:
        ZoneInfo(data['timezone'])
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError('The invitation needs a valid timezone.') from exc
    participants = data['participants']
    if not isinstance(participants, list) or not 1 <= len(participants) <= 100:
        raise ValueError('The invitation must contain 1–100 participants.')
    names, databases, clean = set(), set(), []
    for row in participants:
        if not isinstance(row, dict) or set(row) != {'name', 'database_id'}:
            raise ValueError('Participants may contain only a name and database ID; never a token.')
        name = row['name']
        if not isinstance(name, str) or not name.strip() or len(name) > 100 :
            raise ValueError('Each participant needs a valid display name.')
        name = name.strip()
        if name == ANALYSIS_ACCOUNT:
            raise ValueError('The analysis service cannot be a participant.')
        db = database_id(row['database_id'])
        if name.casefold() in names or db in databases:
            raise ValueError('Each participant must have a unique name and a separate database.')
        names.add(name.casefold()); databases.add(db)
        clean.append({'name': name, 'database_id': db})
    return dict(format='qol-group', version=1, group_name=group_name.strip(), timezone=data['timezone'], participants=clean)


def read_invitation(path):
    path = Path(path)
    if path.stat().st_size > 128 * 1024:
        raise ValueError('This file is too large to be a group invitation.')
    try:
        return validate_invitation(json.loads(path.read_text(encoding='utf-8')))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('This is not a readable QOL group invitation.') from exc


def make_invitation(config, name):
    return validate_invitation({'format': 'qol-group', 'version': 1, 'group_name': name,
        'timezone': config.get('timezone', 'America/Los_Angeles'),
        'participants': [{'name': user, 'database_id': connection['DATABASE_ID']}
                         for user, connection in config['all_users'].items() if user != ANALYSIS_ACCOUNT]})


def group_config(invitation, name, token, timezone):
    invitation = validate_invitation(invitation)
    if name not in {p['name'] for p in invitation['participants']}:
        raise ValueError('Choose your name from the invitation.')
    if not isinstance(token, str) or not token.strip():
        raise ValueError('Paste the group Notion token provided by the organizer.')
    return validate_config({'user': name, 'timezone': timezone.strip(), 'group_name': invitation['group_name'],
        'all_users': {p['name']: {'DATABASE_ID': p['database_id'], 'NOTION_TOKEN': token.strip()}
                      for p in invitation['participants']}})


def check_connections(config, client_factory=NotionClient):
    """Check each schema and the query endpoint; never create a record."""
    failures = {}
    for name, connection in config['all_users'].items():
        if name == ANALYSIS_ACCOUNT:
            continue
        try:
            client = client_factory(connection, config.get('timezone', 'America/Los_Angeles'))
            client.check_schema()
            # Check the query endpoint with at most one row; no record contents are shown.
            client.request('POST', 'data_sources/' + client.source_id + '/query',
                           json={'page_size': 1})
        except Exception as exc:
            # Never reflect tokens from a network/server error into the UI.
            message = str(exc).replace(connection['NOTION_TOKEN'], '[token hidden]')
            failures[name] = message
    return failures


def connect_and_save(config, path=None, client_factory=NotionClient):
    failures = check_connections(config, client_factory)
    if failures:
        detail = '\n'.join(f'{name}: {message}' for name, message in failures.items())
        raise ValueError('Setup was not saved. Ask the organizer to fix these connections, then retry:\n' + detail)
    save_config(config, path)
    return config
