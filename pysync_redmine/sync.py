import json
import click
import pysync_redmine.repositories as repos
from pysync_redmine.domain import (
                                    SequenceRelation,
                                    Task,
                                    Member,
                                    Phase,
                                    )


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
            new_member = self.copy_member(member, destination)
            new_member.save()
            self.sync_data['members'].append((member._id, new_member. _id))
        member_map = {
                value[0]: value[1] for value in self.sync_data['members']
                }

        for phase in origin.phases:
            new_phase = self.copy_phase(phase, destination)
            new_phase.save()
            self.sync_data['phases'].append((phase._id, new_phase._id))
        phase_map = {
            value[0]: value[1] for value in self.sync_data['phases']
            }

        for task in origin.tasks:
            new_task = self.copy_task(task, destination)
            new_task.save()
            self.sync_data['tasks'].append((task._id, new_task._id))
        task_map = {
            value[0]. value[1] for value in self.sync_data['tasks']
            }

        for task in origin.tasks:
            destination_task = destination.tasks[task_map[task._id]]

            destination_task.assigned_to = destination.members[
                                                    member_map[
                                                        task.assigned_to._id
                                                        ]
                                                    ]
            destination_task.phase = destination.phases[
                                                    phase_map[
                                                        task.phase._id
                                                        ]
                                                    ]
            destination_task.parent = destination.tasks[
                                                    task_map[
                                                        task.parent._id
                                                        ]
                                                    ]
            for precede in task.get_precedes():
                SequenceRelation(destination.tasks[precede._id], destination_task)

            destination_task.save()

    def copy_task(self, task, project_destination):
        new_task = Task(project_destination)
        new_task.description = task.description
        new_task.start_date = task.start_date
        new_task.duration = task.duration
        new_task.complete = task.complete

        return new_task

    def copy_phase(self, phase, project_destination):
        new_phase = Phase(project_destination)
        new_phase.due_date = phase.due_date
        new_phase.description = phase.description
        new_phase.key = phase.key

        return new_phase

    def copy_member(self, member, project_destination):
        roles = member.roles.copy()
        new_member = Member(member.key, project_destination, *roles)

        return new_member


