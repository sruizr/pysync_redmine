import xml.etree.ElementTree as ET
from pysync_redmine.domain import (Project,
                                   Resource,
                                   Task,
                                   Phase,
                                   Calendar)
import redmine
from redmine.exceptions import ResourceAttrError
import pdb


class ResourceWrapper:
    FIELDS = {
    'issue': ["due_date", "start_date",
        "parent_issue_id", 'fixed_version_id', 'assigned_to_id'],
    'version': ['due_date']}

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

class GanttProject(Project):

    def __init__(self, file_name):
        Project.__init__(self)
        self.filename = file_name

    def _load_xml(self):
        return ET.parse(file_name).getroot()

    def load(self):
        root = self._load_xml()

        self._load_resources(root)
        self._load_calendar(root)
        self._load_phases(root)
        self._load_tasks(root)
        self._link_tasks(root)
        self._assign_tasks(root)

    def _load_phases(self, root):
        xml_phases = self.root.findall("./tasks/task[task]")

        phases = self.phases
        for xml_phase in xml_phases:
                phase = Phase()
                phase.id = int(xml_phase.attrib["id"])
                phase.description = xml_phase.attrib['name']
                phase.start_date = dt.datetime.strptime(
                                               xml_phase.attrib["start"],
                                               "%Y-%m-%d").date()
                phase.duration = int(xml_phase.attrib["duration"])
                phase.due_date = phase.start_date + \
                                            dt.timedelta(days=phase.duration)
                phases.append(phase)
                phase.complete = int(xml_phase.attrib["complete"])

    def _load_resources(self, root):
       # Loading resources
        xml_resources = root.findall('.//resource')
        for xml_resource in xml_resources:
            resource = Resource(xml_resource.attrib['name'])
            self.resources.append(resource)

    def _load_calendar(self, root):
        self.calendar = Calendar()

    def _load_tasks(self, root):
        pass

    def _load_task(self, element, parent=None):
        pass


class RedmineProject(Project):

    def __init__(self, project_url, user_key, psw):
        Project.__init__(self)

        paths = project_url.split('/')
        project_key = paths.pop(-1)
        url = '/'.join(paths[0:-1])
        self.redmine = redmine.Redmine(url, username=user_key, password=psw)

        project = self.redmine.project.get(project_key)
        self._id = project.id
        self.key = project_key
        self.description = project.name

        users = self.redmine.user.all()
        for member in project.memberships:
            user = users.get(member.user.id)
            project_roles = [r.name for r in member.roles]
            self._load_member(user, project_roles)

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

    def _load_task(self, issue):
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

    def _load_member(self, user, roles):
        self.members[user.id] = (user.login, roles)

    def _load_phase(self, version):
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

