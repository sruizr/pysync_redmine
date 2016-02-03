import datetime
import pdb


class Project:

    def __init__(self, calendar=None):
        self.items = {}
        self.members = {}
        self.phases = {}
        if calendar is None:
            calendar = Calendar()
        self.calendar = calendar
        self.tasks = {}


class Task:

    def __init__(self, project):
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
        self.follows =[]

    def save(self):
        self.project._save_task(self)


class Milestone(Task):
    def __init__(self):
        Task.__init__(self)


class Phase(Task):
    def __init__(self, project):
        Task.__init__(self, project)
        self.due_date = None


class Resource:
    def __init__(self, key):
        self.key = key


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
