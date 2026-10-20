"""Shared, deterministic scoring and input validation for every launcher."""
from datetime import datetime, timedelta
import math


def validate_data(data):
    result = dict(data)
    try:
        wake = datetime.strptime(result['wake_time'], '%Y-%m-%dT%H:%M:%S')
        sleep = datetime.strptime(result['sleep_time'], '%Y-%m-%dT%H:%M:%S')
        day = datetime.strptime(result['todays_date'], '%Y-%m-%d').date()
    except (KeyError, ValueError) as exc:
        raise ValueError('Use YYYY-MM-DD for the date and YYYY-MM-DDTHH:MM:SS for wake/sleep times.') from exc
    if wake.date() != day:
        raise ValueError('Wake time must be on the date being logged.')
    if sleep < wake and sleep.date() == wake.date():
        sleep += timedelta(days=1)
    minutes = (sleep - wake).total_seconds() / 60
    if not 0 < minutes < 24 * 60:
        raise ValueError('Sleep time must be after wake time and less than 24 hours later.')
    for field in ('social_media', 'time_focused'):
        try:
            value = int(str(result[field]))
        except (KeyError, ValueError) as exc:
            raise ValueError('Social media and focused time must be whole minutes.') from exc
        if not 0 <= value <= minutes:
            raise ValueError('Social media and focused minutes must each be between zero and your time awake.')
        result[field] = value
    for field in ('exercise', 'outside', 'talk', 'offday_special_day'):
        if result.get(field) not in ('Yes', 'No'):
            raise ValueError(f'{field} must be Yes or No.')
    result['sleep_time'] = sleep.strftime('%Y-%m-%dT%H:%M:%S')
    result['diary'] = str(result.get('diary', ''))
    if len(result['diary']) > 20000:
        raise ValueError('Please keep your diary under 20,000 characters.')
    return result


def calculate_qol_score(data):
    data = validate_data(data)
    wake = datetime.fromisoformat(data['wake_time'])
    sleep = datetime.fromisoformat(data['sleep_time'])
    focus_percent = data['time_focused'] / ((sleep - wake).total_seconds() / 60) * 100
    missed_habits = sum(data[field] == 'No' for field in ('exercise', 'outside', 'talk'))

    # Score both routes continuously; extra focus can offset the productive
    # route's habit deductions, but can never offset timing or social-media costs.
    healthy_deduction = max(0.0, 60 - focus_percent) + 10 * missed_habits
    productive_deduction = max(0.0, 1.5 * (70 - focus_percent) + 3 * missed_habits)
    score = 100 - min(healthy_deduction, productive_deduction)

    wake_penalty = min(max((wake - wake.replace(hour=8, minute=30, second=0)).total_seconds() / 60, 0) * .2, 15)
    # Anchor bedtime to the waking day, including when sleep is after midnight.
    ideal_sleep = wake.replace(hour=23, minute=30, second=0)
    sleep_penalty = min(abs((sleep - ideal_sleep).total_seconds() / 60) * .2, 15)
    score -= wake_penalty + sleep_penalty + max(data['social_media'] - 45, 0) * .2
    if data['offday_special_day'] == 'Yes':
        return 100.0
    return max(0.0, min(100.0, score))


def next_streak(previous, score):
    previous = int(previous or 0)
    return max(previous, 0) + 1 if score >= 65 else min(previous, 0) - 1


def top_three(scores):
    valid = [(name, float(score)) for name, score in scores.items()
             if score is not None and math.isfinite(float(score))]
    return sorted(valid, key=lambda row: (-row[1], row[0].casefold()))[:3]
