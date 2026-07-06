import math
from datetime import time as clock_time
from datetime import timedelta

import streamlit as st

from pawpal_system import DailyPlan, Owner, Pet, Task

# UI values don't match the backend types, so translate at the boundary:
#   duration is entered in minutes; Task counts whole hours.
#   priority is a label; DailyPlan.schedule sorts on an int (higher wins).
PRIORITY_LEVELS = {"low": 1, "medium": 2, "high": 3}
PRIORITY_LABELS = {level: label for label, level in PRIORITY_LEVELS.items()}

# Ways the user can order the task list. Each maps to (sort key, reverse).
TASK_SORTS = {
    "Priority (high → low)": (lambda t: t.priority, True),
    "Priority (low → high)": (lambda t: t.priority, False),
    "Duration (long → short)": (lambda t: t.duration, True),
    "Duration (short → long)": (lambda t: t.duration, False),
    "Title (A → Z)": (lambda t: t.name.lower(), False),
}


def minutes_to_hours(minutes: int) -> int:
    """Round a minute duration up to at least one whole hour for the scheduler."""
    return max(1, math.ceil(minutes / 60))


def conflict_reason(plan: DailyPlan, task: Task) -> str | None:
    """Explain why `task` couldn't fit: the clash at its most-preferred free-less slot.

    The scheduler tries candidate times in preference order and gives up when
    every one is occupied. We replay that order and return the first conflict
    message, which names the tasks (and pets) blocking the preferred slot.
    """
    for time in plan.candidate_hours(task):
        warning = plan.check_conflict(task, time)
        if warning is not None:
            return warning
    return None


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

col_pref1, col_pref2 = st.columns(2)
with col_pref1:
    walk_time = st.selectbox("Preferred walk time", ["morning", "afternoon", "evening", "night"])
with col_pref2:
    max_tasks = st.number_input("Max tasks per day", min_value=1, max_value=24, value=5)

# The Pet lives in the session "vault" so Task objects added below survive reruns.
if "pet" not in st.session_state:
    st.session_state.pet = Pet(name=pet_name, species=species)
pet = st.session_state.pet
pet.name, pet.species = pet_name, species  # keep display in sync with the inputs

# Owner and DailyPlan also live in the session vault so manually scheduled
# events survive reruns and conflicts can be checked against what's already placed.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, walk_time=walk_time, max_tasks=int(max_tasks))
owner = st.session_state.owner
owner.name, owner.walk_time, owner.max_tasks = owner_name, walk_time, int(max_tasks)
owner.add_pet(pet)  # no-op if already added

if "plan" not in st.session_state:
    st.session_state.plan = DailyPlan(month=7, day=5)
    owner.add_plan(st.session_state.plan)
plan = st.session_state.plan

# Task stores only whole hours, so remember the minutes each task was entered
# with (keyed by object id) to display the real duration the user typed.
if "task_minutes" not in st.session_state:
    st.session_state.task_minutes = {}

# The plan keys events by the whole hour a task occupies, so remember the exact
# HH:MM start time the user picked (keyed by object id) for display.
if "start_times" not in st.session_state:
    st.session_state.start_times = {}

st.markdown("### Tasks")
st.caption("Add a few tasks. Each one becomes a Task attached to the pet.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    new_task = Task(
        name=task_title,
        time_needed_hours=minutes_to_hours(int(duration)),
        priority=PRIORITY_LEVELS[priority],
    )
    pet.add_task(new_task)
    st.session_state.task_minutes[id(new_task)] = int(duration)

