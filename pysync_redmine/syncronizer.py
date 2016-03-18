import pysync_redmine.repositories as base
from pysync_redmine.domain import (
                                    RelationSet,
                                    Task,
                                    Member,
                                    Phase
                                    )


class Syncronizer:

    def __init__(self, sync_data=None):
        self.projects = None
        if not sync_data:
            sync_data = {
                            'repositories': [], 'projects': [], 'tasks': [],
                            'members': [], 'phases': []
                            }
        self.sync_data = sync_data

    def load_repositories(self, sync_data):
        repositories = []
        for repo_info in sync_data['repositories']:
            repository = base.RepoFactory.create(repo_info['class_key'])
            repository.open_source(**repo_info['setup_pars'])
            repositories.append(repository)

        self.repositories = repositories

    def add_repository(self, repository):

        for repo_info in self.sync_data['repositories']:
            if (repo_info['setup_pars'] == repository.setup_pars) and (
                                repo_info['class_key'] == repository.class_key):
                return

        pars = {'class_key': repository.class_key, 'setup_pars': repository.setup_pars}
        self.sync_data['repositories'].append(pars)

    def add_redmine_project(self, url, username, password):
        repository = base.redmine.RedmineRepo()
        tokens = url.split('/')
        project_key = tokens.pop(-1)
        tokens.pop(-1)
        url = '/'.join(tokens)

        repository.open_source(
                               url=url,
                               project_key=project_key,
                               username=username,
                               password=password
                               )
        self.add_repository(repository)

    def add_ganttproject(self, filename):
        repository = base.ganttproject.GanttRepo()
        repository.open_source(filename=filename)

        self.add_repository(repository)

    def deploy(self, from_repo, to_repo):
        self.add_repository(from_repo)
        self.add_repository(to_repo)

        from_project = from_repo.project

        from_project.load()

        to_project = to_repo.project

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
            if task.outputs:
                for node in task.outputs:
                    new_node = to_project.tokens.add_node(node.path()[1:])
                    new_task.outputs.append(new_node)
            if task.inputs:
                for node in task.inputs:
                    new_node = to_project.tokens.add_node(node.path()[1:])
                    new_task.inputs.append(new_node)

            new_task.save()
            self.sync_data['tasks'].append((task._id, new_task._id))
        task_map = {
            value[0]: value[1] for value in self.sync_data['tasks']
            }

        for task in from_project.tasks.values():
            to_project_task = to_project.tasks[task_map[task._id]]

            if task.assigned_to:
                to_project_task.assigned_to = to_project.members[
                                                    member_map[
                                                        task.assigned_to._id
                                                        ]
                                                    ]
            if task.phase:
                to_project_task.phase = to_project.phases[
                                                    phase_map[
                                                        task.phase._id
                                                        ]
                                                    ]
            if task.parent:
                to_project_task.parent = to_project.tasks[
                                                    task_map[
                                                        task.parent._id
                                                        ]
                                                    ]

            to_project_task.save()

        # pdb.set_trace()
        # updating relations on next step, otherwise bug in redmine
        for task in from_project.tasks.values():
            to_project_task = to_project.tasks[task_map[task._id]]
            for next_task, delay in task.relations.next_tasks.items():
                dest_next_task = to_project.tasks[
                                                task_map[
                                                    next_task._id]
                                                ]
                to_project_task.relations.add_next(dest_next_task, delay)
            to_project_task.save()



