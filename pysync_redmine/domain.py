import datetime
from abc import ABCMeta, abstractmethod
import pdb


class StringTree:
    def __init__(self, name='/', parent=None):
        self._parent = None
        self.childs = set()

        # pdb.set_trace()
        if isinstance(name, str):
            name = [name]
        if len(name) == 1:
            self.name = name[0]
            self.parent = parent
        else:
            self.name = name[-1]
            self.parent = StringTree(name[0:-1], parent)

    @property
    def parent(self):
        return self._parent

    @property
    def root(self):
        parent = self.parent
        while parent.parent:
            parent = parent.parent

        return parent

    @parent.setter
    def parent(self, value):
        if self._parent:
            if self in self._parent.childs:
                self._parent.childs.remove(self)
        self._parent = value
        if value:
            value.childs.add(self)

    def add_node(self, path):
        if isinstance(path, str):
            path = [path]
        new_parent = self
        new_path = path.copy()
        for name in path:
            child = new_parent.find(name)
            if child:
                new_parent = child
                new_path.pop(0)
            else:
                break

        if new_path == []:
            return new_parent
        else:
            return StringTree(new_path, new_parent)

    def path(self, end_node=None):
        """Returns a list with the path till the current node,
        If end_node is a node the path is relative to this node."""
        if end_node == self:
            return []
        if self.parent is None or self.parent == end_node:
            return [self.name]
        else:
            full_path = self.parent.path(end_node)
            full_path.append(self.name)
            return full_path

    def find(self, name):
        """Find a child with a specific name, return None otherwise"""
        for child in self.childs:
            if child.name == name:
                return child

    def _str_level(self, level, identation='    '):
        result = identation*level
        result = result + ' ' + self.name + '\n'
        for child in self.childs:
            result += child._str_level(level+1, identation)
        return result

    def __str__(self):
        level = 0
        return self._str_level(level)


class Repository:

    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        self.project = None

    @abstractmethod
    def open_source(self, project, **kwargs):
        pass

    def close_source(self):
        if hasattr(self, 'source'):
            del self.source

    @abstractmethod
    def load_tasks(self, task): pass

    @abstractmethod
    def load_phases(self, phase): pass

    @abstractmethod
    def load_items(self, item, project): pass

    @abstractmethod
    def load_members(self, member): pass

    @abstractmethod
    def insert_task(self, task): pass

    @abstractmethod
    def insert_phase(self, phase): pass

    @abstractmethod
    def insert_item(self, item, project): pass

    @abstractmethod
    def insert_item(self, member): pass


class Project:

    def __init__(self, key, repository=None, calendar=None):
        self.key = key

        if calendar is None:
            calendar = Calendar()
        self.calendar = calendar

        self.repository = repository

        self.tasks = {}
        self.phases = {}
        self.members = {}
        self.tokens = StringTree()

    def load(self):
        if self.repository:
            self.repository.load_calendar()
            self.repository.load_members()
            self.repository.load_phases()
            self.repository.load_tasks()

    def save(self):
        for member in self.members:
            self.repository.save_member(member)
        for phase in self.phase():
            self.repository.save_phase(phase)
        for task in self.tasks:
            self.repository.save_task(task)


class Persistent:
    def __init__(self, project):
        self._id = None
        self.last_update = None
        self.snapshot = {}
        self.repository = project.repository
        self.project = project

    def _snap(self):
        self.snapshot = self.__dict__.copy()

    def save(self):
        class_name = self.__class__.__name__.lower()
        project = self.project
        repository = self.project.repository

        container = None
        if self.snapshot:
            method_name = 'update_{}'
            if self.snapshot == self.__dict__:  # No changes!
                return
        else:
            method_name = 'insert_{}'
            container_name = class_name + 's'
            container = getattr(project, container_name)

        method = getattr(repository, method_name.format(class_name))
        method(self)
        if container is not None:  # Inserted!
            container[self._id] = self

        self._snap()

    def copy(self, new_project):
        pass

    def remove(self):
        pass


class RelationSet:
    def __init__(self, from_task):
        self.from_task = from_task
        self.next_tasks = {}

    def add_next(self, next_task, delay=0):
        self.next_tasks[next_task] = delay


class Task(Persistent):

    def __init__(self, project, phase=None):
        super().__init__(project)
        self.description = None
        self.start_date = None
        self.duration = None
        self.complete = None
        self._assigned_to = None
        self._phase = None

        self._parent = None
        self.subtasks = []
        self.relations = RelationSet(self)
        self.inputs = []
        self.outputs = []
        self.colaborators = []

    @property
    def assigned_to(self):
        return self._assigned_to

    @assigned_to.setter
    def assigned_to(self, value):
        self._assigned_to = value
        value.tasks.append(self)

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, value):
        self._phase = value
        value.tasks.append(self)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value
        value.subtasks.append(self)

    def get_precedes(self):
        precedes = []
        for relation in self.relations:
            if relation.from_task == self:
                precedes.append(relation.to_task)
        return precedes

    def get_follows(self):
        follows = []
        for relation in self.relations:
            if relation.to_task == self:
                follows.append(relation.from_task)
        return follows

    def copy(self, project_destination):
        new_task = Task(project_destination)
        new_task.description = self.description
        new_task.start_date = self.start_date
        new_task.duration = self.duration
        new_task.complete = self.complete



        return new_task

    def __str__(self):

        result = """{}:{}
start date: {}
duration: {}
assigned to: {}""".format(
                                      self._id,
                                      self.description,
                                      self.start_date,
                                      self.duration,
                                      self.assigned_to.key
                                      )
        return result


class Milestone(Task):
    def __init__(self):
        super().__init__()


class Phase(Task):
    def __init__(self, project, key=None):
        super().__init__(project)
        self.key = key
        self.due_date = None
        self.tasks = []

    def copy(self, project_destination):
        new_phase = Phase(project_destination)
        new_phase.due_date = self.due_date
        new_phase.description = self.description
        new_phase.key = self.key

        return new_phase


class Member(Persistent):
    def __init__(self, project, key, *roles):
        super().__init__(project)
        self.key = key
        self.project = project
        if not roles:
            roles = []
        self.roles = set(roles)
        self.tasks = []

    def copy(self, project_destination):
        roles = self.roles.copy()
        new_member = Member(project_destination, self.key, *roles)

        return new_member


class Calendar(Persistent):
    def __init__(self, weekend=[6, 0]):
            self.weekend = weekend
            self.free_days = []

    def get_end_date(self, start_date, duration):
        end_date = start_date
        counter = 0
        while counter+1 < duration:
            end_date = end_date + datetime.timedelta(days=1)
            if (end_date.weekday() not in self.weekend and
                    end_date not in self.free_days):
                counter += 1

        return end_date

    def get_duration(self, start_date, end_date):
        if start_date is None or end_date is None:
            return None

        delta = end_date - start_date
        return delta.days

    def get_start_date(self, duration, end_date):
        pass
