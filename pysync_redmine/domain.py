import datetime
import pdb


class Project:

    def __init__(self, calendar=None):
        self.items = set()
        self.members = {}
        self.phases = {}
        if calendar is None:
            calendar = Calendar()
        self.calendar = calendar
        self.tasks = {}
        self._snapshot = {}


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
        self.project.save(self)
        self.snap()

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
