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

    # Three tasks with different durations, assigned to the pets.
    tasks = [
        Task("Morning walk", [rex], time_needed_hours=1, priority=7),
        Task("Feed cat", [milo], time_needed_hours=1, priority=9),
        Task("Groom both", [rex, milo], time_needed_hours=2, priority=4),
    ]
    for task in tasks:
        for pet in task.applicable_pets:
            pet.add_task(task)

    # All three land on the same day.
    plan = DailyPlan(month=7, day=5)
    owner.add_plan(plan)
    plan.schedule(tasks)

    # Print the day's schedule.
    print(f"Schedule for {owner.name} on {plan.month}/{plan.day}")
    for hour in sorted(plan.events):
        print(f"  {hour:02d}:00  {plan.events[hour].name}")


if __name__ == "__main__":
    main()
