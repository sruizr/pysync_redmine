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
        assert phase.description == "Version Description"
        assert phase.id == 0
        assert phase.begin_date == dt.datetime(2016, 2, 3)
        assert phase.due_date == dt.date(2016, 2, 12)
        assert phase.duration == 9
        assert phase.complete == 48

