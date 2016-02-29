from unittest.mock import Mock
from pysync_redmine.repositories.redmine import RedmineRepo
from pysync_redmine.domain import (
                                   Project,
                                   Task,
                                   Phase,
                                   Member,
                                   Calendar
                                   )
from xml.etree import ElementTree as ET
import datetime


def get_project_frame(project):
        mock_repository = Mock()
        project.repository = mock_repository

        phase = Phase(project)
        phase.description = 'PHA. Phase description'
        phase.due_date = datetime.date(2016, 2, 15)
        phase._id = 2
        phase.save()

        member = Member(project, 'member_key')
        member.user = 'user_'
        member._id = 0
        member.save()

        main_task = Task(project)
        main_task.description = 'Initial description'
        main_task.start_date = datetime.date(2016, 1, 4)
        main_task.duration = 2
        main_task.complete = 75
        main_task._id = 1
        main_task.save()

        parent = Task(project)
        parent.description = 'parent description'
        parent.start_date = datetime.date(2016, 1, 4)
        parent.duration = 1
        parent.complete = 100
        parent._id = 2
        parent.save()

        next_task = Task(project)
        next_task.description = 'next_task description'
        next_task.start_date = datetime.date(2016, 1, 4)
        next_task.duration = 1
        next_task.complete = 100
        next_task._id = 3
        next_task.save()

        return (phase, member, parent, main_task, next_task)


def get_issue_description():
        description = """h3. Inputs

* [[1]]
** 2
*** 3
*** 4

h3. Outputs

* [[1]]
** 5
** 6

------"""
        return description


def get_mock_source_redmine():
    redmine = Mock()

    project = Mock()
    project.identifier = 'example'
    project.id = 1
    redmine.project.get.return_value = project

    roles = [Mock(id=i) for i in range(0, 3)]
    names = ['Project manager', 'Developer', 'Tester']
    for i in range(0,3):
        roles[i].name = names[i]
    redmine.role.all.return_value = roles

    members = [Mock(id=i) for i in range(0, 2)]
    role_ids = [1, 2]
    user_ids = [0, 1]
    for member in members:
        member.user_id = user_ids[member.id]
        member.role_ids = role_ids
    redmine.member_ship.filter.return_value = members

    users = [Mock(id=i) for i in range(0, 2)]
    logins = ['leader', 'worker']
    for user in users:
        user.login = logins[user.id]
    redmine.user.get.side_effect = lambda x: users[x]

    version = Mock()
    version.project_id = 1
    version.name = "PHA"
    version.description = "Phase description"
    version.due_date = datetime.date(2016, 2, 15)
    redmine.version.filter.return_value = [version]

    parent_issue = Mock(id=1, subject='Parent task',
                        start_date=datetime.date(2016, 2, 15),
                        due_date=datetime.date(2015, 2, 23),
                        assigned_to=0,
                        description='No parsed description',
                        parent_issue_id=None, fixed_version_id=1)
    sub_issue = Mock(id=2, subject='Sub task',
                     start_date=datetime.date(2016, 2, 15),
                     due_date=datetime.date(2015, 2, 20),
                     assigned_to=1,
                     description=get_issue_description(),
                     parent_issue_id=1, fixed_version_id=1)
    alone_task = Mock(id=3, subject='Task without phase',
                       start_date=datetime.date(2016, 2, 21),
                       due_date=datetime.date(2015, 2, 21),
                       assigned_to=None,
                       description=None,
                       parent_issue_id=None, fixed_version_id=None)
    redmine.issue.filter.return_value = [parent_issue, sub_issue, alone_task]

    relation = Mock(issue_id=1, issue_to_id=3, relation_type='precedes',
                    delay=1)
    redmine.relation.filter.return_value = [relation]

    return redmine


def get_mock_source_gantt():
    source = ET.Element('project', {'name': 'example'})

    roles = ET.SubElement(source, 'roles')
    ET.SubElement(roles, 'role', {'id': '1', 'name': 'Project Leader'})
    ET.SubElement(roles, 'role', {'id': '2', 'name': 'Developer'})
    ET.SubElement(roles, 'role', {'id': '3', 'name': 'Verifier'})

    resources = ET.SubElement(source, 'resources')
    ET.SubElement(resources, 'resource', {'id': '0', 'name': 'leader',
                  'function': '1'})
    ET.SubElement(resources, 'resource', {'id': '1', 'name': 'developer',
                  'function': '2'})
    ET.SubElement(resources, 'resource', {'id': '2', 'name': 'verifier',
                  'function': '3'})
    ET.SubElement(resources, 'resource', {'id': '3', 'name': 'none',
                  'function': '0'})

    tasks = ET.SubElement(source, 'tasks')
    phase = ET.SubElement(tasks, 'task', {'id': '0', 'name': 'ABC. Phase description',
                          'start': '2016-01-04', 'duration': '8', 'complete': '87'})
    parent = ET.SubElement(phase, 'task', {'id': '1', 'name': 'Parent task',
                           'start': '2016-01-04', 'duration': '3', 'complete': '87'})
    subtask = ET.SubElement(parent, 'task', {'id': '2', 'name': 'subtask task',
                           'start': '2016-01-04', 'duration': '3', 'complete': '90'})
    ET.SubElement(subtask, 'depend', {'id': '3', 'difference': '5'})
    ET.SubElement(subtask, 'custom')
    alone = ET.SubElement(tasks, 'task', {'id': '3', 'name': 'Task without phase',
                           'start': '2016-01-04', 'duration': '3', 'complete': '100'})

    inputs = 'one item // with section, alone item'
    outputs = 'one item // with //several sections, alone item'
    ET.SubElement(alone, 'customproperty',
                  {'taskproperty-id': 'tpc0', 'value': inputs})
    ET.SubElement(alone, 'customproperty',
                  {'taskproperty-id': 'tpc1', 'value': outputs})

    allocations = ET.SubElement(source, 'allocations')
    ET.SubElement(allocations, 'allocation', {
                  'task-id': '1', 'resource-id': '0', 'function': '1',
                  'responsible': 'true'})
    ET.SubElement(allocations, 'allocation', {
                  'task-id': '2', 'resource-id': '1', 'function': '3',
                  'responsible': 'true'})
    ET.SubElement(allocations, 'allocation', {
                  'task-id': '2', 'resource-id': '2', 'function': '2',
                  'responsible': 'false'})

    taskproperties = ET.SubElement(tasks, 'taskproperties')
    ET.SubElement(taskproperties, 'taskproperty',
                    {'id': 'tpc0', 'name': 'inputs'})
    ET.SubElement(taskproperties, 'taskproperty',
                    {'id': 'tpc1', 'name': 'outputs'})

    return source
