"""Private user configuration, kept outside application bundles."""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def config_path():
    if os.environ.get('QOL_CONFIG'):
        return Path(os.environ['QOL_CONFIG']).expanduser()
    return Path.home() / 'Library' / 'Application Support' / 'QOL Score' / 'config.json'


def validate_config(config):
    if not isinstance(config, dict) or not isinstance(config.get('all_users'), dict):
        raise ValueError('Settings must contain a participant mapping.')
    name = config.get('user', '')
    if not isinstance(name, str):
        raise ValueError('Your display name must be text.')
    users = config.get('all_users', {})
    if not name.strip() or name not in users:
        raise ValueError('Choose a username with a configured Notion connection.')
    for label, connection in users.items():
        if not isinstance(connection, dict) or not all(isinstance(connection.get(k), str) and connection[k].strip() for k in ('NOTION_TOKEN', 'DATABASE_ID')):
            raise ValueError(f'Missing Notion token or database ID for {label}.')
    try:
        ZoneInfo(config.get('timezone', 'America/Los_Angeles'))
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError('Enter a valid timezone, for example America/Los_Angeles or Europe/London.') from exc
    return config


def load_config(path=None):
    path = Path(path) if path else config_path()
    try:
        return validate_config(json.loads(path.read_text()))
    except FileNotFoundError:
        return None
    except (ValueError, TypeError, AttributeError, UnicodeError) as exc:
        raise ValueError(f'Invalid configuration at {path}: {exc}') from exc


def save_config(config, path=None):
    validate_config(config)
    path = Path(path) if path else config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement prevents a partial configuration on interruption.
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(config, stream, indent=2)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def backup_config(path=None):
    """Preserve unreadable settings before allowing first-run setup to replace them."""
    path = Path(path) if path else config_path()
    if not path.exists():
        return None
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = path.with_name(path.name + '.' + stamp + '.bak')
    path.chmod(0o600)
    path.rename(backup)
    return backup
