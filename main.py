"""Demo: one owner, two pets, three tasks, one day's schedule."""

from __future__ import annotations

from pawpal_system import DailyPlan, Owner, Pet, Task


def main() -> None:
    # An owner with two pets.
    owner = Owner(name="Sam", walk_time="morning", max_tasks=5)
    rex = Pet(name="Rex", species="dog")
    milo = Pet(name="Milo", species="cat")
    owner.add_pet(rex)
    owner.add_pet(milo)

    # Three tasks: a daily walk, a one-off feed, and a weekly groom.
    walk = Task("Morning walk", [rex], time_needed_hours=1, priority=7, freq="daily")
    feed = Task("Feed cat", [milo], time_needed_hours=1, priority=9, freq="once")
    groom = Task("Groom both", [rex, milo], time_needed_hours=2, priority=4, freq="weekly")
    for task in (walk, feed, groom):
        for pet in task.applicable_pets:
            pet.add_task(task)

    # Add the tasks to the day at explicit times, deliberately OUT of order:
    # afternoon groom first, then morning walk, then midday feed.
    plan = DailyPlan(month=7, day=5)
    owner.add_plan(plan)
    plan.add_event(groom, "15:00")
    plan.add_event(walk, "08:00")
    plan.add_event(feed, "12:00")

    # Conflict detection: try to book a second task at a time already taken.
    # The walk (Rex) holds 08:00, so a vet call for Milo at 08:00 clashes even
    # though it is a different pet.
    vet_call = Task("Vet call", [milo], time_needed_hours=1, priority=6)
    milo.add_task(vet_call)
    warning = plan.check_conflict(vet_call, "08:00")
    if warning:
        print(warning)
        print()

    # Sorting: sort_by_time() puts the out-of-order tasks back in clock order.
    print(f"Schedule for {owner.name} on {plan.month}/{plan.day} (sorted by time)")
    for time, task in plan.sort_by_time():
        print(f"  {time}  {task.name}")

    # Complete the feed (one-off) and the recurring tasks. Completing the daily
    # walk and weekly groom auto-places their next occurrence on a future plan.
    plan.complete_task(feed)
    plan.complete_task(walk)
    plan.complete_task(groom)

    # Filtering by completion status (bool overload).
    print("\nStill to do on 7/5:")
    for task in plan.filter_tasks(False):
        print(f"  - {task.name}")

    # Filtering by pet name (str overload).
    print(f"\n{rex.name}'s tasks on 7/5:")
    for task in plan.filter_tasks(rex.name):
        print(f"  - {task.name}")

    # Recurrence: the daily walk and weekly groom now appear on future plans.
    print("\nUpcoming (auto-placed from completed recurring tasks):")
    for day in owner.calendar:
        if day is plan:
            continue
        for time, task in day.sort_by_time():
            print(f"  {day.month}/{day.day}  {time}  {task.name}  ({task.freq})")


if __name__ == "__main__":
    main()
