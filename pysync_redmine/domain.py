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
            self.repository.open_source()
            self.repository.load_calendar(self)
            self.repository.load_members(self)
            self.repository.load_phases(self)
            self.repository.load_tasks(self)
            self.repository.close_source()


class Persistent:
    def __init__(self, repository=None):
        self.snapshot = {}
        self.repository = repository

    def snap(self):
        self.snapshot = self.__dict__

    def save(self):
        self.repository.save(self)


class Task(Persistent):

    def __init__(self, project, phase=None):
        super().__init__()
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

    def __str__(self):

        result =
"""{}:{}
start date: {}
duration: {}
assigned to: {}""".format(
                                      self._id,
                                      self.description,
                                      self.start_date,
                                      self.duration,
                                      self.assigned_to.key
                                      )


class Milestone(Task):
    def __init__(self):
        super().__init__()


class Phase(Task):
    def __init__(self, project):
        super().__init__(project)
        self.due_date = None
        self.tasks = []


class Member(Persistent):
    def __init__(self, key, *roles):
        super().__init__()
        self.key = key
        if not roles:
            roles = []
        self.roles = set(roles)


class Calendar(Persistent):
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
