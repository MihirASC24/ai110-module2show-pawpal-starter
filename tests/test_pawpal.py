"""Tests for the PawPal+ system classes.

Run `pytest -v` to see a plain-English description of what each test checks
(from its docstring) alongside its PASSED/FAILED status — see conftest.py.
"""

from __future__ import annotations

import pytest

from pawpal_system import DailyPlan, Owner, Pet, Task


def test_mark_complete_changes_is_complete():
    """Marks task complete."""
    task = Task("Feed")
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


def test_add_task_increments_pet_task_count():
    """Increments task count."""
    pet = Pet("Rex", "dog")
    assert pet.task_count == 0
    pet.add_task(Task("Feed"))
    assert pet.task_count == 1


# --- sort_by_time -----------------------------------------------------------


def test_sort_by_time_orders_out_of_order_events():
    """Orders events by time."""
    plan = DailyPlan(7, 5)
    plan.add_event(Task("Groom"), "15:00")
    plan.add_event(Task("Walk"), "08:00")
    plan.add_event(Task("Feed"), "12:00")
    assert [time for time, _ in plan.sort_by_time()] == ["08:00", "12:00", "15:00"]


def test_sort_by_time_lists_multi_hour_task_once():
    """Multi-hour task listed once."""
    plan = DailyPlan(7, 5)
    plan.add_event(Task("Groom", time_needed_hours=2), "09:00")  # spans 09:00 and 10:00
    result = plan.sort_by_time()
    assert len(result) == 1
    assert result[0] == ("09:00", plan.events["09:00"])


# --- filter_tasks (overloaded) ----------------------------------------------


def test_filter_tasks_by_completion_status():
    """Filters by completion status."""
    plan = DailyPlan(7, 5)
    done = Task("Feed")
    done.mark_complete()
    todo = Task("Walk")
    plan.add_event(done, "08:00")
    plan.add_event(todo, "09:00")
    assert plan.filter_tasks(True) == [done]
    assert plan.filter_tasks(False) == [todo]


def test_filter_tasks_by_pet_name():
    """Filters by pet name."""
    rex = Pet("Rex", "dog")
    milo = Pet("Milo", "cat")
    walk = Task("Walk", [rex])
    feed = Task("Feed", [milo])
    plan = DailyPlan(7, 5)
    plan.add_event(walk, "08:00")
    plan.add_event(feed, "09:00")
    assert plan.filter_tasks("Rex") == [walk]
    assert plan.filter_tasks("Milo") == [feed]


def test_filter_tasks_rejects_unsupported_type():
    """Rejects bad filter type."""
    plan = DailyPlan(7, 5)
    with pytest.raises(TypeError):
        plan.filter_tasks(3.5)


# --- recurring tasks --------------------------------------------------------


def test_once_task_does_not_spawn_on_complete():
    """Once task does not recur."""
    task = Task("Vet visit", freq="once")
    assert task.mark_complete() is None


def test_daily_task_spawns_fresh_incomplete_copy():
    """Daily task spawns copy."""
    rex = Pet("Rex", "dog")
    walk = Task("Walk", [rex], time_needed_hours=1, priority=7, freq="daily")
    rex.add_task(walk)

    nxt = walk.mark_complete()

    assert nxt is not None
    assert nxt is not walk
    assert nxt.is_complete is False
    assert nxt.freq == "daily"
    assert nxt.name == walk.name and nxt.priority == walk.priority
    # New occurrence is wired to the same pet on both sides.
    assert nxt in rex.tasks
    assert rex in nxt.applicable_pets


# --- auto_place -------------------------------------------------------------


def test_complete_task_auto_places_daily_on_next_day():
    """Daily placed next day."""
    owner = Owner("Sam", "morning", max_tasks=5)
    rex = Pet("Rex", "dog")
    owner.add_pet(rex)
    walk = Task("Walk", [rex], time_needed_hours=1, freq="daily")
    plan = DailyPlan(7, 5)
    owner.add_plan(plan)
    plan.add_event(walk, "08:00")

    plan.complete_task(walk)

    next_day = owner.plan_for(7, 6)
    assert next_day.events.get("08:00") is not None
    assert next_day.events["08:00"].name == "Walk"


def test_complete_task_auto_places_weekly_seven_days_later():
    """Weekly placed 7 days later."""
    owner = Owner("Sam", "morning", max_tasks=5)
    rex = Pet("Rex", "dog")
    owner.add_pet(rex)
    groom = Task("Groom", [rex], time_needed_hours=2, freq="weekly")
    plan = DailyPlan(7, 5)
    owner.add_plan(plan)
    plan.add_event(groom, "15:00")

    plan.complete_task(groom)

    assert any(p.month == 7 and p.day == 12 for p in owner.calendar)


