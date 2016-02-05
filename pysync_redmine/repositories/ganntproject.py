import datetime
import xml.etree.ElementTree as ET
from pysync_redmine.domain import (Repository,
                                   Project,
                                   Member,
                                   Task,
                                   Phase,
                                   Calendar)


class GanttRepo(Repository):

    def __init__(self, filename=None):
        Repository.__init__(self)
        if filename:
            self.open_source(filename)

    def open_source(self, filename):
        self.source = ET.parse(filename).getself.source()

    def load_members(self, project):
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
            member.snap()

        return members

    def load_calendar(self, project):
        return Calendar()

    def load_phases(self, project):
        project.phases = {}
        resources = self.source.findall('./tasks/task[task]')

        for resource in resources:
            phase = Phase(project)
            phase_id = int(resource.attrib['id'])
            phase._id = phase_id
            phase.description = resource.attrib['name']
            start_date = datetime.datetime.strptime(
                                                    resource.attrib['start'],
                                                    '%Y-%m-%d').date()
            phase.due_date = project.calendar.get_end_date(
                                               start_date,
                                               int(resource.attrib['duration'])
                                               )
            project.phases[phase_id] = phase
            phase.snap()

    def load_tasks(self, project):
        project.tasks = {}
        resources = self.source.findall('./tasks//task')
        for resource in resources:
            if int(resource.attrib['id']) not in self.project.phases:
                task = Task(self)
                task._id = int(resource.attrib['id'])
                task.description = resource.attrib['name']
                task.start_date = datetime.datetime.strptime(
                                                    resource.attrib['start'],
                                                    '%Y-%m-%d').date()
                task.duration = int(resource.attrib['duration'])
                task.complete = int(resource.attrib['complete'])
                project.tasks[task_id] = task_id

        for resources in resource:
            if int(resource.attrib['id']) not in self.project.phases:
                task = project.tasks[int(resource.attrib['id'])]
                for child in resource:
                    if child.tag == 'task':
                        subtask = self.tasks[int(child.attrib['id'])]
                        subtask.parent = task
                        task.subtasks.append(subtask)
                    if child.tag == 'depend':
                        next_task = self.tasks[int(child.attrib['id'])]
                        next_task.follows.append(task)
                    if child.tag == 'customproperty':
                        if child.attrib['taskproperty-id'] == self.input_id:
                            task.inputs = self._get_tokens(
                                                           child.attrib['value']
                                                           )
                        if child.attrib['taskproperty-id'] == self.output_id:
                            task.outputs = self._get_tokens(
                                                            child.attrib['value']
                                                            )

        resources = self.source.findall('./allocations/allocation')
        for resource in resources:
            task = project.tasks[int(xml_allocation.attrib['task-id'])]
            member = project.members[int(
                                         xml_allocation.attrib['resource-id']
                                         )]
            task.assigned_to = member

        for phase in project.phases:
            resources = self.source.findall(
                                    "./tasks/task[@id='{}]'//task".format(
                                                                          phase._id
                                                                          )
                                    )
            for resource in resources:
                task = projects.tasks[int(resource.attrib['id'])]
                task.phase = phase
                phase.tasks.append(task)

        for task in project.tasks:
            task.snap()

    def _get_tokens(self, token_string):
        tokens = token_string.split(',')
        result = []
        for token in tokens:
            token = token.strip()
            token = token.split('//')
            self.items.add(token[0])
            result.append(token)

        return result

