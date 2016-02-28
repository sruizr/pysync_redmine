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
from helper import get_basic_frame as get_base
import datetime
import pdb


def get_fake_redmine():
    redmine = Mock()

    project = Mock()
    project.name = example
    project.id = 1
    redmine.project.get.return_value = project

    roles = [Mock(id=i) for i in range(0, 3)]
    names = ['Project manager', 'Developer', 'Tester']
    for i in range(0,3):
        roles[i].name = names[i]
    redmine.role.all.return_value = roles

    members = [Mock(id=i) for i in range(0, 2)]
    role_ids = [1, 2]
    user_ids = [0, 1]
    for member in members:
        member.user_id = user_ids[member.id]
        member.role_ids = role_ids
    redmine.member_ship.filter.return_value = members

    users = [Mock(id=i) for i in range(0, 2)]
    logins = ['leader', 'worker']
    for user in users:
        user.login = logins[user.id]
    redmine.user.get.side_effect = lambda x: users[x]

    version = Mock()
    version.project_id = 1
    version.name = "PHA"
    version.description = "Phase description"
    version.due_date = datetime.date(2016, 2, 15)
    redmine.version.filter.return_value = [version]

    parent_issue = Mock(id=1, subject='Parent task',
                        start_date=datetime.date(2016, 2, 15),
                        due_date=datetime.date(2015, 2, 23),
                        assigned_to=0,
                        description='No parsed description',
                        parent_issue_id=None, fixed_version_id=1)
    sub_issue = Mock(id=2, subject='Sub task',
                     start_date=datetime.date(2016, 2, 15),
                     due_date=datetime.date(2015, 2, 20),
                     assigned_to=1,
                     description=self._get_issue_description(),
                     parent_issue_id=1, fixed_version_id=1)
    alone_task = Mock(id=3, subject='Task without phase',
                       start_date=datetime.date(2016, 2, 21),
                       due_date=datetime.date(2015, 2, 21),
                       assigned_to=None,
                       description=None,
                       parent_issue_id=None, fixed_version_id=None)
    redmine.issue.filter.return_value = [parent_issue, sub_issue, alone_task]

    relation = Mock(issue_id=1, issue_to_id=3, relation_type='precedes',
                    delay=1)
    redmine.relation.filter.return_value = [relation]

class A_RedmineRepo:

    def setup_method(self, method):
        self.patcher = patch('pysync_redmine.repositories.redmine.redmine')
        redmine = self.patcher.start()
        self.source = Mock()
        redmine.Redmine.return_value = self.source

        self.repo = RedmineRepo()

        self.repo.open_source(project_key='example', url='http://fake_redmine.org',
                              username='user', password='psw')
        self.project = self.repo.project
        self.project._id = 123

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
        member_ships = dict()
        for i in range(0, 4):
            member_ships[i] = Mock()
            member_ships[i].user_id = i+1
            member_ships[i].roles_id = [r for r in range(0, i+1)]
        self.source.member_ship.filter.return_value = member_ships

        roles = dict()
        for i in range(0, 4):
            roles[i] = Mock()
            roles[i].name = 'name {}'.format(i)
            roles[i].id = i
        self.source.role.all.return_value = roles

        users = dict()
        for i in range(1, 5):
            users[i] = Mock()
            users[i].id = i
            users[i].login = 'user{}'.format(i)
        self.source.user.all.return_value = users

        self.repo.load_members()
        project = self.repo.project
        roles = list(roles.values())
        for i in range(1, 5):
            member = project.members[i]
            assert member._id == i
            assert member.key == 'user{}'.format(i)
            assert member.roles == set([r.name for r in roles[0:i]])

        pars = {'project_id': self.project._id}
        self.source.member_ship.filter.assert_called_with(**pars)
        self.source.role.all.assert_called_with()
        self.source.user.all.assert_called_with()

    @patch('pysync_redmine.repositories.redmine.ResourceWrapper')
    def should_load_phases(self, mock_wrapper):
        mock_wrapper.side_effect = lambda x, y: x

        versions = dict()
        for i in range(1, 3):
            versions[i] = Mock()
            versions[i].id = i
            versions[i].name = 'v{}'.format(i)
            versions[i].description = 'version number {}'.format(i)
            versions[i].due_date = datetime.date(2016, 1, i)

        self.source.version.filter.return_value = versions

        self.repo.load_phases()

        pars = {'project_id': self.project._id}
        self.source.version.filter.assert_called_with(project_id=self.project._id)

        for i in range(1, 3):
            phase = self.project.phases[i]
            assert phase._id == i
            assert phase.description == '{}. {}'.format(versions[i].name,
                                                        versions[i].description)
            assert phase.due_date == versions[i].due_date

    def should_load_tasks(self):
        issues = []
        for i in range(0, 2):
            issue = Mock()
            issue.id = i
            issue.subject = 'description {}'.format(i)
            issues.append(issue)

        self.source.issue.filter.return_value = issues




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
        output_2 = root.add_node(['1', '6'])
        task.inputs = [input_1, input_2]
        task.outputs = [output_1, output_2]

        issue = Mock()
        issue.id = 5
        self.source.issue.create.return_value = issue

        self.repo.insert_task(task)

        description = self._get_issue_description()
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

        phase, member, parent, main_task, next_task = get_base(self.project)

        # Updating changes
        main_task.description = 'Final description'
        main_task.start_date = datetime.date(2016, 1, 5)
        main_task.duration = 3
        main_task.complete = 100
        main_task.assigned_to = member
        main_task.phase = phase
        main_task.parent = parent

        main_task.relations.add_next(next_task, 0)

        self.source.issue_relation.filter.return_value = []

        self.repo.update_task(main_task)

        pars = {
            'subject': 'Final description',
            'start_date': main_task.start_date,
            'due_date': datetime.date(2016, 1, 7),
            'done_ratio': 100,
            'fixed_version_id': phase._id,
            'assigned_to_id': member._id,
            'parent_issue_id': parent._id
        }
        self.source.issue.update.assert_called_with(1, **pars)

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
        phase, member, parent, main_task, next_task = get_base(self.project)

        mock_relation = Mock()
        mock_relation.id = 1000
        mock_relation.issue_id = main_task._id
        mock_relation.issue_to_id = next_task._id
        mock_relation.relation_type = 'precedes'
        self.source.issue_relation.filter.return_value = [mock_relation]

        self.repo.update_task(main_task)

        self.source.issue_relation.delete.assert_called_with(mock_relation.id)

    def should_update_tasks_with_changed_delays(self):
        phase, member, parent, main_task, next_task = get_base(self.project)
        main_task.relations.add_next(next_task, 1)

        mock_relation = Mock()
        mock_relation.id = 1000
        mock_relation.issue_id = main_task._id
        mock_relation.issue_to_id = next_task._id
        mock_relation.relation_type = 'precedes'
        mock_relation.delay = 0
        self.source.issue_relation.filter.return_value = [mock_relation]

        self.repo.update_task(main_task)

        self.source.issue_relation.delete.assert_called_with(mock_relation.id)
        pars = {
            'issue_id': main_task._id,
            'issue_to_id': next_task._id,
            'relation_type': 'precedes',
            'delay': 1
            }
        self.source.issue_relation.create.assert_called_with(
                                                        **pars)

    def _get_issue_description(self):
        description = """h3. Inputs

* [[1]]
** 2
*** 3
*** 4

h3. Outputs

* [[1]]
** 5
** 6

------"""
        return description
