"""
Tests for `pysync_redmine` module.
"""
import pytest
from pysync_redmine.pysync_redmine import GanttProjectLoader
import datetime as dt
import pdb


class A_ProjectLoader:

    def setup_method(self, method):
        self.loader = GanttProjectLoader("test/resources/example.gan")

    def should_load_all_phases(self):
        phases = self.loader.get_phases()

        assert len(phases) == 1

        phase = phases[0]
        assert phase.description == "Version description"
        assert phase.id == 0
        assert phase.start_date == dt.date(2016, 2, 3)
        assert phase.duration == 9
        assert phase.complete == 48
        assert phase.due_date == dt.date(2016, 2, 12)

    def should_get_all_tasks_from_a_phase(self):
        phases = self.loader.get_phase()
        phase = phase[0]

        tasks = self.loader.get_tasks_from(phase)
        assert len(tasks) == 2

        task = tasks[0]
        assert task.description == "Task with subtasks"
        assert task.id == 1
        assert task.start_date == dt.date(2016, 2, 3)
        assert task.duration == 5
        assert task.complete == 61
        assert task.due_date == dt.date(2016, 2, 8)

    def should_supply_task_by_id(self):
        pass

    def should_supply_all_tasks(self):
        pass

