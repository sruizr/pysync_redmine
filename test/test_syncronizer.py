from unittest.mock import patch, Mock
import pytest
# from pysync_redmine.repositories import Repository
from pysync_redmine.syncronizer import Syncronizer
from pysync_redmine.repositories import RepoFactory
from pysync_redmine.domain import Project
from test.repositories.helper import get_fake_repo
import pdb


class A_Syncronizer:

    def setup_method(self, method):
        self.syncro = Syncronizer()

    def should_load_without_sync_file(self):
        assert hasattr(self.syncro, 'sync_data')
        assert type(self.syncro.sync_data) == dict
        assert hasattr(self.syncro, 'projects')

    @patch('pysync_redmine.repositories.RepoFactory')
    def should_load_repositories_with_sync_data(self, mock_factory):
        sync_data = {'repositories': [
                                        {
                                                'class_key': 'fake_class_1',
                                                'setup_pars': {'par': 123}
                                        },
                                        {
                                                'class_key': 'fake_class_2',
                                                'setup_pars': {'par': 456}
                                        }
                                            ]
                                }
        mock_1, mock_2 = [Mock(class_key='fake_class_1'),
                          Mock(class_key='fake_class_2')]
        mock_factory.create.side_effect = [mock_1, mock_2]

        self.syncro = Syncronizer()

        self.syncro.load_repositories(sync_data)

        repo_1, repo_2 = self.syncro.repositories

        assert repo_1.class_key == 'fake_class_1'
        assert repo_2.class_key == 'fake_class_2'
        mock_1.open_source.assert_called_with(
                                  **sync_data['repositories'][0]['setup_pars']
                                  )
        mock_2.open_source.assert_called_with(
                                  **sync_data['repositories'][1]['setup_pars']
                                  )

    def should_add_repo(self):
        fake_repo = Mock()
        fake_repo.setup_pars = {'project_key': 'example'}
        fake_repo.class_key = 'fake_class'

        self.syncro.add_repository(fake_repo)

        assert self.syncro.sync_data['repositories'][-1]['setup_pars'] == fake_repo.setup_pars
        assert self.syncro.sync_data['repositories'][-1]['class_key'] == 'fake_class'

    @patch('pysync_redmine.syncronizer.base.redmine.RedmineRepo')
    def should_add_redmine_repo(self, mock_repo):
        redmine_repo = Mock()
        mock_repo.return_value = redmine_repo
        should_setup_pars = {
                                            'url': 'http://domain.com',
                                            'username': 'fake_user',
                                            'password': '****',
                                            'project_key': 'example'
                                            }
        redmine_repo.setup_pars = should_setup_pars
        redmine_repo.class_key = 'RedmineRepo'

        url = 'http://domain.com/project/example'
        username = 'fake_user'
        password = '****'
        self.syncro.add_redmine_project(url, username, password)

        redmine_repo.open_source.assert_called_with(**should_setup_pars)
        assert self.syncro.sync_data['repositories'][-1]['setup_pars'] == should_setup_pars
        assert self.syncro.sync_data['repositories'][-1]['class_key'] == 'RedmineRepo'

    @patch('pysync_redmine.syncronizer.base.ganttproject.GanttRepo')
    def should_add_gantt_repo(self, mock_repo):
        gantt_repo = Mock()
        mock_repo.return_value = gantt_repo
        should_setup_pars = {
                                            'filename': 'example.gan',
                                            'project_key': 'example'
                                            }
        gantt_repo.setup_pars = should_setup_pars
        gantt_repo.class_key = 'GanttRepo'

        self.syncro.add_ganttproject(filename=should_setup_pars['filename'])

        gantt_repo.open_source.assert_called_with(filename=should_setup_pars['filename'])
        assert self.syncro.sync_data['repositories'][-1]['setup_pars'] == \
            should_setup_pars
        assert self.syncro.sync_data['repositories'][-1]['class_key'] == \
            gantt_repo.class_key

    def should_avoid_add_repository_without_setup(self):
        fake_repo = RepoFactory.create('RedmineRepo')

        with pytest.raises(AttributeError):
            self.syncro.add_repository(fake_repo)

    def sho2uld_avoid_add_duplicated_repos(self):
        fake_repo = Mock()
        fake_repo.setup_pars = {'project_key': 'example'}
        fake_repo.class_key = 'fake_class'

        self.syncro.add_repository(fake_repo)
        self.syncro.add_repository(fake_repo)

        assert self.syncro.sync_data['repositories'][-1]['setup_pars'] == fake_repo.setup_pars
        assert self.syncro.sync_data['repositories'][-1]['class_key'] == 'fake_class'
        assert len(self.syncro.sync_data['repositories']) == 1

    def should_deploy_one_repository_to_other(self):
        origin = get_fake_repo()
        destination = Mock()

        def insert_task(task):
            task._id = int(task.description[-1]) + 1

        def insert_phase(phase):
            phase._id = int(phase.key[-1]) + 1

        def insert_member(member):
            member._id = int(member.key[-1]) + 1

        destination.insert_task.side_effect = insert_task
        destination.insert_phase.side_effect = insert_phase
        destination.insert_member.side_effect = insert_member

        destination.project = Project(origin.project.key, destination)
        # pdb.set_trace()
        self.syncro.deploy(origin, destination)

        assert len(self.syncro.sync_data['tasks']) == 5
        assert len(self.syncro.sync_data['phases']) == 1
        assert len(self.syncro.sync_data['members']) == 3
        assert self.syncro.sync_data['tasks'][0] == (0, 1)
        assert self.syncro.sync_data['phases'][0] == (1, 2)
        assert self.syncro.sync_data['members'][0] == (0, 1)

        project = destination.project
        parent = destination.project.tasks[1]
        assert parent.phase == project.phases[2]
        assert project.tasks[2].assigned_to == project.members[2]

        for i in range(2, 4):
            assert project.tasks[i].parent == project.tasks[1]

        assert project.tasks[4].relations.next_tasks[project.tasks[5]] == 0
        assert len(project.tasks) == 5
        assert len(project.phases) == 1
        assert len(project.members) == 3

        for i in range(0, 2):
            assert (destination.project.tasks[1].inputs[i].path() ==
                    origin.project.tasks[0].inputs[i].path())
            assert (destination.project.tasks[1].outputs[i].path() ==
                    origin.project.tasks[0].outputs[i].path())

    def sh2ould_update_destination_with_origin(self):
        pass

