
class Project:

    def __init__(self):
        self.resources = []
        self.phases = []
        self.calendar = []
        self.tasks = []


class Task:

    def __init__(self):
        self.id = None
        self.begin_date = None
        self.due_date = None
        self.duration = None
        self.complete = None
        self.assigned_to = None
        self.subtasks = []
        self.phase = None


class Milestone(Task):
    def __init__(self):
        Task.__init__(self)


class Phase(Task):
    def __init__(self):
        Task.__init__(self)


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
        pass

    def get_start_date(self, duration, end_date):
        pass
