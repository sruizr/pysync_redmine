from pysync_redmine.repositories.redmine import RedmineRepo
from pysync_redmine.repositories.ganttproject import GanttRepo


class RepoFactory:

    @staticmethod
    def create(class_key):
        if class_key == 'RedmineRepo':
            return RedmineRepo()

        if class_key == 'GanttRepo':
            return GanttRepo()
