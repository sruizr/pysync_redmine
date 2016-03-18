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

        self.source = ET.parse(setup_pars['filename']).getroot()
        project_name = self.source.attrib['name']

        self.setup_pars = setup_pars
        if 'project_key' not in self.setup_pars:
            self.setup_pars['project_key'] = project_name

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

    def insert_member(self, member):
        resources = self.source.find('./resources')
        ids = [int(resource.attrib['id']) for resource in resources]
        new_id = 0
        if ids:
            new_id = max(ids) + 1

        function_name = list(member.roles)[0]
        roles = self.source.find("./roles")
        ids = [int(role.attrib['id']) for role in roles]
        new_role_id = 0
        if ids:
            new_role_id = max(ids) + 1

        role_id = None
        for role in roles[0]:
            if function_name == role.attrib['name']:
                role_id = int(role.attrib['id'])
                break

        if role_id is None:
            ET.SubElement(roles, 'role', {'id': str(new_role_id),
                                   'name': function_name})
            role_id = new_id

        attributes = {'id': str(new_id), 'name': member.key,
                                    'function': str(role_id)}
        ET.SubElement(resources, 'resource',
                               attributes)
        member._id = new_id

    def insert_phase(self, phase):
        new_id = self._get_new_task_id()
        duration = 0
        start_date = phase.due_date
        for task in phase.tasks:
            if task.start_date < start_date:
                start_date = task.start_date
        duration = self.project.calendar.get_duration(
                                                    start_date,
                                                    phase.due_date
                                                    )

        phase_name = '{}. {}'.format(phase.key, phase.description)

        attributes = {'id': str(new_id), 'name': phase_name,
                        'duration': str(duration), 'color': '#000000',
                        'meeting': 'false', 'start': start_date.isoformat(),
                        'complete': '0', 'expand': 'true'}
        tasks = self.source.find('./tasks')
        ET.SubElement(tasks, 'task', attributes)

        phase._id = new_id

    def insert_task(self, task):
        main_filter = './tasks'
        if task.phase:
            phase_filter = main_filter + '/task[@id="{}"]'.format(
                                                                task.phase._id)
        if task.parent:
            parent_filter = phase_filter + '//task[@id="{}"]'.format(
                                                            task.parent._id)
        parent = self.source.find(parent_filter)
        if not parent:
            raise ValueError

        new_id = self._get_new_task_id()
        attributes = {
                'id': str(new_id), 'name': task.description,
                'color': '#8cb6ce', 'meeting': 'false',
                'start': task.start_date.isoformat(),
                'duration': str(task.duration), 'complete': str(task.complete),
                'expand': 'true'
                        }
        ET.SubElement(parent, 'task', attributes)
        task._id = new_id

        if task.assigned_to:
            member = self.source.find('./resources/resource[@id="{}"]'.format(
                                                    task.assigned_to._id))
            function = member.attrib['function']

            allocations = self.source.find('./allocations')
            attributes = {
                                'task-id': str(task._id),
                                'resource-id': str(task.assigned_to._id),
                                'function': function, 'responsible': 'true',
                                'load': '100.0'
                                }
            ET.SubElement(allocations, 'allocation', attributes)

        # Updating durations of phases and parent tasks

    def update_task(self, task):

        fields = {}
        before_fields = task.snapshot
        after_fields = task.__dict__

        for key, value in after_fields.items():
            if before_fields[key] != value:
                fields[key] = value

        attributes = {}
        if fields:
            if 'description' in fields:
                attributes['name'] = fields['description']
            if 'start_date' in fields:
                attributes['start'] = fields['start_date'].isoformat()
            if 'duration' in fields:
                attributes['duration'] = str(fields['duration'])
            if 'complete' in fields:
                attributes['complete'] = str(fields['complete'])
            if '_parent' in fields or '_phase' in fields:
                self._move_task(task)
            if '_assigned_to' in fields:
                self._assign_task(task, True)
            if 'inputs' in fields:
                self._update_inputs(task)
                # To be done
            if 'outputs' in fields:
                self._update_outputs(task)

            task_element = self.source.find('./tasks//task[@id="{}"]'.format(
                                          task._id))
            for key, value in attributes.items():
                task_element.attrib[key] = value

        self._update_links(task)
        task._snap()

    def _assign_task(self, task, responsible):
        allocations = self.source.find('./allocations')
        updated = False
        responsible_value = 'true' if responsible else 'false'

        allocation_filter = './allocations/allocation[@task-id="{}"][@responsible="{}"]'.format(task._id, responsible_value)
        allocation = self.source.find(allocation_filter)

        if task.assigned_to is None:
            if allocation:
                allocations.remove(allocation)
        else:
            if allocation is None:
                attributes = {
                    'task-id': str(task._id),
                    'resource-id': str(task.assigned_to._id),
                    'function':'1',
                    'responsible': responsible_value
                    }
                ET.SubElement(allocations, 'allocation', attributes)
            else:
                allocation.attrib['resource-id'] = str(task.assigned_to._id)

    def _update_inputs(self, task):
        pass

    def _update_outputs(self, task):
        pass


    def _update_links(self, task):
        task_filter = './tasks//task[@id="{}"]'.format(task._id)
        task_element = self.source.find(task_filter)
        source_next_tasks = self.source.findall(
                           task_filter + '/depend'
                            )
        source_next_task = {
                        int(task.attrib['id']): int(task.attrib['difference'])
                        for task in source_next_tasks
                        }

        domain_next_tasks = task.relations.next_tasks

        for next_task, delay in domain_next_tasks.items():
            if next_task._id not in source_next_task:
                attributes = {
                                    'id': str(next_task._id), 'type': '2',
                                    'difference': str(delay),
                                    'hardness': 'Strong'
                                    }
                ET.SubElement(task_element, 'depend', attributes)
            elif delay != source_next_task[next_task._id]:
                depend = self.source.find(
                        task_filter+'/depend[@id="{}"]'.format(next_task._id)
                        )
                depend.attrib['difference'] = str(delay)

        domain_next_task_ids = [
                                    next_task._id
                                    for next_task in domain_next_tasks.keys()
                                            ]
        for next_task_id, delay in source_next_task.items():
            if next_task_id not in domain_next_task_ids:
                depend = self.source.find(
                        task_filter+'/depend[@id="{}"]'.format(next_task_id)
                        )
                task_element.remove(depend)

    def _get_new_task_id(self):
        tasks = self.source.findall('./tasks//task')
        ids = [int(task.attrib['id']) for task in tasks]

        new_id = 0
        if ids:
            new_id = max(ids) + 1
        return new_id

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
