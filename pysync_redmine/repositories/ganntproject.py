import datetime
import xml.etree.ElementTree as ET
from pysync_redmine.domain import (Repository,
                                   Project,
                                   Member,
                                   Task,
                                   Phase,
                                   Calendar,
                                   RelationSet)
import pdb


class GanttRepo(Repository):

    def __init__(self):
        Repository.__init__(self)

    def open_source(self, project, **setup_pars):
        self.project = project
        self.project.repository = self
        self.setup_pars = setup_pars
        self.setup_pars['project_key'] = project.key

        self.source = ET.parse(setup_pars['filename']).getroot()

    def load_members(self):
        project = self.project
        members = {}
        resources = self.source.findall('./resources/resource')
        functions = self.source.findall('./roles/role')
        for resource in resources:
            role = resource.attrib['function']
            for function in functions:
                if function.attrib['id'] == role:
                    role = function.attrib['name']
                    break
            member = Member(project, resource.attrib['name'], role)
            member._id = int(resource.attrib['id'])
            members[member._id] = member
            member._snap()

        project.members = members

    def load_calendar(self):
        self.project.calendar = Calendar()

    def load_phases(self):
        project = self.project
        phases = {}
        resources = self.source.findall('./tasks/task[task]')

        for resource in resources:
            phase = Phase(project)
            phase_id = int(resource.attrib['id'])
            phase._id = phase_id
            name = resource.attrib['name']
            key, description = name.split('. ')
            key = key.strip()
            description = description.strip()
            phase.key = key
            phase.description = description
            start_date = datetime.datetime.strptime(
                                                    resource.attrib['start'],
                                                    '%Y-%m-%d').date()
            phase.due_date = project.calendar.get_end_date(
                                               start_date,
                                               int(resource.attrib['duration'])
                                               )
            phases[phase_id] = phase
            phase._snap()

        project.phases = phases

    def load_tasks(self):
        project = self.project
        tasks = {}
        resources = self.source.findall('./tasks//task')
        for resource in resources:
            if int(resource.attrib['id']) not in project.phases:
                task = Task(project)
                task._id = int(resource.attrib['id'])
                task.description = resource.attrib['name']
                task.start_date = datetime.datetime.strptime(
                                                    resource.attrib['start'],
                                                    '%Y-%m-%d').date()
                task.duration = int(resource.attrib['duration'])
                task.complete = int(resource.attrib['complete'])
                tasks[task._id] = task
        project.tasks = tasks

        for resource in resources:
            if int(resource.attrib['id']) not in project.phases:
                task = project.tasks[int(resource.attrib['id'])]
                for child in resource:
                    if child.tag == 'task':
                        subtask = project.tasks[int(child.attrib['id'])]
                        subtask.parent = task
                    if child.tag == 'depend':
                        next_task = project.tasks[int(child.attrib['id'])]
                        task.relations.add_next(next_task, int(child.attrib['difference']))
                    # if child.tag == 'customproperty':
                    #     if child.attrib['taskproperty-id'] == self.input_id:
                    #         task.inputs = self._get_tokens(
                    #                                        child.attrib['value']
                    #                                        )
                    #     if child.attrib['taskproperty-id'] == self.output_id:
                    #         task.outputs = self._get_tokens(
                    #                                         child.attrib['value']
                    #                                         )

        resources = self.source.findall('./allocations/allocation')
        for resource in resources:
            task = project.tasks[int(resource.attrib['task-id'])]
            member = project.members[int(
                                         resource.attrib['resource-id']
                                                        )]
            task.assigned_to = member

        for phase in project.phases.values():
            resources = self.source.findall(
                                    "./tasks/task[@id='{}']//task".format(
                                                                    phase._id
                                                                    )
                                                        )
            for resource in resources:
                task = project.tasks[int(resource.attrib['id'])]
                task.phase = phase
                phase.tasks.append(task)

        for task in project.tasks.values():
            task._snap()

    def _get_tokens(self, token_string):
        tokens = token_string.split(',')
        result = []
        for token in tokens:
            token = token.strip()
            token = token.split('//')
            self.items.add(token[0])
            result.append(token)

        return result
