from unittest.mock import Mock, patch
from pysync_redmine.repositories.ganttproject import GanttRepo
from pysync_redmine.domain import (
                                   Project,
                                   Task,
                                   Phase,
                                   Member,
                                   )
import datetime
from helper import (
                    get_fake_source_gantt,
                    load_project_base
                    )

import pdb


class A_GanttRepo:

    def setup_class(cls):
        cls.blank_project = None

    def setup_method(self, method):
        self.patcher = patch('pysync_redmine.repositories.'
                             'ganttproject.ET.parse')
        element_tree = self.patcher.start()
        root = Mock()
        element_tree.return_value = root
        root.getroot.return_value = get_fake_source_gantt()

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

    def should_insert_member_on_existing_project(self):

        new_member = Member(self.project, "fakeMember", 'fake role')

        new_member.save()

        assert new_member._id == 3
        assert self.repo.source.findall('./roles/role[@name="fake role"]')
        assert self.repo.source.findall('./resources/resource['
                                        '@name="fakeMember"]')

    def should_insert_empty_phase(self):
        new_phase = Phase(self.project, "PHA2")
        new_phase.description = "New phase description"
        new_phase.due_date = datetime.date(2016, 2, 19)
        new_phase.save()

        assert new_phase._id == 7
        phase_task = self.repo.source.find('./tasks/task[@name="{}. {}"]'.
                                        format(new_phase.key,
                                               new_phase.description))
        attributes = {'id': '7', 'name': 'PHA2. New phase description',
                'color': '#000000', 'meeting': 'false', 'start': '2016-02-19',
                'duration': '1', 'complete': '0', 'expand': 'true'}

        assert phase_task.attrib == attributes

    def should_insert_phase_with_tasks(self):
        new_phase = Phase(self.project, "PHA2")
        new_phase.description = "New phase description"
        new_phase.due_date = datetime.date(2016, 2, 19)

        new_task = Task(self.project, new_phase)
        new_task.start_date = datetime.date(2016, 2, 17)
        new_task.duration = 1

        new_phase.save()

        assert new_phase._id == 7
        phase_task = self.repo.source.find('./tasks/task[@name="{}. {}"]'.
                                        format(new_phase.key,
                                               new_phase.description))
        attributes = {'id': '7', 'name': 'PHA2. New phase description',
                'color': '#000000', 'meeting': 'false', 'start': '2016-02-17',
                'duration': '3', 'complete': '0', 'expand': 'true'}

        assert phase_task.attrib == attributes

    def should_insert_task_with_parent_and_task(self):
        load_project_base(self.project)
        self.project.repository = self.repo

        phase = self.project.phases[0]
        parent = self.project.tasks[1]

        new_task = Task(self.project, phase)
        new_task.description = "New task description"
        new_task.start_date = datetime.date(2016, 2, 17)
        new_task.duration = 4
        new_task.complete = 55
        new_task.parent = parent
        new_task.phase = phase
        new_task.assigned_to = self.project.members[0]

        new_task.save()


        assert new_task._id == 7
        attributes = {'id': '7', 'name': 'New task description',
                'color': '#8cb6ce', 'meeting': 'false', 'start': '2016-02-17',
                'duration': '4', 'complete': '55', 'expand': 'true'}
        gantt_task = self.repo.source.find('./tasks//task[@id="{}"]'.format(
                                                                   new_task._id
                                                                   ))
        assert gantt_task is not None
        assert gantt_task.attrib == attributes

        allocation = self.repo.source.find(
                    './allocations/allocation[@task-id="{}"]'.format(new_task._id)
                    )
        assert allocation is not None
        attributes = {
                        'task-id': str(new_task._id), 'resource-id': str(0),
                        'function': '1', 'responsible': 'true',
                        'load': '100.0'
                        }
        assert allocation.attrib == attributes

        # due_date = self.project.calendar.get_end_date(
        #                                               new_task.start_date,
        #                                               new_task.duration)
        # assert phase.due_date == due_date

    def should_update_task_with_new_next_steps(self):
        load_project_base(self.project)
        self.project.repository = self.repo

        task = self.project.tasks[1]
        next_task = self.project.tasks[5]
        task.relations.add_next(next_task, 6)

        task.save()

        depend = self.repo.source.find(
                           './tasks//task[@id="{}"]/depend[@id="{}"]'.format(
                                task._id, next_task._id)
                                                    )
        assert depend is not None
        attributes = {
                    'id': str(next_task._id), 'type': '2', 'difference': '6',
                    'hardness': 'Strong'
                    }
        assert depend.attrib == attributes

    def should_update_task_with_updated_next_steps(self):
        load_project_base(self.project)
        self.project.repository = self.repo

        task = self.project.tasks[2]
        next_task = self.project.tasks[3]
        task.relations.next_tasks[next_task] = 5

        task.save()

        depend_filter = './tasks//task[@id="{}"]/depend[@id="{}"]'.format(
                                                    task._id, next_task._id)
        depend = self.repo.source.find(depend_filter)
        assert depend is not None
        attributes = {
                    'id': str(next_task._id), 'type': '2', 'difference': '5',
                    'hardness': 'Strong'
                    }
        assert depend.attrib == attributes

    def should_update_task_with_removed_next_step(self):
        load_project_base(self.project)
        self.project.repository = self.repo

        task = self.project.tasks[2]
        next_task = self.project.tasks[3]
        task.relations.next_tasks.pop(next_task)

        task.save()

        depend_filter = './tasks//task[@id="{}"]/depend[@id="{}"]'.format(
                                                    task._id, next_task._id)
        depend = self.repo.source.find(depend_filter)
        assert depend is None
