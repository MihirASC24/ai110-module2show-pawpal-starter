# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Sample Output (Terminal)
Schedule for Sam on 7/5
  00:00  Feed cat
  01:00  Groom both
  02:00  Groom both
  06:00  Morning walk
```

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|

| Task sorting | `DailyPlan.sort_by_time()` | Sorts the day's events chronologically by their `"HH:MM"` key (zero-padded strings sort correctly as text); a multi-hour task is listed once, at its earliest slot. |

| Filtering | `DailyPlan.filter_tasks()` | Overloaded via `functools.singledispatchmethod`: pass a `bool` to filter by completion status, or a `str` to filter by pet name. Results reuse `sort_by_time()`, so they stay time-ordered and de-duplicated. |

| Conflict handling | `DailyPlan.check_conflict()` | Detects overlapping time slots across a task's full span and returns a warning naming the clashing task(s) and every pet involved — whether the tasks share a pet or belong to different pets. |

| Recurring tasks | `Task.mark_complete()` → `Task._spawn_next()`; auto-placed by `DailyPlan.complete_task()` → `DailyPlan.auto_place()` | Completing a `"daily"` or `"weekly"` task spawns a fresh incomplete copy and places it on the next occurrence's plan (+1 or +7 days, created via `Owner.plan_for()`); a `"once"` task spawns nothing. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