if pet.tasks:
    st.write(f"Current tasks ({pet.task_count}):")
    sort_choice = st.selectbox("Sort tasks by", list(TASK_SORTS), key="task_sort")
    key_fn, reverse = TASK_SORTS[sort_choice]
    sorted_tasks = sorted(pet.tasks, key=key_fn, reverse=reverse)
    st.table(
        [
            {
                "task": t.name,
                "minutes": st.session_state.task_minutes.get(id(t), t.duration * 60),
                "reserves (hrs)": t.duration,
                "priority": PRIORITY_LABELS.get(t.priority, t.priority),
            }
            for t in sorted_tasks
        ]
    )
    st.caption(
        "The scheduler works in whole-hour slots, so a task shorter than an hour "
        "still reserves one full hour."
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Schedule a Task at a Specific Time")
st.caption("Pick a task and a start time. You'll get a warning if it clashes with what's already scheduled.")

if pet.tasks:
    mcol1, mcol2 = st.columns([3, 1])
    with mcol1:
        task_idx = st.selectbox(
            "Task",
            options=list(range(len(pet.tasks))),
            format_func=lambda i: pet.tasks[i].name,
            key="manual_task",
        )
    with mcol2:
        start = st.time_input(
            "Start time",
            value=clock_time(8, 0),
            step=timedelta(minutes=5),
            key="manual_time",
        )

    chosen = pet.tasks[task_idx]
    slot = f"{start.hour:02d}:{start.minute:02d}"
    if st.button("Schedule at time"):
        # check_conflict ignores the task's own slots, so it's safe to check
        # before freeing them — that way a clash with *another* task is caught first.
        warning = plan.check_conflict(chosen, slot)
        if warning:
            st.warning(warning)
        else:
            # Free any previous placement so re-scheduling moves the task
            # rather than leaving a stale hour slot (and a duplicate) behind.
            plan.remove_event(chosen)
            if plan.add_event(chosen, slot):
                st.session_state.start_times[id(chosen)] = slot
                st.success(f"Scheduled '{chosen.name}' at {slot} (reserves {chosen.duration}h).")
            else:
                st.session_state.start_times.pop(id(chosen), None)
                st.warning(
                    f"'{chosen.name}' reserves {chosen.duration}h and would run past the "
                    f"end of the day starting at {slot}."
                )
    st.caption(
        "A task occupies the whole hour it starts in, so two tasks in the same "
        "hour (e.g. 08:15 and 08:45) still conflict."
    )
else:
    st.info("Add a task above before scheduling.")

st.divider()

st.subheader("Build Schedule")
st.caption("Auto-places the pet's tasks by priority, keeping any manual placements at their chosen times.")

if st.button("Generate schedule"):
    if not pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        # schedule() leaves manual placements untouched and fills the rest.
        events = plan.schedule(pet.tasks)

        if not events:
            st.warning("Nothing could be scheduled.")

        # Sort the tasks that didn't make it into two buckets: those blocked by a
        # full day (a real time clash) versus those simply beyond the daily limit.
        # A task with no free candidate hour is a conflict; otherwise it was cut.
        scheduled = set(events.values())
        conflicts, over_max = [], []
        for task in (t for t in pet.tasks if t not in scheduled):
            reason = conflict_reason(plan, task)
            (conflicts if reason else over_max).append((task, reason))

        if conflicts:
            st.markdown("#### ⚠️ Schedule conflicts")
            for task, reason in conflicts:
                st.warning(reason)

        if over_max:
            st.info(
                f"Not scheduled (over max of {owner.max_tasks}): "
                f"{', '.join(task.name for task, _ in over_max)}"
            )

# Current schedule — reflects both manual placements and auto-generation.
# Prefer the exact HH:MM the user picked; fall back to the whole-hour slot key
# for tasks the auto-scheduler placed (which always land on the hour).
st.markdown("### Current schedule")
if plan.events:
    st.success(f"{len(set(plan.events.values()))} task(s) scheduled for {owner.name}.")
    rows = [
        {
            "time": st.session_state.start_times.get(id(task), time),
            "task": task.name,
            "hours": task.duration,
        }
        for time, task in plan.sort_by_time()
    ]
    rows.sort(key=lambda row: row["time"])  # order by the exact time shown
    st.table(rows)
    if st.button("Clear schedule"):
        plan.events.clear()
        st.session_state.start_times.clear()
        st.rerun()
else:
    st.info("Nothing scheduled yet. Place a task above or generate a schedule.")
