from unittest.mock import Mock
from pysync_redmine.repositories.redmine import RedmineRepo
from pysync_redmine.domain import (
                                   Project,
                                   Task,
                                   Phase,
                                   Member,
                                   Calendar,
                                   StringTree
                                   )
from xml.etree import ElementTree as ET
from datetime import date


def load_project_base(project):
        mock_repository = Mock()
        project.repository = mock_repository
        load_phases_for_testing(project)
        load_members_for_testing(project)
        load_tasks_for_testing(project)
        load_relations_for_testing(project)
        load_tokens_for_testing(project)


def load_phases_for_testing(project):
        phase = Phase(project)
        phase.description = 'PHA. Phase description'
        phase.due_date = date(2016, 2, 15)
        phase._id = 0
        project.phases[phase._id] = phase
        phase._snap()


def load_members_for_testing(project):
        member_names = ['A_project_leader', 'A_developer', 'A_verifier']
        roles = ['Project Leader', 'Developer', 'Verifier']
        for i in range(0, 3):
            member = Member(project, member_names[i], roles[i])
            member._id = i
            member.project.members[i] = member
            member._snap()

def load_tasks_for_testing(project):
        task_descriptions = ['Task with subtasks', 'Subtask 1', 'Subtask 2',
                    'Task without subtasks', 'Milestone', 'Task without phase']
        start_dates = [date(2016, 2, 3), date(2016, 2, 3), date(2016, 2, 10),
                        date(2016, 2, 15), date(2016, 2, 16), date(2016, 2, 1)]
        durations = [8, 5, 3, 1, 0, 2]
        completes = [61, 69, 50, 0, 0, 100]

        for i in range(0, 6):
                task = Task(project)
                task.description = task_descriptions[i]
                task.start_date = start_dates[i]
                task.duration = durations[i]
                task.complete = completes[i]
                task._id = i + 1
                task.save()

        tasks = project.tasks
        for i in range(1, 5):
            tasks[i].phase = project.phases[0]

        tasks[2].parent = tasks[1]
        tasks[3].parent = tasks[1]

        members = project.members
        for i in range(1, 4):
            tasks[i].assigned_to_id = members[i-1]

        for i in range(1, 7):
          tasks[i].save()

def load_tokens_for_testing(project):
    tokens = project.tokens
    tasks = project.tasks

    token = tokens.add_node([1, 2, 3])
    tasks[3].inputs.append(token)

    token = tokens.add_node([1, 2, 4])
    tasks[3].inputs.append(token)

    token = tokens.add_node([1, 5])
    tasks[3].outputs.append(token)

    token = tokens.add_node([6])
    tasks[3].outputs.append(token)


def load_relations_for_testing(project):
    tasks = project.tasks
    tasks[6].relations.add_next(tasks[1])
    tasks[2].relations.add_next(tasks[3])
    tasks[3].relations.add_next(tasks[4])
    tasks[4].relations.add_next(tasks[5])


def get_issue_description():
        description = """h3. Inputs

* [[1]]
** 2
*** 3
*** 4

h3. Outputs

* [[1]]
** 5
* [[6]]

------"""
        return description


