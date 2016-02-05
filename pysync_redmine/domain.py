import datetime
from abc import ABCMeta, abstractmethod
import pdb


class Repository:

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    def close_source(self):
        if hasattr(self, 'source'):
            del self.source

    @abstractmethod
    def open_project(self, **kwars): pass

    @abstractmethod
    def members(self, project): pass

    @abstractmethod
    def members(self, project): pass

    @abstractmethod
    def phases(self, project): pass

    @abstractmethod
    def tasks(self, project): pass

    @abstractmethod
    def items(self, project): pass

    @abstractmethod
    def project(self, key): pass

    @abstractmethod
    def save_task(self, task): pass

    @abstractmethod
    def save_phase(self, phase): pass

    @abstractmethod
    def save_item(self, item, project): pass


class Project:

    def __init__(self, key, repository=None):
        self.key = key
        self.repository = repository
        self.load()

    def load(self):
        if self.repository:
            self.repository.open_project(self.key)
            self.calendar = self.repository.calendar()
            self.members = self.repository.members()
            self.phases = self.repository.phases()
            self.tasks = self.repository.tasks()
            self.items = self.repository.items()
            self.repository.close_project(self.key)


class Task:

    def __init__(self, project, phase=None):
        self._id = None
        self.description = None
        self.project = project
        self.start_date = None
        self.duration = None
        self.complete = None
        self.assigned_to = None
        self.phase = None

        self.parent = None
        self.subtasks = []
        self.precedes = []
        self.follows = []
        self.inputs = []
        self.outputs = []

    def snap(self):
        self.snapshot = self.__dict__

    def save(self):
        self.project.repository.save_task(self)

    def __str__(self):
        return '{}: {}'.format(self._id, self.description)


class Milestone(Task):
    def __init__(self):
        Task.__init__(self)


class Phase(Task):
    def __init__(self, project):
        Task.__init__(self, project)
        self.due_date = None
        self.tasks = []


class Member:
    def __init__(self, key, *roles):
        self.key = key
        if not roles:
            roles = []
        self.roles = set(roles)


class Calendar:
    def __init__(self, weekend=['sat', 'sun']):
            self.weekend = weekend
            self.free_days = []

    def get_end_date(self, start_date, duration):
        pass

    def get_duration(self, start_date, end_date):
        if start_date is None or end_date is None:
            return None

        delta = end_date - start_date
        return delta.days

    def get_start_date(self, duration, end_date):
        pass
