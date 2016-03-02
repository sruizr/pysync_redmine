import pytest
from unittest.mock import Mock, patch
from pysync_redmine.repositories.redmine import RedmineRepo
from pysync_redmine.domain import (
                                   Project,
                                   Task,
                                   Phase,
                                   Member,
                                   Calendar
                                   )
from helper import load_project_base as load_base
from helper import (
                    get_mock_source_redmine,
                    get_issue_description,
                    load_phases_for_testing,
                    load_members_for_testing
                    )
import datetime
import pdb


class A_RedmineRepo:

    def setup_method(self, method):
        self.patcher = patch('pysync_redmine.repositories.redmine.redmine')
        redmine = self.patcher.start()
        self.source = get_mock_source_redmine()
        redmine.Redmine.return_value = self.source

        self.repo = RedmineRepo()

        self.repo.open_source(project_key='example', url='http://fake_redmine.org',
                              username='user', password='psw')
        self.project = self.repo.project
        self.project._id = 123
        self.repo.load_calendar()

    def teardown_method(self, method):
        self.patcher.stop()

    @patch('pysync_redmine.repositories.redmine.redmine')
    def should_be_loaded_with_project_url(self, mock_redmine):
        redmine = Mock()

        mock_redmine.Redmine.return_value = redmine
        project = Mock()
        project.id = 1
        project.name = 'This is an example'

        redmine.project.get.return_value = project

        redmine_repo = RedmineRepo()
        redmine_repo.open_source(project_key='example',
                                 url='http://fake_redmine',
                                 username='user', password='psw')

        assert redmine_repo.setup_pars['url'] == 'http://fake_redmine'
        assert redmine_repo.project.key == 'example'
        assert redmine_repo.project._id == 1

        mock_redmine.Redmine.assert_called_with(
                                                'http://fake_redmine',
                                                username='user',
                                                password='psw'
                                                )

    @patch('getpass.getpass')
    @patch('builtins.input')
    @patch('pysync_redmine.repositories.redmine.redmine')
    def should_be_loaded_without_user(self, mock_redmine, mock_input,
                                      mock_getpass):
        redmine = Mock()
        mock_redmine.Redmine.return_value = redmine

        project = Mock()
        project.id = 1
        project.key = 'example'
        project.name = 'This is an example'
        redmine.project.get.return_value = project

        mock_input.return_value = 'userrr'
        mock_getpass.return_value = 'pswww'

        redmine_repo = RedmineRepo()
        redmine_repo.open_source(project_key=project.key, url='http://fake_redmine')

        assert redmine_repo.project._id == project.id
        mock_redmine.Redmine.assert_called_with('http://fake_redmine',
                                                username='userrr',
                                                password='pswww')

    def should_load_members(self):

        self.repo.load_members()

        project = self.repo.project
        keys = ['A_project_leader', 'A_developer']
        roles = ['Developer', 'Verifier']
        for i in range(0, 2):
            member = project.members[i]
            assert member._id == i
            assert member.key == keys[i]
            assert member.roles == set([roles[i]])

        pars = {'project_id': self.project._id}
        self.source.member_ship.filter.assert_called_with(**pars)
        self.source.role.all.assert_called_with()

    @patch('pysync_redmine.repositories.redmine.ResourceWrapper')
    def should_load_tasks(self, mock_wrapper):
        project = self.repo.project

        load_phases_for_testing(project)
        load_members_for_testing(project)
        mock_wrapper.side_effect = lambda x, y: x

        self.repo.load_tasks()

        self.repo.source.issue.filter.assert_called_with(
                                                         project_id=project._id
                                                         )
        tasks = project.tasks

        assert len(tasks) == 6
        task_descriptions = ['Task with subtasks', 'Subtask 1', 'Subtask 2',
                                'Task without subtasks', 'Milestone',
                                'Task without phase']
        for i in range(1, 7):
            assert tasks[i].description == task_descriptions[i-1]

        parent = tasks[1]
        subtask_1 = tasks[2]
        subtask_2 = tasks[3]
        alone = tasks[4]
        milestone = tasks[5]
        orphan = tasks[6]

        assert parent._id == 1
        assert parent.start_date == datetime.date(2016, 2, 3)
        assert parent.duration == 8
        assert parent.complete == 12
        assert parent.phase == project.phases[0]
        assert parent.assigned_to == project.members[0]
        assert len(parent.subtasks) == 2

        assert orphan._id == 6
        assert orphan.start_date == datetime.date(2016, 2, 1)
        assert orphan.duration == 2
        assert orphan.complete == 100
        assert orphan.phase is None
        assert orphan.assigned_to is None
        assert len(orphan.subtasks) == 0

        assert parent in orphan.relations.next_tasks
        assert subtask_2 in subtask_1.relations.next_tasks
        assert alone in subtask_2.relations.next_tasks
        assert milestone in alone.relations.next_tasks

        empty_token_tasks = [parent, subtask_1, alone, milestone, orphan]
        for task in empty_token_tasks:
            assert not task.inputs, "Failed task {}, it has inputs".format(
                                                            task.description)
            assert not task.outputs, "Failed task {}, it has outputs".format(
                                                            task.description)

        assert len(subtask_2.inputs) == 2
        assert len(subtask_2.outputs) == 2
        assert subtask_2.inputs[0].path(project.tokens) == ['1', '2', '3']
        assert subtask_2.inputs[1].path(project.tokens) == ['1', '2', '4']
        assert subtask_2.outputs[0].path(project.tokens) == ['1', '5']
        assert subtask_2.outputs[1].path(project.tokens) == ['6']


    @patch('pysync_redmine.repositories.redmine.ResourceWrapper')
    def should_load_phases(self, mock_wrapper):
        mock_wrapper.side_effect = lambda x, y: x
        project = self.repo.project
        self.repo.load_phases()

        self.source.version.filter.assert_called_with(
                                                  project_id=self.project._id
                                                  )

        phase = project.phases[0]
        assert phase._id == 0
        assert phase.description == 'PHA. Phase description'
        assert phase.due_date == datetime.date(2016, 2, 15)

    def should_insert_member(self):
        member = Member(self.project, 'user_key',
                        *['master chef'])

        user = Mock()
        user.id = 456
        self.source.user.filter.return_value = [user]

        roles = [Mock(), Mock()]
        roles[0].id = 1
        roles[0].name = 'no my friend'
        roles[1].id = 2
        roles[1].name = 'master chef'
        self.source.role.all.return_value = roles

        membership = Mock()
        membership.id = 3
        self.source.project_membership.create.return_value = membership

        self.repo.insert_member(member)

        pars = {
                    'project_id': 123,
                    'user_id': user.id,
                    'role_ids': [2]
        }
        self.source.project_membership.create.assert_called_with(
                                                                  **pars)
        assert member._id == 456

    def should_insert_phase(self):
        phase = Phase(self.project)
        phase.key = '12'
        phase.description = 'A phase description'
        phase.due_date = datetime.date(2016, 1, 4)

        version = Mock()
        version.id = 3
        self.source.version.create.return_value = version

        self.repo.insert_phase(phase)

        pars = {
                    'project_id': 123,
                    'name': phase.key,
                    'description': phase.description,
                    'due_date': phase.due_date
        }
        self.source.version.create.assert_called_with(**pars)
        assert phase._id == 3

    def should_insert_task(self):

        task = Task(self.project)

        task.description = 'task description'
        task.start_date = datetime.date(2016, 1, 4)
        task.duration = 1
        task.complete = 75

        root = self.project.tokens

        input_1 = root.add_node(['1', '2', '3'])
        input_2 = root.add_node(['1', '2', '4'])
        output_1 = root.add_node(['1', '5'])
        output_2 = root.add_node(['6'])
        task.inputs = [input_1, input_2]
        task.outputs = [output_1, output_2]

        issue = Mock()
        issue.id = 5
        self.source.issue.create.return_value = issue

        self.repo.insert_task(task)

        description = get_issue_description()
        print(description)

        pars = {
            'project_id': 123,
            'subject': 'task description',
            'start_date': datetime.date(2016, 1, 4),
            'due_date': datetime.date(2016, 1, 4),
            'done_ratio': 75,
            'description': description
        }
        self.source.issue.create.assert_called_with(**pars)
        assert task._id == 5

    def should_update_task_update_main_fields_and_new_nexts(self):

        load_base(self.project)
        main_task = self.project.tasks[6]
        next_task = self.project.tasks[3]
        member = self.project.members[1]
        parent = self.project.tasks[1]
        phase = self.project.phases[0]

        # Updating changes
        main_task.description = 'Final description'
        main_task.start_date = datetime.date(2016, 1, 5)
        main_task.duration = 3
        main_task.complete = 80
        main_task.assigned_to = member
        main_task.phase = phase
        main_task.parent = parent

        main_task.relations.add_next(next_task, 0)

        mock_relation = Mock()
        mock_relation.issue_id = 6
        mock_relation.issue_to_id = 1
        mock_relation.relation_type = 'precedes'
        mock_relation.delay = 0
        self.source.issue_relation.filter.return_value = [mock_relation]

        self.repo.update_task(main_task)

        pars = {
            'subject': 'Final description',
            'start_date': main_task.start_date,
            'due_date': datetime.date(2016, 1, 7),
            'done_ratio': 80,
            'fixed_version_id': phase._id,
            'assigned_to_id': member._id,
            'parent_issue_id': parent._id
        }
        self.source.issue.update.assert_called_with(main_task._id, **pars)

        pars = {
            'issue_id': main_task._id,
            'issue_to_id': next_task._id,
            'relation_type': 'precedes',
            'delay': 0
            }
        self.source.issue_relation.create.assert_called_with(
                                                        **pars)

        assert not self.source.issue_relation.delete.called

    def should_update_tasks_with_removed_next_tasks(self):

        load_base(self.project)
        main_task = self.project.tasks[6]
        next_task = self.project.tasks[1]

        # Remove issue_relation with id=1
        main_task.relations.next_tasks.pop(next_task)

        self.repo.update_task(main_task)

        self.source.issue_relation.delete.assert_called_with(1)

    def should_update_tasks_with_changed_delays(self):
        load_base(self.project)
        main_task = self.project.tasks[6]
        next_task = self.project.tasks[1]

        # changed delay from 0 to 3
        main_task.relations.next_tasks[next_task] = 3
        self.repo.update_task(main_task)

        self.source.issue_relation.delete.assert_called_with(1)
        pars = {
            'issue_id': main_task._id,
            'issue_to_id': next_task._id,
            'relation_type': 'precedes',
            'delay': 3
            }
        self.source.issue_relation.create.assert_called_with(
                                                        **pars)


