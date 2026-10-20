"""Bounded Notion requests; no automatic retries of record creation."""
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

SCHEMA = {'Name': 'title', 'Wake Time': 'date', 'Sleep Time': 'date',
          'Exercise?': 'select', 'Went Outside?': 'select', 'Talk to Someone?': 'select',
          'Min. on Social Media': 'number', 'Date': 'date', 'Time Focused': 'number',
          'Offday/Special Day?': 'select', 'QOL Score': 'number', 'Streak': 'number', 'Diary': 'rich_text'}


class NotionError(RuntimeError):
    pass


class NotionClient:
    def __init__(self, connection, timezone='America/Los_Angeles', session=None):
        self.database_id = connection['DATABASE_ID'].strip()
        self.timezone = ZoneInfo(timezone)
        self.session = session or requests.Session()
        self.headers = {'Authorization': 'Bearer ' + connection['NOTION_TOKEN'].strip(),
                        'Content-Type': 'application/json', 'Notion-Version': '2025-09-03'}
        self.source_id = None
        self.properties = None

    def request(self, method, path, **kwargs):
        try:
            response = self.session.request(method, 'https://api.notion.com/v1/' + path,
                                            headers=self.headers, timeout=(5, 20), **kwargs)
        except requests.RequestException as exc:
            raise NotionError('Cannot reach Notion. Check your internet connection. If saving timed out, check Notion before submitting again.') from exc
        if not response.ok:
            try:
                message = response.json().get('message', 'Request rejected')
            except ValueError:
                message = 'Request rejected'
            raise NotionError(f'Notion ({response.status_code}): {message}')
        try:
            return response.json()
        except ValueError as exc:
            raise NotionError('Notion returned an unreadable response.') from exc

    def resolve(self):
        if self.source_id:
            return
        database = self.request('GET', 'databases/' + self.database_id)
        sources = database.get('data_sources', [])
        if len(sources) != 1:
            raise NotionError('Use a Notion database with exactly one data source for QOL Score.')
        source = self.request('GET', 'data_sources/' + sources[0]['id'])
        self.properties = source.get('properties', {})
        self.source_id = sources[0]['id']

    def check_schema(self):
        self.resolve()
        wrong = [f'{key} ({kind})' for key, kind in SCHEMA.items()
                 if self.properties.get(key, {}).get('type') != kind]
        if wrong:
            raise NotionError('Your Notion database needs these properties: ' + ', '.join(wrong))

    def query(self, **payload):
        self.resolve()
        cursor = None
        seen = set()
        while True:
            body = dict(payload, page_size=100)
            if cursor:
                body['start_cursor'] = cursor
            data = self.request('POST', 'data_sources/' + self.source_id + '/query', json=body)
            yield from data.get('results', [])
            if not data.get('has_more'):
                return
            cursor = data.get('next_cursor')
            if not cursor or cursor in seen:
                raise NotionError('Notion returned an invalid pagination cursor.')
            seen.add(cursor)

    @staticmethod
    def entry_number(page):
        title = page.get('properties', {}).get('Name', {}).get('title', [])
        text = ''.join(t.get('plain_text', t.get('text', {}).get('content', '')) for t in title)
        try:
            return int(text)
        except ValueError:
            return 0

    def latest(self):
        # Name is a text property; numeric entry order must be computed explicitly.
        return max(self.query(), key=self.entry_number, default=None)

    def highest(self):
        page = self.latest()
        return self.entry_number(page) if page else 0

    def streak(self, entry):
        pages = list(self.query(filter={'property': 'Name', 'title': {'equals': str(entry)}}))
        return pages[0].get('properties', {}).get('Streak', {}).get('number') if pages else 0

    def iso(self, value):
        naive = datetime.fromisoformat(value)
        # Reject ambiguous/nonexistent clock times rather than silently changing them.
        aware = naive.replace(tzinfo=self.timezone)
        from datetime import timezone
        if aware.astimezone(timezone.utc).astimezone(self.timezone).replace(tzinfo=None) != naive:
            raise ValueError('This clock time does not exist due to daylight saving time. Choose another time.')
        if aware.utcoffset() != naive.replace(tzinfo=self.timezone, fold=1).utcoffset():
            raise ValueError('This clock time is ambiguous due to daylight saving time. Choose an unambiguous time.')
        return aware.isoformat()

    def save(self, data):
        self.check_schema()
        day = data['todays_date']
        # A daily competition gets one entry per person and date.
        if next(self.query(filter={'property': 'Date', 'date': {'equals': day}}), None):
            raise ValueError('An entry already exists for this date. Edit it in Notion instead of submitting twice.')
        latest = self.latest()
        if latest:
            date = (latest.get('properties', {}).get('Date', {}).get('date') or {}).get('start', '')[:10]
            if date and day < date:
                raise ValueError('Log dates in order so the streak stays correct. Edit older dates in Notion.')
        number = self.entry_number(latest) + 1 if latest else 1
        from core import next_streak
        previous = latest.get('properties', {}).get('Streak', {}).get('number') if latest else 0
        data['entry_number'] = str(number)
        data['streak'] = next_streak(previous, data['qol_score'])
        properties = {'Name': {'title': [{'text': {'content': str(number)}}]},
                      'Wake Time': {'date': {'start': self.iso(data['wake_time'])}},
                      'Sleep Time': {'date': {'start': self.iso(data['sleep_time'])}},
                      'Date': {'date': {'start': day}},
                      'Diary': {'rich_text': [{'text': {'content': data['diary'][i:i+2000]}}
                                              for i in range(0, len(data['diary']), 2000)]}}
        for key, field in [('Exercise?', 'exercise'), ('Went Outside?', 'outside'),
                           ('Talk to Someone?', 'talk'), ('Offday/Special Day?', 'offday_special_day')]:
            properties[key] = {'select': {'name': data[field]}}
        for key, field in [('Min. on Social Media', 'social_media'), ('Time Focused', 'time_focused'),
                           ('QOL Score', 'qol_score'), ('Streak', 'streak')]:
            properties[key] = {'number': data[field]}
        self.request('POST', 'pages', json={'parent': {'data_source_id': self.source_id}, 'properties': properties})
        return data
