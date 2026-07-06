import math

import streamlit as st

from pawpal_system import DailyPlan, Owner, Pet, Task

# UI values don't match the backend types, so translate at the boundary:
#   duration is entered in minutes; Task counts whole hours.
#   priority is a label; DailyPlan.schedule sorts on an int (higher wins).
PRIORITY_LEVELS = {"low": 1, "medium": 2, "high": 3}


def minutes_to_hours(minutes: int) -> int:
    """Round a minute duration up to at least one whole hour for the scheduler."""
    return max(1, math.ceil(minutes / 60))


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
    pet.add_task(
        Task(
            name=task_title,
            time_needed_hours=minutes_to_hours(int(duration)),
            priority=PRIORITY_LEVELS[priority],
        )
    )

if pet.tasks:
    st.write(f"Current tasks ({pet.task_count}):")
    st.table(
        [
            {"task": t.name, "hours": t.duration, "priority": t.priority}
            for t in pet.tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Runs DailyPlan.schedule() over the pet's tasks for today.")

if st.button("Generate schedule"):
    if not pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        # Build the object graph and hand the tasks to the scheduler.
        owner = Owner(name=owner_name, walk_time=walk_time, max_tasks=int(max_tasks))
        owner.add_pet(pet)
        plan = DailyPlan(month=7, day=5)
        owner.add_plan(plan)
        events = plan.schedule(pet.tasks)

        if events:
            st.success(f"Scheduled {len(set(events.values()))} task(s) for {owner.name}.")
            st.table(
                [
                    {"time": time, "task": events[time].name}
                    for time in sorted(events)
                ]
            )
        else:
            st.warning("Nothing could be scheduled.")

        scheduled = set(events.values())
        dropped = [t.name for t in pet.tasks if t not in scheduled]
        if dropped:
            st.info(f"Not scheduled (over max of {owner.max_tasks}): {', '.join(dropped)}")
