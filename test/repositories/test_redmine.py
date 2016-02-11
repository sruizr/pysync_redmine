import pytest
from unittest.mock import Mock, patch
from pysync_redmine.repositories.redmine import RedmineRepo
from pysync_redmine.domain import (
                                   Project,
                                   Task,
                                   Phase,
                                   Member,
                                   )
import datetime
import pdb


class A_RedmineRepo:

    def setup_method(self, method):
        self.patcher = patch('pysync_redmine.repositories.redmine.redmine')
        redmine = self.patcher.start()
        self.redmine = Mock()
        redmine.Redmine.return_value = self.redmine
        self.repo = RedmineRepo('http://fake_redmine/project/example',
                              'user', 'psw')
        self.project = Project('example')
        self.project._id = 123
        self.project.description = 'example project'

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

        redmine_repo = RedmineRepo('http://fake_redmine/project/example',
                              'user', 'psw')

        # pdb.set_trace()

        assert redmine_repo.source == 'http://fake_redmine'
        assert redmine_repo.project.key == 'example'
        assert redmine_repo.project._id == 1
        assert redmine_repo.project.description == project.name

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
        project.name = 'This is an example'
        redmine.project.get.return_value = project

        mock_input.return_value = 'user'
        mock_getpass.return_value = 'psw'

        redmine_repo = RedmineRepo('http://fake_redmine/project/example')

        assert redmine_repo.source == 'http://fake_redmine'
        assert redmine_repo.project.key == 'example'
        assert redmine_repo.project._id == 1
        assert redmine_repo.project.description == project.name
        mock_redmine.Redmine.assert_called_with('http://fake_redmine',
                                                username='user', password='psw')

    def should_load_members(self):
        pass


    def should_load_phases(self):
        pass

    def should_load_tasks(self):
        issues = []
        for i in range(0,2):
            issue = Mock()
            issue.id = i
            issue.subject = 'description {}'.format(i)

            issues.append(issue)

        self.redmine.issue.filter.return_value = issues

    def should_insert_member(self):
        member = Member(self.project, 'user_key',
                        *['master chef'])

        user = Mock()
        user.id = 456
        self.redmine.user.filter.return_value = [user]

        roles = [Mock(), Mock()]
        roles[0].id = 1
        roles[0].name = 'no my friend'
        roles[1].id = 2
        roles[1].name = 'master chef'
        self.redmine.role.all.return_value = roles

        membership = Mock()
        membership.id = 3
        self.redmine.project_membership.create.return_value = membership

        self.repo.insert_member(member)

        pars = {
                    'project_id': 123,
                    'user_id': user.id,
                    'roles_ids': [2]
        }
        self.redmine.project_membership.create.assert_called_with(
                                                                  **pars)
        assert member._id == 456

    def should_insert_phase(self):
        phase = Phase(self.project)
        phase.key = '12'
        phase.description = 'A phase description'
        phase.due_date = datetime.date(2016, 1, 4)

        version = Mock()
        version.id = 3
        self.redmine.version.create.return_value = version

        self.repo.insert_phase(phase)

        pars ={
                    'project_id': 123,
                    'name': phase.key,
                    'description': phase.description,
                    'due_date': phase.due_date
        }
        self.redmine.version.create.assert_called_with(**pars)
        assert phase._id == 3

    def should_insert_task(self):

        task = Task(self.project)

        task.description = 'task description'
        task.start_date = datetime.date(2016, 1, 4)
        task.duration = 1
        task.complete = 75

        issue = Mock()
        issue.id = 5
        self.redmine.issue.create.return_value = issue

        self.repo.insert_task(task)

        pars = {
            'project_id': 123,
            'subject': 'task description',
            'start_date': datetime.date(2016, 1, 4),
            'due_date': datetime.date(2016, 1, 5),
            'done_ratio': 75,
        }
        self.redmine.issue.create.assert_called_with(**pars)
        assert task._id == 5

    def get_basic_frame(self):
        mock_repository = Mock()
        self.project.repository = mock_repository

        phase = Phase(self.project)
        phase._id = 2
        phase.save()

        member = Member(self.project, 'member_key')
        member._id = 5
        member.save()

        main_task = Task(self.project)
        main_task.description = 'Initial description'
        main_task.start_date = datetime.date(2016, 1, 4)
        main_task.duration = 2
        main_task.complete = 75
        main_task._id = 1
        main_task.save()

        parent = Task(self.project)
        parent.description = 'parent description'
        parent.start_date = datetime.date(2016, 1, 4)
        parent.duration = 1
        parent.complete = 100
        parent._id = 2
        parent.save()

        next_task = Task(self.project)
        next_task.description = 'next_task description'
        next_task.start_date = datetime.date(2016, 1, 4)
        next_task.duration = 1
        next_task.complete = 100
        next_task._id = 3
        next_task.save()

        return (phase, member, parent, main_task, next_task)

    def should_update_task_update_main_fields_and_new_nexts(self):

        phase, member, parent, main_task, next_task = self.get_basic_frame()

        # Updating changes
        main_task.description = 'Final description'
        main_task.start_date = datetime.date(2016, 1, 5)
        main_task.duration = 3
        main_task.complete = 100
        main_task.assigned_to = member
        main_task.phase = phase
        main_task.parent = parent

        main_task.relations.add_next(next_task, 0)

        self.redmine.issue_relation.filter.return_value = []

        self.repo.update_task(main_task)

        pars = {
            'subject': 'Final description',
            'start_date': main_task.start_date,
            'due_date': datetime.date(2016, 1, 8),
            'done_ratio': 100,
            'fixed_version_id': phase._id,
            'assigned_to_id': member._id,
            'parent_issue_id': parent._id,
        }
        self.redmine.issue.update.assert_called_with(1, **pars)

        pars = {
            'issue_id': main_task._id,
            'issue_to_id': next_task._id,
            'relation_type': 'precedes',
            'delay': 0
            }
        self.redmine.issue_relation.create.assert_called_with(
                                                        **pars)

    def should_update_tasks_with_removed_next_tasks(self):
        phase, member, parent, main_task, next_task = self.get_basic_frame()

        mock_relation = Mock()
        mock_relation.id = 1000
        mock_relation.issue_to_id = next_task._id
        mock_relation.relation_type = 'precedes'
        self.redmine.issue_relation.filter.return_value = [mock_relation]

        self.repo.update_task(main_task)

        self.redmine.issue_relation.delete.assert_called_with(mock_relation.id)

    def should_update_tasks_with_changed_delays(self):
        phase, member, parent, main_task, next_task = self.get_basic_frame()

        main_task.relations.add_next(next_task, 1)

        mock_relation = Mock()
        mock_relation.id = 1000
        mock_relation.issue_to_id = next_task._id
        mock_relation.relation_type = 'precedes'
        mock_relation.delay = 0
        self.redmine.issue_relation.filter.return_value = [mock_relation]

        self.repo.update_task(main_task)

        self.redmine.issue_relation.delete.assert_called_with(mock_relation.id)
        pars = {
            'issue_id': main_task._id,
            'issue_to_id': next_task._id,
            'relation_type': 'precedes',
            'delay': 1
            }
        self.redmine.issue_relation.create.assert_called_with(
                                                        **pars)

