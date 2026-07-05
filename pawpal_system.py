"""PawPal+ system class skeleton.

Generated from diagrams/uml_draft.mmd. Method bodies are left as stubs
(`raise NotImplementedError`) to be filled in during implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(eq=False)
class Task:
    """A single care activity for one or more pets.

    eq=False keeps Task hashable by identity so it can be used as a
    dict key in DailyPlan.events.
    """

    name: str
    applicable_pets: list[Pet] = field(default_factory=list)
    time_needed_hours: int = 0
    priority: int = 0


@dataclass
class Pet:
    """An animal being cared for."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        raise NotImplementedError


class DailyPlan:
    """One day's schedule of tasks, keyed by the hour they occur."""

    def __init__(self, month: int, day: int) -> None:
        self.month: int = month
        self.day: int = day
        self.events: dict[Task, int] = {}

    def add_event(self, task: Task, hour: int) -> bool:
        """Place a single task at the given hour.

        Returns True if the task fit, False if it could not be scheduled.
        """
        raise NotImplementedError

    def remove_event(self, task: Task) -> None:
        """Remove a task from the day's events."""
        raise NotImplementedError

    def schedule(self, tasks: list[Task]) -> dict[Task, int]:
        """Lay a batch of tasks into the day, resolving conflicts by priority.

        Returns the resulting Task -> hour mapping.
        """
        raise NotImplementedError


class Owner:
    """The person using the app to care for their pets."""

    def __init__(self, name: str, walk_time: str, max_tasks: int) -> None:
        self.name: str = name
        self.walk_time: str = walk_time  # "morning" | "afternoon" | "evening" | "night"
        self.max_tasks: int = max_tasks
        self.calendar: list[DailyPlan] = []
        self.pets: list[Pet] = []

    def add_plan(self, plan: DailyPlan) -> None:
        """Add a daily plan to the owner's calendar."""
        raise NotImplementedError

    def remove_plan(self, plan: DailyPlan) -> None:
        """Remove a daily plan from the owner's calendar."""
        raise NotImplementedError

    def add_pet(self, pet: Pet) -> None:
        """Add a pet the owner cares for."""
        raise NotImplementedError

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from the owner's pets."""
        raise NotImplementedError
