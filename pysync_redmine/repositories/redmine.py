import redmine
from redmine.exceptions import ResourceAttrError
from pysync_redmine.domain import (Repository,
                                   Project,
                                   Member,
                                   Task,
                                   Phase,
                                   Calendar)
import getpass
import pdb


class ResourceWrapper:
    FIELDS = {
                    'issue': [
                                "due_date", "start_date",
                                'parent_issue_id', 'fixed_version_id',
                                'assigned_to_id'
                                ],
                    'version': ['due_date']
                    }

    def __init__(self, resource, type):
        self.fields = self.FIELDS[type]
        self.resource = resource

    def __getattr__(self, item):
        try:
            return self.resource.__getattr__(item)
        except ResourceAttrError:
            if item in self.fields:
                return None
            else:
                raise

    def __getitem__(self, item):
        return getattr(self, item)


class RedmineRepo(Repository):

    def __init__(self, project_url, user_key=None, psw=None):

        if user_key is None:
            user_key = input("Enter your redmine user key:")
        if psw is None:
            psw = getpass.getpass("Enter your password:")

        paths = project_url.split('/')
        project_key = paths.pop(-1)
        self.source = '/'.join(paths[0:-1])
        self.redmine = redmine.Redmine(self.source,
                                       username=user_key, password=psw)

        project = self.redmine.project.get(project_key)
        self.project = Project(project_key, self)
        self.project._id = project.id
        self.project.description = project.name

    def _to_be_removed(self):
        project = self.project
        for version in project.versions:
            self._load_phase(version)

        for issue in project.issues:
            self._load_task(issue)

        for issue in project.issues:
                for child in issue.children:
                    self.tasks[issue.id].subtasks.append(
                                                         self.tasks[child.id])
                    self.tasks[child.id].parent = self.tasks[issue.id]

        for issue in project.issues:
            for relation in issue.relations:
                    if relation.relation_type == 'precedes':
                        self.tasks[relation.issue_id].follows.append(
                                                                     self.tasks[relation.issue_to_id]
                                                                     )
                        self.tasks[relation.issue_to_id].precedes.append(
                                             self.tasks[relation.issue_id]
                                             )
        for task in self.tasks:
            task.snap()

        for phase in self.phases:
            phase.snap()

    def open_source(self):
        self.source = None

    def load_tasks(self, project):
        issues = self.redmine.issue.filter(project_id=project._id)
        for issue in issues:
            issue = ResourceWrapper(issue, "issue")
            task = self.new_task()
            task._id = issue.id
            task.description = issue.subject
            task.start_date = issue.start_date
            task.duration = self.calendar.get_duration(issue.start_date,
                                                       issue.due_date)
            if issue.assigned_to_id:
                task.assigned_to = self.members[issue.assigned_to_id]
            if issue.fixed_version_id:
                task.phase = self.phases[issue.fixed_version_id]
            task.complete = issue.done_ratio

            self.tasks[task._id] = task

    def load_members(self, user, roles):
        users = self.redmine.user.all()
        for member in project.memberships:
            user = users.get(member.user.id)
            project_roles = [r.name for r in member.roles]
            self._load_member(user, project_roles)

        self.members[user.id] = (user.login, roles)

    def load_phases(self ):

        phase = Phase(self)
        version = ResourceWrapper(version, 'version')
        phase._id = version.id
        phase.description = "{}//{}".format(version.name, version.description)
        phase.due_date = version.due_date

        self.phases[phase._id] = phase

    def insert_task(self, task):
        calendar = task.project.calendar
        fields = {
            'project_id': task.project._id,
            'subject': task.description,
            'start_date': task.start_date,
            'due_date': calendar.get_end_date(task.start_date,
                                              task.duration),
            'done_ratio': task.complete
        }

        issue = self.redmine.issue.create(**fields)
        task._id = issue.id

    def insert_phase(self, phase):
        pars = {
                'project_id': phase.project._id,
                'name': phase.key,
                'description': phase.description,
                'due_date': phase.due_date
                }

        version = self.redmine.version.create(**pars)
        phase._id = version.id

    def insert_member(self, member):
        user = self.redmine.user.filter(name=member.key)[0]
        roles = self.redmine.role.all()
        role_ids = []
        for role in roles:
                if role.name in member.roles:
                    role_ids.append(role.id)

        project_membership = self.redmine.project_membership.create(
                                                            project_id=member.project._id,
                                                            user_id=user.id,
                                                            roles_ids=role_ids)

        member._id = user.id

    def update_task(self, task):

        resource_id = task._id
        fields = {}

        if task.description != task.snapshot['description']:
            fields['subject'] = task.description

        if task.start_date != task.snapshot['start_date']:
            fields['start_date'] = task.start_date

        if (task.duration != task.snapshot['duration'] or
                task.start_date != task.snapshot['start_date']):
            fields['due_date'] = task.project.calendar.get_end_date(
                                                            task.start_date,
                                                            task.duration)

        if task.complete != task.snapshot['complete']:
            fields['done_ratio'] = task.complete

        if task.parent != task.snapshot['_parent']:
            fields['parent_issue_id'] = task.parent._id

        if (task.assigned_to != task.snapshot['_assigned_to'] and
                task.assigned_to is not None):
            fields['assigned_to_id'] = task.assigned_to._id

        if (task.phase != task.snapshot['_phase'] and
                task.phase is not None):
            fields['fixed_version_id'] = task.phase._id

        self.redmine.issue.update(resource_id, **fields)

        # Updating relations directly from repository

        relations = self.redmine.issue_relation.filter(issue_id=task._id)
        current_relations = {}
        tasks = task.project.tasks
        for relation in relations:
            if relation.relation_type == 'precedes':
                current_relations[tasks[relation.issue_to_id]] = relation

        for next_task, delay in task.relations.next_tasks.items():
            if next_task in current_relations:
                if delay != current_relations[next_task].delay:
                    self.redmine.issue_relation.delete(
                                               current.relations[next_task].id
                                               )
                    self.redmine.issue_relation.create(issue_id=task._id,
                                                       issue_to_id=next_task._id,
                                                       relation_type='precedes',
                                                       delay=delay)
            else:
                self.redmine.issue_relation.create(issue_id=task._id,
                                                   issue_to_id=next_task._id,
                                                   relation_type='precedes',
                                                   delay=delay)

        # pdb.set_trace()
        for relation in current_relations:
            if relation not in task.relations.next_tasks:
                self.redmine.issue_relation.delete(relation._id)

    def update_member(self, member):
        pass

    def update_phase(self, phase):
        pass

