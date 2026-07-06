"""Tests for the PawPal+ system classes."""

from __future__ import annotations

from pawpal_system import Pet, Task


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
