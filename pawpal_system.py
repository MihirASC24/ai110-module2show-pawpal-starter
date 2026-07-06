"""PawPal+ system classes.

Implemented from diagrams/uml_draft.mmd: Task, Pet, DailyPlan, and Owner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import singledispatchmethod


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
    freq: str = "once"  # "once" | "daily" | "weekly"

    @property
    def duration(self) -> int:
        """Hours this task occupies once placed (at least one)."""
        return self.time_needed_hours if self.time_needed_hours > 0 else 1

    def mark_complete(self) -> Task | None:
        """Mark this task done, spawning the next occurrence if it recurs.

        A "daily" or "weekly" task automatically creates a fresh, incomplete
        copy of itself for its next occurrence, wires that copy to the same
        pets, and returns it. A one-off ("once") task returns None. The copy
        carries freq forward, so the caller can place it 1 day or 7 days later.
        """
        self.is_complete = True
        if self.freq not in ("daily", "weekly"):
            return None
        return self._spawn_next()

    def _spawn_next(self) -> Task:
        """Build the next occurrence: a new incomplete Task tied to the same pets.

        The copy carries name, duration, priority, and freq forward but starts
        incomplete (is_complete defaults to False), so the recurring chain keeps
        going. Pets are re-attached via add_task rather than by copying
        applicable_pets directly, because add_task also updates each pet's
        tasks list and task_count — keeping both sides of the link in sync.
        """
        nxt = Task(
            name=self.name,
            time_needed_hours=self.time_needed_hours,
            priority=self.priority,
            freq=self.freq,
        )
        for pet in list(self.applicable_pets):
            pet.add_task(nxt)  # keeps applicable_pets and task_count in sync both ways
        return nxt


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
    """One day's schedule of tasks, keyed by the "HH:MM" time they occupy.

    events maps "HH:MM" -> Task. A task needing time_needed_hours > 1 claims
    one entry per hour it runs, so overlaps are visible directly: a slot is
    free iff it is absent from events. The back-reference to owner lets
    schedule() consult the owner's constraints (max_tasks, walk_time)
    without those values having to be passed in separately.
    """

    HOURS_IN_DAY = 24

    # Plans store only month/day; this year is used solely for date arithmetic
    # (month rollover, e.g. daily task on 07-31 -> 08-01).
    _REF_YEAR = 2026

    # Preferred hour windows for walk tasks, indexed by Owner.walk_time.
    # Kept as integer ranges: an internal computation helper, not stored data.
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
        self.events: dict[str, Task] = {}

    @staticmethod
    def _format_hour(hour: int) -> str:
        """Render an integer hour as an 'HH:MM' clock string."""
        return f"{hour:02d}:00"

    @staticmethod
    def _parse_hour(time: str) -> int:
        """Return the integer hour component of an 'HH:MM' clock string."""
        return int(time.split(":")[0])

    def add_event(self, task: Task, time: str) -> bool:
        """Place a task at the given 'HH:MM' time, returning True only if its span was free."""
        start = self._parse_hour(time)
        if start < 0 or start + task.duration > self.HOURS_IN_DAY:
            return False
        span = [self._format_hour(h) for h in range(start, start + task.duration)]
        if any(slot in self.events for slot in span):
            return False
        for slot in span:
            self.events[slot] = task
        return True

    def remove_event(self, task: Task) -> None:
        """Free every slot currently occupied by this task."""
        for slot in [s for s, t in self.events.items() if t is task]:
            del self.events[slot]

    def check_conflict(self, task: Task, time: str) -> str | None:
        """Return a warning if scheduling `task` at `time` overlaps existing tasks.

        Checks every hour in the task's span, so a multi-hour task is caught
        even if only part of it overlaps. The message names the clashing
        task(s) and every pet involved, so a clash works the same whether the
        tasks share a pet or belong to different pets. Returns None if free.
        """
        start = self._parse_hour(time)
        span = [self._format_hour(h) for h in range(start, start + task.duration)]
        clashing: list[Task] = []
        for slot in span:
            other = self.events.get(slot)
            if other is not None and other is not task and other not in clashing:
                clashing.append(other)
        if not clashing:
            return None
        names = ", ".join(f"'{t.name}'" for t in clashing)
        pets = sorted({pet.name for t in [task, *clashing] for pet in t.applicable_pets})
        who = ", ".join(pets) if pets else "no pets assigned"
        return (
            f"WARNING: '{task.name}' at {time} conflicts with {names} "
            f"(pets involved: {who})"
        )

    def sort_by_time(self) -> list[tuple[str, Task]]:
        """Return (time, task) pairs ordered by their 'HH:MM' start time.

        Zero-padded 24-hour strings sort correctly as plain text, so sorted()
        with a lambda that keys on the time string is enough. A multi-hour task
        occupies several slots, so we keep only its first (earliest) one.
        """
        ordered = sorted(self.events.items(), key=lambda item: item[0])
        result: list[tuple[str, Task]] = []
        seen: set[int] = set()
        for time, task in ordered:
            if id(task) not in seen:
                seen.add(id(task))
                result.append((time, task))
        return result

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task complete on this plan and auto-place its next occurrence.

        Remembers the time slot the task occupied here so the recurring copy
        can be placed at the same time on its future plan. Returns the spawned
        occurrence (None for one-off tasks).
        """
        slots = [s for s, t in self.events.items() if t is task]
        start = min(slots, key=self._parse_hour) if slots else None
        nxt = task.mark_complete()
        if nxt is not None:
            self.auto_place(nxt, start)
        return nxt

    def auto_place(self, task: Task, at_time: str | None = None) -> DailyPlan | None:
        """Place a recurring task's next occurrence on its future plan.

        "daily" advances one day, "weekly" seven. The target plan is fetched
        from the owner (created if it doesn't exist yet), so completing a task
        keeps the recurring chain going without manual scheduling. Prefers the
        same time of day, falling back to the first free slot if it is taken.
        Returns the plan the task landed on, or None if there is no owner.
        """
        if self.owner is None:
            return None
        step = 1 if task.freq == "daily" else 7
        month, day = self._advance_date(step)
        target = self.owner.plan_for(month, day)
        if at_time is not None and target.add_event(task, at_time):
            return target
        target._place(task)  # preferred time was taken; use the next free slot
        return target

    def _advance_date(self, days: int) -> tuple[int, int]:
        """Return the (month, day) that is `days` after this plan's date.

        Delegates to datetime so month lengths and rollover are handled
        correctly (e.g. 07-31 + 1 day -> 08-01). Plans store only month/day,
        so _REF_YEAR supplies a year purely for the arithmetic; the year is
        discarded and only (month, day) is returned.
        """
        d = date(self._REF_YEAR, self.month, self.day) + timedelta(days=days)
        return d.month, d.day

    @singledispatchmethod
    def filter_tasks(self, key) -> list[Task]:
        """Filter this plan's tasks. Overloaded on the argument type.

        Python has no built-in method overloading, so functools.singledispatchmethod
        picks the right implementation from the *type* of the argument:
        pass a bool to filter by completion status, or a str to filter by pet name.
        """
        raise TypeError(
            f"cannot filter by {type(key).__name__}; "
            "pass a bool (completion status) or str (pet name)"
        )

    @filter_tasks.register
    def _(self, is_complete: bool) -> list[Task]:
        """Overload (bool): keep tasks whose completion status matches is_complete.

        Iterates sort_by_time(), so results come back in clock order with each
        multi-hour task listed once rather than once per slot it occupies.
        """
        return [task for _, task in self.sort_by_time() if task.is_complete == is_complete]

    @filter_tasks.register
    def _(self, pet_name: str) -> list[Task]:
        """Overload (str): keep tasks that apply to a pet with the given name.

        Like the bool overload, it builds on sort_by_time(), so the returned
        tasks are time-ordered and de-duplicated across the hours they span.
        """
        return [
            task
            for _, task in self.sort_by_time()
            if any(pet.name == pet_name for pet in task.applicable_pets)
        ]

    def schedule(self, tasks: list[Task]) -> dict[str, Task]:
        """Place tasks highest-priority first within the owner's limits, returning 'HH:MM' -> Task.

        Any task already on the plan (e.g. placed manually at a chosen time) is
        left exactly where it is and counts toward the limit, so auto-scheduling
        fills the remaining slots around fixed placements rather than moving them.
        """
        max_tasks = self.owner.max_tasks if self.owner is not None else len(tasks)
        placed_ids = {id(task) for task in self.events.values()}
        ordered = sorted(tasks, key=lambda t: t.priority, reverse=True)

        scheduled = len(placed_ids)
        for task in ordered:
            if id(task) in placed_ids:
                continue  # keep an already-placed task at its existing time
            if scheduled >= max_tasks:
                break
            if self._place(task):
                scheduled += 1
        return self.events

    def _place(self, task: Task) -> bool:
        """Try each candidate start time until the task fits."""
        for time in self.candidate_hours(task):
            if self.add_event(task, time):
                return True
        return False

    def candidate_hours(self, task: Task) -> list[str]:
        """Return start times ('HH:MM') to try, walk tasks preferring the owner's walk_time window."""
        day_hours = range(self.HOURS_IN_DAY)
        if self.owner is not None and "walk" in task.name.lower():
            window = self.WALK_WINDOWS.get(self.owner.walk_time, range(0))
            ordered = list(window) + [h for h in day_hours if h not in window]
        else:
            ordered = list(day_hours)
        return [self._format_hour(h) for h in ordered]


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

    def plan_for(self, month: int, day: int) -> DailyPlan:
        """Return the calendar plan for the given date, creating one if absent."""
        for plan in self.calendar:
            if plan.month == month and plan.day == day:
                return plan
        plan = DailyPlan(month, day)
        self.add_plan(plan)
        return plan

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
