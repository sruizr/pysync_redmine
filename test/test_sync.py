import pytest
from unittest.mock import Mock, patch
from pysync_redmine.domain import (
                                   Repository,
                                   Task,
                                   Project,
                                   Member,
                                   Phase,
                                   RelationSet
                                   )
import pysync_redmine.repositories as repos
from pysync_redmine.sync import Syncronizer


def test_sync_red_ganttproject():
    pass


class A_Syncronizer:

    def setup_method(self, method):
        self.syncro = Syncronizer()

    def should_load_without_sync_file(self):
        self.syncro = Syncronizer()
        assert hasattr(self.syncro, 'sync_data')
        assert type(self.syncro.sync_data) == dict
        assert hasattr(self.syncro, 'projects')

    def should_load_with_sync_data(self):
        sync_data = {'fake_sync_data': True}
        self.syncro = Syncronizer(sync_data)

        pass

    def create_fake_repo(self):
        repo = Mock()
        repo.project = Project('example', repo)
        project = repo.project

        for i in range(0, 3):
            member = Member(project, "key_{}".format(i), "fakeRole")
            member._id = i
            member.save()

        phase = Phase(project, 'phase key')
        phase._id = 1
        phase.save()

        for i in range(0, 5):
            task = Task(project)
            task._id = i
            task.save()

        for i in range(0, 3):
            task = project.tasks[i]
            task.phase = phase
            task.assigned_to = project.members[i]
            task.save()

        project.tasks[3].assigned_to = project.members[0]
        project.tasks[4].assigned_to = project.members[1]

        for i in range(1, 3):
            project.tasks[i].parent = project.tasks[0]

        project.tasks[3].relations.add_next(project.tasks[4])

        return repo

    def should_deploy_one_repository_to_other(self):
        origin = self.create_fake_repo()
        destination = Mock()
        destination.insert_task = lambda x: x._id =

        destination.project = Project(origin.project.key, destination)

        self.syncro.deploy(origin, destination)
