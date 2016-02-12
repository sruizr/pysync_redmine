import json
import click
import pysync_redmine.repositories as repos
from pysync_redmine.domain import (
                                    RelationSet,
                                    Task,
                                    Member,
                                    Phase,
                                    )
import pdb

@click.command()
@click.option('--file', prompt='Enter path of project file',
              help='Filename of GanntProject')
@click.option('--project', prompt='Enter the URL of your project',
              help='URL of project at Redmine')
@click.option('--user', prompt='Enter your user login at Redmine',
              help='User key how is goint to update system to Redmine')
@click.option('--password', prompt='Enter your password', hide_input=True)
def gantt_to_redmine(filename, project_url, user_key, psw):
    redmine = repos.redmine.RedmineRepo(project_url, user_key, psw)
    gantt = repos.ganntproject.GanttRepo(filename)

    redmine.open_source()
    gantt.open_source()

    redmine_project = redmine.project
    gantt_project = gantt.project

    syncronizer = Syncronizer()

    syncronizer.deploy(redmine_project, gantt_project)

    data_name = '{}.json'.format(gantt_project.key)
    with open(data_name, 'w') as outfile:
        json.dump(syncronizer.sync_data, outfile)


@click.command()
@click.option('--sync_file', prompt='Enter your sync_file to load:', help=
              'Filename .json with sync data')
def sync_projects(sync_data_file):
    pass


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

    def deploy(self, from_repo, to_repo):

        from_project = from_repo.project
        to_project = to_repo.project

        from_repo.open_source()
        from_repo.load_project('project_key')
        from_repo.close_source()

        to_repo.open_source()

        for member in from_project.members.values():
            new_member = member.copy(to_project)
            new_member.save()
            self.sync_data['members'].append((member._id, new_member. _id))
        member_map = {
                value[0]: value[1] for value in self.sync_data['members']
                }

        for phase in from_project.phases.values():
            new_phase = phase.copy(to_project)
            new_phase.save()
            self.sync_data['phases'].append((phase._id, new_phase._id))
        phase_map = {
            value[0]: value[1] for value in self.sync_data['phases']
            }

        for task in from_project.tasks.values():
            new_task = task.copy(to_project)
            new_task.save()
            self.sync_data['tasks'].append((task._id, new_task._id))
        task_map = {
            value[0]: value[1] for value in self.sync_data['tasks']
            }

        pdb.set_trace()
        for task in from_project.tasks.values():
            to_project_task = to_project.tasks[task_map[task._id]]

            to_project_task.assigned_to = to_project.members[
                                                    member_map[
                                                        task.assigned_to._id
                                                        ]
                                                    ]
            to_project_task.phase = to_project.phases[
                                                    phase_map[
                                                        task.phase._id
                                                        ]
                                                    ]
            to_project_task.parent = to_project.tasks[
                                                    task_map[
                                                        task.parent._id
                                                        ]
                                                    ]
            for next_task, delay in task.nexts:
                dest_next_task = to_project.tasks[
                                                task_map[
                                                    next_task._id]
                                                ]
                to_project_task.relations.add_next(dest_next_task, delay)

            to_project_task.save()

        to_repo.close_source()

