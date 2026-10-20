# QOL Score rules — version 1.3.0

You have two ways to score well: a healthy day with all three habits, or a highly productive day that compensates for missed habits. The app calculates both routes and keeps the higher score. It then deducts points for wake time, bedtime, and social media.

These rules apply to new submissions from version 1.3.0. Existing Notion entries retain their previously saved scores and streaks; updating the app does not recalculate historical data. Everyone competing should use the same version.

## Focus percentage

Focused minutes divided by minutes awake, multiplied by 100. Minutes awake is the interval between your entered wake time and bedtime. Nine focused hours in a 15-hour waking day is 60% focus. Focus is self-reported; the group should agree which activities count.

Changing wake time or bedtime also changes this denominator, even when those times have no additional direct timing penalty. Actual overnight sleep duration is not measured separately.

## Healthy route

Start at 100. Deduct:

- 1 point per percentage point of focus below 60%.
- 10 points for no exercise.
- 10 points for not going outside.
- 10 points for not talking to someone.

Focus above 60% adds no healthy-route bonus. Habit answers are Yes/No; duration and intensity are not scored separately.

Examples: 55% focus and all habits completed gives 95. At 60% focus with one habit missed, this route gives 90.

## Productive route

Start at 100. Below 70% focus, deduct 1.5 points per percentage point below the target. Add a 3-point deduction for each missed habit.

Above 70%, each additional percentage point offsets 1.5 points of those habit deductions. The combined productive deduction cannot go below zero, so extra focus cannot raise this route above 100.

Precisely: `productive deduction = max(0, 1.5 × (70 − focus percentage) + 3 × missed habits)`.

At 70% focus, missing one/two/three habits gives 97/94/91 on this route. The two routes together can reach 100 with:

| Habits missed | Focus needed | Winning route |
| --- | --- | --- |
| None | 60% | Healthy |
| One | 72% | Productive |
| Two | 74% | Productive |
| Three | 76% | Productive |

The app picks the higher route automatically. There is no hard switch at 60%; more focus or completing another habit cannot lower the score.

## Shared deductions

After choosing the better route:

| Input | Deduction |
| --- | --- |
| Waking after 8:30 AM | 0.2 points per minute late, capped at 15 |
| Waking at or before 8:30 AM | No direct penalty or bonus |
| Bedtime before or after **11:30 PM** | 0.2 points per minute away, capped at 15 |
| Social media up to 45 minutes | No penalty |
| Social media above 45 minutes | 0.2 points per additional minute, without a separate cap |

Both earlier and later bedtimes are penalized. The bedtime target belongs to the waking day, so 12:01 AM the next morning is 31 minutes late and costs 6.2 points. Bedtime at 11:00 PM or midnight costs 6 points. At 10:15 PM or 12:45 AM the bedtime deduction reaches its 15-point cap.

Wake time at 9:00 AM costs 6 points. Social media for 90 minutes costs 9 points. Extra productive focus can offset productive habit deductions only; it cannot cancel these shared deductions.

The final score is floored at zero, calculated at full precision, and rounded to one decimal place when submitted/displayed.

## Example

At 50% focus, with no exercise but Yes for outside and social contact, healthy gives 80 and productive gives 67. Choose 80. Bedtime at 1:30 AM costs the maximum 15 points. With waking by 8:30 AM and social media no greater than 45 minutes, the final score is 65.

## Other rules

- Offday/Special Day = Yes overrides the normal scoring calculation to 100 after inputs pass validation. This remains eligible for a good streak. Agree on allowed off days as a group.
- A rounded final score of 65 or higher continues a good streak; below 65 continues a bad streak. Changing category starts at one. Streaks count recorded entries rather than consecutive calendar days and add no score bonus.
- Rankings use each participant's latest numbered entry; dates can differ. Ties sort alphabetically. Score, date and stored streak come from that same entry.
- Diary, username and entry number do not directly change points. The logging date determines the dates associated with wake/bedtime inputs.
- Use `YYYY-MM-DD` for the logging date and `YYYY-MM-DDTHH:MM:SS` for wake/bedtime in 24-hour format. Wake time must be on the logging date. A same-date bedtime earlier than waking is interpreted as the next morning.
- Waking periods must be greater than zero and less than 24 hours. Focus and social-media minutes must be whole, nonnegative values, each no greater than time awake.
- Entry numbers are automatic; after saving, the form shows the next number. Only one entry per date is allowed, and dates must be submitted in order. Edit older entries in Notion.
