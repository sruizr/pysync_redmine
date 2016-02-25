import pysync_redmine.repositories as repos


class A_RepositoryFactory:
    def should_create_redmine_repos(self):
        repository = repos.RepoFactory.create('RedmineRepo')

        assert repository.class_key == 'RedmineRepo'

    def should_create_gantt_repos(self):
        repository = repos.RepoFactory.create('GanttRepo')

        assert repository.class_key == 'GanttRepo'
