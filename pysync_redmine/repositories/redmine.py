import redmine
from redmine.exceptions import ResourceAttrError
from pysync_redmine.domain import (Repository,
                                   Project,
                                   Member,
                                   Task,
                                   Phase,
                                   Calendar)
import getpass


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
        Project.__init__(self)

        if user_key is None:
            user_key = input("Enter your redmine user key:")
        if psw is None:
            psw = getpass.getpass("Enter your password:")

        paths = project_url.split('/')
        project_key = paths.pop(-1)
        url = '/'.join(paths[0:-1])
        self.redmine = redmine.Redmine(url, username=user_key, password=psw)

        self.project = self.redmine.project.get(project_key)
        self._id = project.id
        self.key = project_key
        self.description = project.name


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

    def open_source(self, )

    def load_tasks(self, issue):
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

    def load_phases(self, ):

        phase = Phase(self)
        version = ResourceWrapper(version, 'version')
        phase._id = version.id
        phase.description = "{}//{}".format(version.name, version.description)
        phase.due_date = version.due_date

        self.phases[phase._id] = phase

    def new_task(self):
        task = Task(self)
        return task

    def _save_task(self, task):
        if task._id is None:
                issue = redmine.issue.new()
        else:
                issue = redmine.issue.get(task._id)

        issue.project_id = self._id
        issue.subject = task.description
        issue.start_date = task.start_date
        issue.due_date = self.calendar.get_end_date(
                                                    task.start_date,
                                                    task.duration)

        issue.save()
        task._id = issue.id

    def get_task(self, id):
        if id not in self.tasks:
                issue = self.redmine.issue.get(id)
                task = self.new_task()
                task._id = issue.id
                task.description = issue.description
                task.start_date = issue.start_date
                task.duration = self.calendar.get_duration(
                                                           issue.start_date,
                                                           issue.due_date)
                task.complete = issue.done_ratio
                task.phase = self.get_phase(issue.fixed_version_id)
                self.tasks[id] = task
                task.parent = self.get_task(issue.parent_issue_id)
                self.subtasks.append(self.get_task(child.id))
                # if issue.relations:

        return self.tasks[id]

    def get_phase(self, id):
        if id not in self.phases:
            pass

    def copy_task(self, task):
        issue = self.redmine.issues.new()
        issue.subject = task.description
        issue.project_id = task.project._id
        issue.start_date = task.start_date
        issue.due_date = task.project.calendar.get_due_date(task.start_date,
                                                            task.duration)
        issue.done_ratio = task.complete
        issue.save()

        return self._get_task(issue, task.project)

    def _get_task(self, issue, project):
        task = Task(project)
        task._id = issue.id
        task.description = issue.

    def insert_task(self, task):
        issue = self.redmine.issue.new()
        issue.subject = task.description
        issue.project_id = task.project._id
        issue.start_date = task.start_date
        issue.due_date = task.project.calendar.get_due_date(task.start_date,
                                                            task.duration)
        issue.done_ratio = task.complete
        issue.save()

        task._id = issue.id

    def insert_phase(self, phase):
        version = self.redmine.version.new()
        version.project_id = phase.project.key
        version.name = phase.key
        version.description = phase.description
        version.due_date = phase.due_date
        version.save()

        phase._id = version.id

    def insert_member(self, member):
        user = self.redmine.user.filter(name=member.key)[0]
        roles = self.redmine.role.all()
        role_ids = []
        for role in roles:
                if role.name in member.roles:
                    role_ids.append(role.id)

        project_membership = self.redmine.project_membership.create(
                                                            member.project.key
                                                            user.id, role_ids)

        member._id = user.id

    def update_task(self, task):

        resource_id = task._id
        fields = {}

        if task.descriptoin != task.snapshot['description']:
            fields['subject'] = task.description

        if task.start_date != task.snapshot['start_date']:
            fields['start_date'] = task.start_date

        if (task.duration != task.snapshot['duration'] or
                task.start_date != task.snapshot['start_date']):
            fields['due_date'] = task.project.calendar.get_due_date(
                                                            task.start_date,
                                                            task.duration)

        if task.complete != task.snapshot['complete']:
            fields['done_ratio'] = task.complete

        if task.parent != task.snapshot['_parent']:
            fields['parent_issue_id'] = task.parent._id

        if (task.assigned_to != task.snapshot['assigned_to'] and
                task.assigned_to is not None):
            fields['assigned_to_id'] = task.assigned_to._id

        if (task.phase != task.snapshot['_phase'] and
            task.phase is not None):
            fields['fixed_version_id'] = task.phase,._id

        #Update relations
        relations = self.redmine.issue_relation.filter(issue_id=)
        if task.relations != task.snapshot['relations']:
            for relation in task.relations:
                if relation.from_task == task:
                    self.redmine.issue_relation.create(task._id,
                                                       relation.to_task._id,
                                                       'preceeds')

    def update_member(self, member):
        pass

    def update_phase(self, phase):
        pass

