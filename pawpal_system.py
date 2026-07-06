"""PawPal+ system classes.

Implemented from diagrams/uml_draft.mmd: Task, Pet, DailyPlan, and Owner.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(eq=False)
class Task:
    """A single care activity for one or more pets.

    eq=False keeps Task hashable by identity so the same Task object can
    occupy several hour slots in DailyPlan.events without collapsing.
    """

    name: str
    applicable_pets: list[Pet] = field(default_factory=list)
    time_needed_hours: int = 0
    priority: int = 0
    is_complete: bool = False

    @property
    def duration(self) -> int:
        """Hours this task occupies once placed (at least one)."""
        return self.time_needed_hours if self.time_needed_hours > 0 else 1

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_complete = True


@dataclass
class Pet:
    """An animal being cared for."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)
    task_count: int = 0

    def add_task(self, task: Task) -> None:
        """Add a task to this pet, keeping task.applicable_pets and task_count in sync."""
        if task not in self.tasks:
            self.tasks.append(task)
            self.task_count += 1
        if self not in task.applicable_pets:
            task.applicable_pets.append(self)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet, keeping task.applicable_pets and task_count in sync."""
        if task in self.tasks:
            self.tasks.remove(task)
            self.task_count -= 1
        if self in task.applicable_pets:
            task.applicable_pets.remove(self)


class DailyPlan:
    """One day's schedule of tasks, keyed by the hour they occupy.

    events maps hour -> Task. A task needing time_needed_hours > 1 claims
    one entry per hour it runs, so overlaps are visible directly: an hour
    is free iff it is absent from events. The back-reference to owner lets
    schedule() consult the owner's constraints (max_tasks, walk_time)
    without those values having to be passed in separately.
    """

    HOURS_IN_DAY = 24

    # Preferred hour windows for walk tasks, indexed by Owner.walk_time.
    WALK_WINDOWS: dict[str, range] = {
        "morning": range(6, 12),
        "afternoon": range(12, 17),
        "evening": range(17, 21),
        "night": range(21, 24),
    }

    def __init__(self, month: int, day: int, owner: Owner | None = None) -> None:
        """Create an empty plan for the given date, optionally tied to an owner."""
        self.month: int = month
        self.day: int = day
        self.owner: Owner | None = owner
        self.events: dict[int, Task] = {}

    def add_event(self, task: Task, hour: int) -> bool:
        """Place a task at the given hour, returning True only if its span was free."""
        span = range(hour, hour + task.duration)
        if hour < 0 or hour + task.duration > self.HOURS_IN_DAY:
            return False
        if any(h in self.events for h in span):
            return False
        for h in span:
            self.events[h] = task
        return True

    def remove_event(self, task: Task) -> None:
        """Free every hour currently occupied by this task."""
        for hour in [h for h, t in self.events.items() if t is task]:
            del self.events[hour]

    def schedule(self, tasks: list[Task]) -> dict[int, Task]:
        """Place tasks highest-priority first within the owner's limits, returning hour -> Task."""
        max_tasks = self.owner.max_tasks if self.owner is not None else len(tasks)
        ordered = sorted(tasks, key=lambda t: t.priority, reverse=True)

        scheduled = 0
        for task in ordered:
            if scheduled >= max_tasks:
                break
            if self._place(task):
                scheduled += 1
        return self.events

    def _place(self, task: Task) -> bool:
        """Try each candidate start hour until the task fits."""
        for hour in self._candidate_hours(task):
            if self.add_event(task, hour):
                return True
        return False

    def _candidate_hours(self, task: Task) -> list[int]:
        """Return start hours to try, walk tasks preferring the owner's walk_time window."""
        day_hours = range(self.HOURS_IN_DAY)
        if self.owner is not None and "walk" in task.name.lower():
            window = self.WALK_WINDOWS.get(self.owner.walk_time, range(0))
            rest = [h for h in day_hours if h not in window]
            return list(window) + rest
        return list(day_hours)


class Owner:
    """The person using the app to care for their pets."""

    def __init__(self, name: str, walk_time: str, max_tasks: int) -> None:
        """Create an owner with a walk-time preference and daily task limit."""
        self.name: str = name
        self.walk_time: str = walk_time  # "morning" | "afternoon" | "evening" | "night"
        self.max_tasks: int = max_tasks
        self.calendar: list[DailyPlan] = []
        self.pets: list[Pet] = []

    def add_plan(self, plan: DailyPlan) -> None:
        """Add a plan to the calendar and set its owner, refusing another owner's plan."""
        if plan.owner is not None and plan.owner is not self:
            raise ValueError("plan already belongs to another owner")
        if plan not in self.calendar:
            self.calendar.append(plan)
        plan.owner = self

    def remove_plan(self, plan: DailyPlan) -> None:
        """Remove a daily plan from the calendar and clear plan.owner."""
        if plan in self.calendar:
            self.calendar.remove(plan)
            plan.owner = None

    def add_pet(self, pet: Pet) -> None:
        """Add a pet the owner cares for."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet, detaching it from its tasks to avoid dangling refs."""
        if pet in self.pets:
            self.pets.remove(pet)
        for task in list(pet.tasks):
            pet.remove_task(task)
