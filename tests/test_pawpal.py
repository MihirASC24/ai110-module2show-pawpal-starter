"""Tests for the PawPal+ system classes."""

from __future__ import annotations

import pytest

from pawpal_system import DailyPlan, Owner, Pet, Task


def test_mark_complete_changes_is_complete():
    task = Task("Feed")
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


def test_add_task_increments_pet_task_count():
    pet = Pet("Rex", "dog")
    assert pet.task_count == 0
    pet.add_task(Task("Feed"))
    assert pet.task_count == 1


# --- sort_by_time -----------------------------------------------------------


def test_sort_by_time_orders_out_of_order_events():
    plan = DailyPlan(7, 5)
    plan.add_event(Task("Groom"), "15:00")
    plan.add_event(Task("Walk"), "08:00")
    plan.add_event(Task("Feed"), "12:00")
    assert [time for time, _ in plan.sort_by_time()] == ["08:00", "12:00", "15:00"]


def test_sort_by_time_lists_multi_hour_task_once():
    plan = DailyPlan(7, 5)
    plan.add_event(Task("Groom", time_needed_hours=2), "09:00")  # spans 09:00 and 10:00
    result = plan.sort_by_time()
    assert len(result) == 1
    assert result[0] == ("09:00", plan.events["09:00"])


# --- filter_tasks (overloaded) ----------------------------------------------


def test_filter_tasks_by_completion_status():
    plan = DailyPlan(7, 5)
    done = Task("Feed")
    done.mark_complete()
    todo = Task("Walk")
    plan.add_event(done, "08:00")
    plan.add_event(todo, "09:00")
    assert plan.filter_tasks(True) == [done]
    assert plan.filter_tasks(False) == [todo]


def test_filter_tasks_by_pet_name():
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
    plan = DailyPlan(7, 5)
    with pytest.raises(TypeError):
        plan.filter_tasks(3.5)


# --- recurring tasks --------------------------------------------------------


def test_once_task_does_not_spawn_on_complete():
    task = Task("Vet visit", freq="once")
    assert task.mark_complete() is None


def test_daily_task_spawns_fresh_incomplete_copy():
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
    rex = Pet("Rex", "dog")
    walk = Task("Walk", [rex], freq="daily")
    plan = DailyPlan(7, 5)  # not attached to an owner
    plan.add_event(walk, "08:00")
    # Completing still spawns the copy, but there is no calendar to place it on.
    nxt = plan.complete_task(walk)
    assert nxt is not None
