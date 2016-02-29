from unittest.mock import Mock, patch
from pysync_redmine.repositories.ganttproject import GanttRepo
from pysync_redmine.domain import (
                                   Project,
                                   Task,
                                   Phase,
                                   Member,
                                   )
import datetime
from helper import get_mock_source_gantt
import pdb


class A_GanttRepo:

    def setup_method(self, method):
        self.patcher = patch('pysync_redmine.repositories.'
                             'ganttproject.ET.parse')
        element_tree = self.patcher.start()
        root = Mock()
        element_tree.return_value = root
        root.getroot.return_value = get_mock_source_gantt()

        self.repo = GanttRepo()
        self.repo.open_source(filename='fake_file.gan')
        self.repo.load_calendar()
        self.project = self.repo.project

    def teardown_method(self, method):
        self.patcher.stop()
        self.repo.close_source()

    def should_load_phases(self):
        self.repo.load_phases()

        assert len(self.project.phases) == 1
        phase = self.project.phases[0]
        assert phase._id == 0
        assert phase.key == 'PHA'
        assert phase.description == 'Phase description'
        assert phase.due_date == datetime.date(2016, 2, 15)

    def should_load_members(self):
        self.repo.load_members()

        assert len(self.project.members) == 3
        member = self.project.members[0]
        assert member.key == 'A_project_leader'
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
        subtask1 = self.project.tasks[2]
        subtask2 = self.project.tasks[3]
        alone = self.project.tasks[4]
        milestone = self.project.tasks[5]
        orphan = self.project.tasks[6]

        leader = self.project.members[0]
        developer = self.project.members[1]
        verifier = self.project.members[2]

        assert len(self.project.tasks) == 6
        assert len(parent.subtasks) == 2

        assert parent.subtasks[0] == subtask1
        assert parent.subtasks[1] == subtask2
        assert parent.assigned_to == leader

        assert subtask2.parent == parent
        assert subtask2.phase == phase
        assert subtask2.assigned_to == verifier
        assert subtask2.relations.next_tasks[alone] == 0
        assert len(subtask2.colaborators) == 1
        assert developer == subtask2.colaborators[0]

        assert orphan.parent is None
        assert orphan.phase is None
        assert orphan.assigned_to is None

        assert len(subtask2.inputs) == 2
        assert len(subtask2.outputs) == 2
        # print(self.project.tokens._str_level(1))
        assert len(self.project.tokens.childs) == 2
