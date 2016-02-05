import datetime
import xml.etree.ElementTree as ET
from pysync_redmine.domain import (Repository,
                                   Project,
                                   Member,
                                   Task,
                                   Phase,
                                   Calendar)


class GanttRepo(Repository):

    def __init__(self, file_name):
        Repository.__init__(self)
        self.filename = file_name

        self.load()

    def open_source(self, project_key):
        self.source = ET.parse(self.filename).getself.source()

    def project(self, project_key=None):
        if project_key:
            self.open_source(project_key)
        if not hasattr(self, 'project');

        return self.project

    def tasks(self):


    def load(self):
        input_property = self.source.find(
                                   "./tasks/taskproperties/"
                                   "taskproperty[@name='inputs']"
                                   )
        if input_property is not None:
            self.input_id = input_property.attrib['id']

        output_property = self.source.find(
                                    "./tasks/taskproperties/"
                                    "taskproperty[@name='outputs']"
                                    )
        if output_property is not None:
            self.output_id = input_property.attrib['id']


        calendar = self.source.find('./calendars')
        self._load_calendar(calendar)

        tasks = self.source.findall('.//task')
        for task in tasks:
            self._load_task(task)

        allocations = self.source.findall('./allocations/allocation')
        for allocation in allocations:
            self._load_assigned_to(allocation)

        phases = self.source.findall('./tasks/task[task]')
        for phase in phases:
            self._load_phase(phase)

        # link tasks
        tasks = self.source.findall('./tasks/task/task')
        for xml_task in tasks:
            self._update_links(xml_task)

    def members(self):

        members = {}
        resources = self.source.findall('./resources/resource')
        functions = self.source.findall('./roles/role')
        for resource in resources:
            role = resource.attrib['function']
            for function in functions:
                if function.attrib['id'] == role:
                    role = function.attrib['name']
                    break
            member = Member(resource.attrib['name'], role)
            members[int(resource.attrib['id'])] = member

        return members

    def calendar(self):
        return Calendar()

    def tasks(self):
        tasks = {}
        task = Task(self)
        task._id = int(xml_task.attrib['id'])
        task.description = xml_task.attrib['name']
        task.start_date = datetime.datetime.strptime(
                                                     xml_task.attrib['start'],
                                                     '%Y-%m-%d').date()
        task.duration = int(xml_task.attrib['duration'])
        task.complete = int(xml_task.attrib['complete'])

        self.tasks[task._id] = task

        return tasks

    def _load_assigned_to(self, xml_allocation):
        task = self.tasks[int(xml_allocation.attrib['task-id'])]
        member = self.members[int(xml_allocation.attrib['resource-id'])]
        task.assigned_to = member

    def _load_phase(self, xml_phase):
        phase_id = int(xml_phase.attrib['id'])
        phase = self.tasks.pop(phase_id)
        self.phases[phase_id] = phase

        self._update_phase(phase, xml_phase)

    def _update_phase(self, phase, xml):
        for child in xml:
            if child.tag == 'task':
                task = self.tasks[int(child.attrib['id'])]
                task.phase = phase
                self._update_phase(phase, child)

    def _update_links(self, xml):
        task = self.tasks[int(xml.attrib['id'])]
        for child in xml:
            if child.tag == 'task':
                subtask = self.tasks[int(child.attrib['id'])]
                subtask.parent = task
                task.subtasks.append(subtask)
                self._update_links(child)
            if child.tag == 'depend':
                next_task = self.tasks[int(child.attrib['id'])]
                next_task.follows.append(task)
                task.precedes.append(next_task)
            if child.tag == 'customproperty':
                if child.attrib['taskproperty-id'] == self.input_id:
                    task.inputs = self._get_tokens(child.attrib['value'])
                if child.attrib['taskproperty-id'] == self.output_id:
                    task.outputs = self._get_tokens(child.attrib['value'])

    def _get_tokens(self, token_string):
        tokens = token_string.split(',')
        result = []
        for token in tokens:
            token = token.strip()
            token = token.split('//')
            self.items.add(token[0])
            result.append(token)

        return result
