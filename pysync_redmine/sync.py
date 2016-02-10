import json
import click
import pysync_redmine.repositories as repos


@click.command()
@click.option('--project', prompt='Enter the URL of your project',
              help='URL of project at Redmine')
@click.option('--user', prompt='Enter your user login at Redmine',
              help='User key how is goint to update system to Redmine')
@click.option('--password', prompt='Enter your password', hide_input=True)
@click.option('--file', prompt='Enter path of project file',
              help='Filename of GanntProject')
def sync_red_ganttproject(project_url, user_key, psw, filename):
    redmine = repos.redmine.RedmineRepo(project_url, user_key, psw)
    gantt = repos.ganntproject.GanttRepo(filename)

    redmine_project = redmine.open_project()
    gantt_project = gantt.open_project()

    syncronizer = Syncronizer(redmine_project, gantt_project)

    syncronizer.develop(gantt_project)


class Syncronizer:
    def __init__(self, sync_data=None):
        self.projects = None
        if not sync_data:
            sync_data = {
                            'projects': [], 'tasks': [],
                            'members': [], 'phases': []
                            }
        self.sync_data = sync_data

    def copy_project(self, project):
        self.project.append(project)
        self.sync_data['projects'].append(project.repository.init)
        if len(self.projects) > 1:
            self.deploy(project)

    def deploy(self, destination):

        for project in self.projects:
            if project != destination:
                origin = project
        if destination not in self.projects:
            self.projects.append(destination)

        for member in origin.members:
            new_member = destination.copy_member(member)
            self.sync_data['members'].append((member._id, new_member. _id))

        for phase in origin.phases:
            new_phase = destination.copy_phase(phase)
            self.sync_data['phases'].append((phase._id, new_phase._id))

        for task in origin.tasks:
            new_task = destination.copy_task(task)
            self.sync_data['tasks'].append((task._id, new_task._id))

        #Setting phases