def test_auto_place_handles_month_rollover():
    """Handles month rollover."""
    owner = Owner("Sam", "morning", max_tasks=5)
    rex = Pet("Rex", "dog")
    owner.add_pet(rex)
    walk = Task("Walk", [rex], time_needed_hours=1, freq="daily")
    plan = DailyPlan(7, 31)
    owner.add_plan(plan)
    plan.add_event(walk, "08:00")

    plan.complete_task(walk)

    assert any(p.month == 8 and p.day == 1 for p in owner.calendar)


def test_auto_place_returns_none_without_owner():
    """No owner still spawns copy."""
    rex = Pet("Rex", "dog")
    walk = Task("Walk", [rex], freq="daily")
    plan = DailyPlan(7, 5)  # not attached to an owner
    plan.add_event(walk, "08:00")
    # Completing still spawns the copy, but there is no calendar to place it on.
    nxt = plan.complete_task(walk)
    assert nxt is not None


def test_auto_place_falls_back_when_preferred_slot_taken():
    """Falls back when slot taken."""
    owner = Owner("Sam", "morning", max_tasks=5)
    rex = Pet("Rex", "dog")
    owner.add_pet(rex)
    walk = Task("Walk", [rex], time_needed_hours=1, freq="daily")
    plan = DailyPlan(7, 5)
    owner.add_plan(plan)
    plan.add_event(walk, "08:00")

    # Pre-occupy 08:00 on the next day so the preferred slot is unavailable.
    next_day = owner.plan_for(7, 6)
    blocker = Task("Blocker")
    next_day.add_event(blocker, "08:00")

    plan.complete_task(walk)

    # The recurring copy still gets placed, and the taken slot is left alone.
    placed = [t for t in next_day.events.values() if t.name == "Walk"]
    assert placed, "recurring Walk copy should be placed on the next day"
    assert next_day.events["08:00"] is blocker


# --- check_conflict ---------------------------------------------------------


def test_check_conflict_returns_none_when_slot_free():
    """No conflict when free."""
    plan = DailyPlan(7, 5)
    plan.add_event(Task("Feed"), "08:00")
    assert plan.check_conflict(Task("Walk"), "10:00") is None


def test_check_conflict_flags_overlapping_task():
    """Flags overlapping tasks."""
    plan = DailyPlan(7, 5)
    plan.add_event(Task("Feed"), "08:00")
    msg = plan.check_conflict(Task("Walk"), "08:00")
    assert msg is not None
    assert "'Walk'" in msg  # the task being scheduled
    assert "'Feed'" in msg  # the task it clashes with


def test_check_conflict_detects_partial_multi_hour_overlap():
    """Detects partial overlap."""
    plan = DailyPlan(7, 5)
    groom = Task("Groom", time_needed_hours=2)  # occupies 08:00 and 09:00
    plan.add_event(groom, "08:00")
    walk = Task("Walk", time_needed_hours=2)  # would occupy 09:00 and 10:00
    # Only the 09:00 hour overlaps, but the clash must still be reported.
    msg = plan.check_conflict(walk, "09:00")
    assert msg is not None
    assert "'Groom'" in msg


def test_check_conflict_lists_involved_pets_sorted():
    """Lists involved pets sorted."""
    rex = Pet("Rex", "dog")
    milo = Pet("Milo", "cat")
    feed = Task("Feed", [rex])
    walk = Task("Walk", [milo])
    plan = DailyPlan(7, 5)
    plan.add_event(feed, "08:00")
    msg = plan.check_conflict(walk, "08:00")
    # Pets from both the new and clashing tasks appear, in sorted order.
    assert "pets involved: Milo, Rex" in msg


def test_check_conflict_reports_no_pets_when_none_assigned():
    """Reports no pets assigned."""
    plan = DailyPlan(7, 5)
    plan.add_event(Task("Feed"), "08:00")
    msg = plan.check_conflict(Task("Walk"), "08:00")
    assert "no pets assigned" in msg


def test_check_conflict_ignores_same_task():
    """Ignores self-conflict."""
    plan = DailyPlan(7, 5)
    walk = Task("Walk", time_needed_hours=2)  # occupies 08:00 and 09:00
    plan.add_event(walk, "08:00")
    # A task never conflicts with itself across the hours it already owns.
    assert plan.check_conflict(walk, "08:00") is None


# --- sort_by_time (multi-hour ordering) -------------------------------------


def test_sort_by_time_orders_multi_hour_task_by_its_start():
    """Sorts multi-hour by start."""
    plan = DailyPlan(7, 5)
    plan.add_event(Task("Groom", time_needed_hours=3), "09:00")  # spans 09:00-11:00
    plan.add_event(Task("Feed"), "08:00")
    plan.add_event(Task("Walk"), "13:00")
    # A multi-hour task sorts by its earliest slot and appears exactly once.
    assert [time for time, _ in plan.sort_by_time()] == ["08:00", "09:00", "13:00"]
