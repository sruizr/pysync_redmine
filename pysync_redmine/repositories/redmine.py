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
                                'assigned_to_id', "done_ratio", 'description'
                                ],
                    'version': ['due_date', 'desription', 'name', 'id']
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
        self.class_key = 'RedmineRepo'

    def open_source(self, **setup_pars):
        self.setup_pars = setup_pars
        self.project = Project(setup_pars["project_key"], self)

        username = setup_pars.pop('username', None)
        psw = setup_pars.pop('password', None)

        if username is None:
            username = input("Enter your redmine login name: ")
        if psw is None:
            psw = getpass.getpass("Enter your password: ")

        self.source = redmine.Redmine(self.setup_pars['url'],
                                      username=username, password=psw)

        red_project = self.source.project.get(self.project.key)
        self.project._id = red_project.id

    def load_calendar(self):
        self.project.calendar = Calendar()

    def load_tasks(self):
        issues = self.source.issue.filter(project_id=self.project._id)
        tasks = self.project.tasks
        for issue in issues:
            issue = ResourceWrapper(issue, "issue")
            task = Task(self.project)
            task._id = issue.id
            task.description = issue.subject
            task.start_date = issue.start_date
            task.duration = self.project.calendar.get_duration(issue.start_date,
                                                       issue.due_date)
            # pdb.set_trace()
            if issue.assigned_to_id is not None:
                task.assigned_to = self.project.members[issue.assigned_to_id]
            if issue.fixed_version_id is not None:
                task.phase = self.project.phases[issue.fixed_version_id]
            task.complete = issue.done_ratio
            tasks[task._id] = task

        for issue in issues:
            if issue.parent_issue_id is not None:
                tasks[issue.id].parent = tasks[issue.parent_issue_id]


            task._snap()

    def load_members(self):
        roles = self.source.role.all()
        member_ships = self.source.member_ship.filter(
                                                  project_id=self.project._id
                                                  )

        for member_ship in member_ships:
            user = self.source.user.get(member_ship.user_id)
            project_roles = [roles[r].name for r in member_ship.role_ids]
            member = Member(self.project, user.login, *project_roles)
            member._id = user.id
            self.project.members[member._id] = member

    def load_phases(self):
        versions = self.source.version.filter(project_id=self.project._id)
        for version in versions:
            phase = Phase(self.project)
            # pdb.set_trace()
            version = ResourceWrapper(version, 'version')
            phase._id = version.id
            phase.description = "{}. {}".format(
                                            version.name, version.description
                                            )
            phase.due_date = version.due_date
            self.project.phases[phase._id] = phase

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

        self.source.project_membership.create(
                                                project_id=member.project._id,
                                                user_id=user.id,
                                                role_ids=role_ids)

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

        if fields:  # pending test
            self.source.issue.update(resource_id, **fields)

        # Updating relations directly from repository
        self._update_relations(task)

    def update_member(self, member):
        pass

    def update_phase(self, phase):
        pass

    def _update_relations(self, task):

        current_relations = {}
        tasks = task.project.tasks

        relations = self.source.issue_relation.filter(issue_id=task._id)
        for relation in relations:
            if (relation.relation_type == 'precedes') and (
                                                relation.issue_id == task._id):
                current_relations[tasks[relation.issue_to_id]] = relation
            if (relation.relation_type == 'follows') and (
                                          relation.issue_to_id == task._id):
                current_relations[tasks[relation.issue_id]] = relation

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

        # delete task relation if no exist in self.project, bug it seems enter always..
        for next_task, relation in current_relations.items():
            if next_task not in task.relations.next_tasks:
                self.source.issue_relation.delete(relation.id)

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