def get_mock_source_redmine():
    redmine = Mock()

    project = Mock()
    project.identifier = 'example'
    project.id = 1
    redmine.project.get.return_value = project

    roles = [Mock(id=i) for i in range(0, 3)]
    names = ['Project manager', 'Developer', 'Verifier']
    for i in range(0, 3):
        roles[i].name = names[i]
    redmine.role.all.return_value = roles

    members = [Mock(id=i) for i in range(0, 2)]
    role_ids = [1, 2]
    user_ids = [0, 1]
    for member in members:
        member.user_id = user_ids[member.id]
        member.role_ids = [role_ids[member.id]]
    redmine.member_ship.filter.return_value = members

    users = [Mock(id=i) for i in range(0, 3)]
    logins = ['A_project_leader', 'A_developer', 'A_verifier']
    for user in users:
        user.login = logins[user.id]
    redmine.user.get.side_effect = lambda x: users[x]

    version = Mock()
    version.id = 0
    version.name = "PHA"
    version.description = "Phase description"
    version.due_date = date(2016, 2, 15)
    redmine.version.filter.return_value = [version]

    parent_issue = Mock(id=1, subject='Task with subtasks',
                        start_date=date(2016, 2, 3),
                        due_date=date(2016, 2, 12),
                        assigned_to_id=0,
                        done_ratio=12,
                        description='No parsed description',
                        parent_issue_id=None, fixed_version_id=0)
    sub_issue1 = Mock(id=2, subject='Subtask 1',
                     start_date=date(2016, 2, 3),
                     due_date=date(2016, 2, 9),
                     assigned_to_id=1,
                     done_ratio=12,
                     description=get_issue_description(),
                     parent_issue_id=1, fixed_version_id=0)
    sub_issue2 = Mock(id=3, subject='Subtask 2',
                     start_date=date(2016, 2, 10),
                     due_date=date(2016, 2, 12),
                     assigned_to_id=1,
                     done_ratio=12,
                     description=get_issue_description(),
                     parent_issue_id=1, fixed_version_id=0)
    alone_task = Mock(id=4, subject='Task without subtasks',
                            start_date=date(2016, 2, 15),
                            due_date=date(2016, 2, 15),
                            assigned_to_id=None,
                            done_ratio=12,
                            description=None,
                            parent_issue_id=None, fixed_version_id=0)
    milestone = Mock(id=5, subject='Milestone',
                            start_date=date(2016, 2, 16),
                            due_date=date(2016, 2, 16),
                            assigned_to_id=None,
                            done_ratio=0,
                            description=None,
                            parent_issue_id=None, fixed_version_id=0)
    orphan = Mock(id=6, subject='Task without phase',
                            start_date=date(2016, 2, 1),
                            due_date=date(2016, 2, 2),
                            assigned_to_id=None,
                            done_ratio=100,
                            description=None,
                            parent_issue_id=None, fixed_version_id=None)
    redmine.issue.filter.return_value = [parent_issue, sub_issue1,
                                sub_issue2, milestone, orphan, alone_task]

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
    ET.SubElement(resources, 'resource', {'id': '0', 'name': 'A_project_leader',
                  'function': '1'})
    ET.SubElement(resources, 'resource', {'id': '1', 'name': 'A_developer',
                  'function': '2'})
    ET.SubElement(resources, 'resource', {'id': '2', 'name': 'A_verifier',
                  'function': '3'})

    tasks = ET.SubElement(source, 'tasks')
    taskproperties = ET.SubElement(tasks, 'taskproperties')
    ET.SubElement(taskproperties, 'taskproperty',
                            {'id': 'tpc0', 'name': 'inputs'})
    ET.SubElement(taskproperties, 'taskproperty',
                            {'id': 'tpc1', 'name': 'outputs'})

    phase = ET.SubElement(tasks, 'task', {'id': '0', 'name': 'PHA. Phase description',
                   'start': '2016-02-03', 'duration': '9', 'complete': '48'})
    parent = ET.SubElement(phase, 'task', {'id': '1', 'name': 'Task with subtasks',
                   'start': '2016-02-03', 'duration': '8', 'complete': '61'})
    subtask1 = ET.SubElement(parent, 'task', {'id': '2', 'name': 'Subtask 1',
                   'start': '2016-02-03', 'duration': '5', 'complete': '69'})
    subtask2 = ET.SubElement(parent, 'task', {'id': '3', 'name': 'Subtask 2',
                   'start': '2016-02-10', 'duration': '3', 'complete': '50'})
    alone_task = ET.SubElement(phase, 'task', {'id': '4',
                       'name': 'Task without subtasks', 'start': '2016-02-15',
                       'duration': '1', 'complete': '0'})
    milestone = ET.SubElement(tasks, 'task', {'id': '5', 'name': 'Milestone',
                              'start': '2016-02-16',
                              'duration': '0', 'complete': '48',
                              'meeting': True})
    orphan_task = ET.SubElement(tasks, 'task', {'id': '6', 'name': 'Task without phase',
                          'start': '2016-02-01', 'duration': '2', 'complete': '100'})

    #  Relations
    ET.SubElement(subtask1, 'depend', {'id': '3', 'difference': '0', 'type': '2', 'hardness': 'Strong'})
    ET.SubElement(subtask2, 'depend', {'id': '4', 'difference': '0', 'type': '2', 'hardness': 'Strong'})
    ET.SubElement(alone_task, 'depend', {'id': '5', 'difference': '0', 'type': '2', 'hardness': 'Strong'})
    ET.SubElement(orphan_task, 'depend', {'id': '1', 'difference': '0', 'type': '2', 'hardness': 'Strong'})

    inputs = '1//2//3, 1//2//4'
    outputs = '1//5, 6'
    ET.SubElement(subtask2, 'customproperty',
                  {'taskproperty-id': 'tpc0', 'value': inputs})
    ET.SubElement(subtask2, 'customproperty',
                  {'taskproperty-id': 'tpc1', 'value': outputs})

    allocations = ET.SubElement(source, 'allocations')
    ET.SubElement(allocations, 'allocation', {
                  'task-id': '1', 'resource-id': '0', 'function': '1',
                  'responsible': 'true'})
    ET.SubElement(allocations, 'allocation', {
                  'task-id': '2', 'resource-id': '1', 'function': '3',
                  'responsible': 'true'})
    ET.SubElement(allocations, 'allocation', {
                  'task-id': '3', 'resource-id': '2', 'function': '2',
                  'responsible': 'true'})
    ET.SubElement(allocations, 'allocation', {
                  'task-id': '3', 'resource-id': '1', 'function': '2',
                  'responsible': 'false'})

    return source
