
import pytest
from unittest.mock import Mock, patch
from pysync_redmine.repositories.ganntproject import GanttRepo
from pysync_redmine.domain import (
                                   Project,
                                   Task,
                                   Phase,
                                   Member,
                                   )
import datetime
import xml.etree.ElementTree as ET
import pdb


class A_GanttRepo:

    def setup_method(self, method):
        self.patcher = patch('pysync_redmine.repositories.ganntproject.ET')
        et = self.patcher.start()
        et.parse.return_value = self.get_xml_source()

        self.repo = GanttRepo('fakefile.gantt')

        self.project = Project('example')
        self.project._id = 123
        self.project.description = 'example project'

    def get_xml_source(self):
        xml_source = None

        return xml_source

    def teardown_method(self, method):
        self.patcher.stop()
        self.repo.close_source()

    def should_load_tasks(self):
        pass

    def should_load_phases(self):
        pass

    def should_load_members(self):
        pass

    def should_load_calendar(self):
        pass

