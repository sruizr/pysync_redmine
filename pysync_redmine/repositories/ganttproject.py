import datetime
import xml.etree.ElementTree as ET
from pysync_redmine.domain import (Repository,
                                   Project,
                                   Member,
                                   Task,
                                   Phase,
                                   Calendar,
                                   RelationSet,
                                   StringTree)
import pdb


class GanttRepo(Repository):

    def __init__(self):
        self.class_key = 'GanttRepo'
        Repository.__init__(self)

    def open_source(self, **setup_pars):

        self.setup_pars = setup_pars

        self.source = ET.parse(setup_pars['filename']).getroot()
        project_name = self.source.attrib['name']
        self.project = Project(project_name, self)

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

        input_id = self.source.findall('./tasks/taskproperties/taskproperty'
                                       '[@name="inputs"]')
        if input_id:
            input_id = input_id[0].attrib['id']
        output_id = self.source.findall('./tasks/taskproperties/taskproperty'
                                       '[@name="outputs"]')
        if output_id:
            output_id = output_id[0].attrib['id']

        for resource in resources:
            if int(resource.attrib['id']) not in project.phases:
                task = project.tasks[int(resource.attrib['id'])]
                for child in resource:
                    if child.tag == 'task':
                        subtask = project.tasks[int(child.attrib['id'])]
                        subtask.parent = task
                    if child.tag == 'depend':
                        next_task = project.tasks[int(child.attrib['id'])]
                        task.relations.add_next(next_task,
                                                int(child.attrib['difference'])
                                                )
                    if child.tag == 'customproperty':
                        if child.attrib['taskproperty-id'] == input_id:
                            task.inputs = self._get_tokens(
                                                           child.attrib['value']
                                                           )
                        if child.attrib['taskproperty-id'] == output_id:
                            task.outputs = self._get_tokens(
                                                            child.attrib['value']
                                                            )

        resources = self.source.findall('./allocations/allocation')
        for resource in resources:
            task_id = int(resource.attrib['task-id'])
            if task_id in project.tasks:
                task = project.tasks[task_id]
                member = project.members[int(
                                             resource.attrib['resource-id']
                                                            )]
                if resource.attrib['responsible'] == 'true':
                    task.assigned_to = member
                else:
                    task.colaborators.append(member)

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
            token = [e.strip() for e in token]
            token = self.project.tokens.add_node(token)
            result.append(token)

        return result
