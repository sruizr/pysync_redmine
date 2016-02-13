
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
        self.patcher = patch('pysync_redmine.repositories.'
                             'ganntproject.ET.parse')
        element_tree = self.patcher.start()
        root = Mock()
        element_tree.return_value = root
        root.getroot.return_value = self.get_fake_source()

        self.repo = GanttRepo()
        self.project = Project('example')
        self.repo.open_source(self.project, filename='fake_file.gan')
        self.repo.load_calendar()

    def get_fake_source(self):
        source = ET.Element('project')

        roles = ET.SubElement(source, 'roles')
        ET.SubElement(roles, 'role', {'id': '1', 'name': 'Project Leader'})
        ET.SubElement(roles, 'role', {'id': '2', 'name': 'Developer'})
        ET.SubElement(roles, 'role', {'id': '3', 'name': 'Verifier'})

        resources = ET.SubElement(source, 'resources')
        ET.SubElement(resources, 'resource', {'id': '0', 'name': 'leader',
                      'function': '1'})
        ET.SubElement(resources, 'resource', {'id': '1', 'name': 'developer',
                      'function': '2'})
        ET.SubElement(resources, 'resource', {'id': '2', 'name': 'verifier',
                      'function': '3'})
        ET.SubElement(resources, 'resource', {'id': '3', 'name': 'none',
                      'function': '0'})

        tasks = ET.SubElement(source, 'tasks')
        phase = ET.SubElement(tasks, 'task', {'id': '0', 'name': 'ABC. Phase description',
                              'start': '2016-01-04', 'duration': '8', 'complete': '87'})
        parent = ET.SubElement(phase, 'task', {'id': '1', 'name': 'Parent task',
                               'start': '2016-01-04', 'duration': '3', 'complete': '87'})
        subtask = ET.SubElement(parent, 'task', {'id': '2', 'name': 'subtask task',
                               'start': '2016-01-04', 'duration': '3', 'complete': '90'})
        ET.SubElement(subtask, 'depend', {'id': '3', 'difference': '5'})
        ET.SubElement(tasks, 'task', {'id': '3', 'name': 'Task without phase',
                               'start': '2016-01-04', 'duration': '3', 'complete': '100'})

        allocations = ET.SubElement(source, 'allocations')
        ET.SubElement(allocations, 'allocation', {
                      'task-id': '1', 'resource-id': '0', 'function': '1',
                      'responsible': 'true'})
        ET.SubElement(allocations, 'allocation', {
                      'task-id': '2', 'resource-id': '1', 'function': '3',
                      'responsible': 'true'})

        return source

    def teardown_method(self, method):
        self.patcher.stop()
        self.repo.close_source()

    def should_load_phases(self):
        self.repo.load_phases()

        assert len(self.project.phases) == 1
        phase = self.project.phases[0]
        assert phase._id == 0
        assert phase.key == 'ABC'
        assert phase.due_date == datetime.date(2016, 1, 14)
        assert phase.description == 'Phase description'

    def should_load_members(self):
        self.repo.load_members()

        assert len(self.project.members) == 4
        member = self.project.members[0]
        assert member.key == 'leader'
        assert member.roles == {'Project Leader'}
        assert member.project == self.project
        assert member._id == 0

    def should_load_calendar(self):
        self.repo.load_calendar

    def should_load_tasks(self):
        self.repo.load_members()
        self.repo.load_phases()

        self.repo.load_tasks()

        phase = self.project.phases[0]
        parent = self.project.tasks[1]
        subtask = self.project.tasks[2]
        alone = self.project.tasks[3]
        leader = self.project.members[0]
        developer = self.project.members[1]

        assert len(self.project.tasks) == 3
        assert len(parent.subtasks) == 1

        assert parent.subtasks[0] == subtask
        assert parent.assigned_to == leader

        assert subtask.parent == parent
        assert subtask.phase == phase
        assert subtask.assigned_to == developer
        assert subtask.relations.next_tasks[alone] == 5
        assert alone.parent is None
        assert alone.phase is None
        assert alone.assigned_to is None

