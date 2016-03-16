import pytest
from click.testing import CliRunner
import os
from unittest.mock import Mock, patch
from pysync_redmine.domain import (
                                   Repository,
                                   Task,
                                   Project,
                                   Member,
                                   Phase,
                                   RelationSet,
                                   StringTree
                                   )
from pysync_redmine.sync import upload, download
import pdb


class A_SyncCommand:
    def setup_method(self, method):
        self.runner = CliRunner()

    @patch('pysync_redmine.sync.Syncronizer')
    def should_upload_from_ganttfile_to_redmine_project(self, mock_syncronizer):
        syncronizer = Mock()
        mock_syncronizer.return_value = syncronizer

        file_name = os.path.join(os.getcwd(),
                                 'test', 'resources',
                                 'example.gan')
        result = self.runner.invoke(upload, [
                                    '--filename', file_name, '--url',
                                    'http://redmine.com/projects/example',
                                    '--user', 'username', '--password', 'pass'
                                    ]
                                    )

        assert result.exit_code == 0
        syncronizer.add_ganttproject.assert_called_with(file_name)
        syncronizer.add_redmine_project.assert_called_with(
                                        'http://redmine.com/projects/example',
                                        'username', 'pass')
        syncronizer.deploy_to_redmine.assert_called_with()

    @patch('pysync_redmine.sync.Syncronizer')
    def should_download_from_redmine_project_to_ganttfile(
                                                                self,
                                                                mock_syncronizer):
        syncronizer = Mock()
        mock_syncronizer.return_value = syncronizer

        file_name = os.path.join(os.getcwd(),
                                 'test', 'resources',
                                 'example.gan')
        result = self.runner.invoke(download, [
                                    '--filename', file_name, '--url',
                                    'http://redmine.com/projects/example',
                                    '--user', 'username', '--password', 'pass'
                                    ]
                                    )

        assert result.exit_code == 0
        # pdb.set_trace()
        syncronizer.add_ganttproject.assert_called_with(file_name)
        syncronizer.deploy_to_ganttproject.assert_called_with()
        syncronizer.add_redmine_project.assert_called_with(
                                        'http://redmine.com/projects/example',
                                        'username', 'pass')
