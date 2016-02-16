import redmine
from redmine.exceptions import ResourceAttrError
from pysync_redmine.domain import (Repository,
                                   Project,
                                   Member,
                                   Task,
                                   Phase,
                                   Calendar,
                                   StringTree)
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

    def __init__(self):
        Repository.__init__(self)

    def open_source(self, project, **setup_pars):
        self.setup_pars = setup_pars
        self.project = project
        username = setup_pars.pop('username', None)
        psw = setup_pars.pop('password', None)

        if not username:
            username =input("Enter your redmine login name: ")
        if not psw:
            psw = getpass.getpass("Enter your password: ")

        self.source = redmine.Redmine(self.setup_pars['url'],
                                       username=username, password=psw)

    def load_tasks(self, project):
        issues = self.source.issue.filter(project_id=project._id)
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
        users = self.source.user.all()
        for member in project.memberships:
            user = users.get(member.user.id)
            project_roles = [r.name for r in member.roles]
            self._load_member(user, project_roles)

        self.members[user.id] = (user.login, roles)

    def load_phases(self):

        phase = Phase(self)
        version = ResourceWrapper(phase, 'version')
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

        if task.inputs or task.outputs:
            description = self._get_issue_description(task)
            fields['description'] = description
            print(description)


        issue = self.source.issue.create(**fields)
        task._id = issue.id

    def insert_phase(self, phase):
        pars = {
                'project_id': phase.project._id,
                'name': phase.key,
                'description': phase.description,
                'due_date': phase.due_date
                }

        version = self.source.version.create(**pars)
        phase._id = version.id

    def insert_member(self, member):
        user = self.source.user.filter(name=member.key)[0]
        roles = self.source.role.all()
        role_ids = []
        for role in roles:
                if role.name in member.roles:
                    role_ids.append(role.id)

        project_membership = self.source.project_membership.create(
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

        self.source.issue.update(resource_id, **fields)

        # Updating relations directly from repository

        relations = self.source.issue_relation.filter(issue_id=task._id)
        current_relations = {}
        tasks = task.project.tasks
        for relation in relations:
            if relation.relation_type == 'precedes':
                current_relations[tasks[relation.issue_to_id]] = relation

        for next_task, delay in task.relations.next_tasks.items():
            if next_task in current_relations:
                if delay != current_relations[next_task].delay:
                    self.source.issue_relation.delete(
                                               current_relations[next_task].id
                                               )
                    self.source.issue_relation.create(issue_id=task._id,
                                                       issue_to_id=next_task._id,
                                                       relation_type='precedes',
                                                       delay=delay)
            else:
                self.source.issue_relation.create(issue_id=task._id,
                                                   issue_to_id=next_task._id,
                                                   relation_type='precedes',
                                                   delay=delay)

        # delete task relation if no exist in self.project
        for next_task, relation in current_relations.items():
            if next_task not in task.relations.next_tasks:
                self.source.issue_relation.delete(relation.id)

    def update_member(self, member):
        pass

    def update_phase(self, phase):
        pass

    def _get_issue_description(self, task):
        description = ''
        if task.inputs:
            description += 'h3. Inputs\n\n'
            inputs = StringTree()
            for token in task.inputs:
                inputs.add_node(token.path()[1:])
            for document in inputs.childs:
                description += '* [[{}]]\n'.format(document.name)
                description += self._write_childs(document.childs, 2)

        if task.outputs:
            description += '\nh3. Outputs\n\n'
            outputs = StringTree()
            for token in task.outputs:
                outputs.add_node(token.path()[1:])
            for document in outputs.childs:
                description += '* [[{}]]\n'.format(document.name)
                description += self._write_childs(document.childs, 2)

        if description:
            description += '\n------'
        return description

    def _write_childs(self, childs, level):
        description = ''
        if childs:
            child_list = sorted(list(childs), key=lambda child: child.name)
            for child in child_list:
                description += '*'*level + ' ' + child.name + '\n'
                description += self._write_childs(child.childs, level+1)
        return description
