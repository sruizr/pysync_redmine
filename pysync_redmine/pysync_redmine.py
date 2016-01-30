import xml.etree.ElementTree as ET
import datetime as dt



class Project:
    pass


class Task:

    def __init__(self):
        self.id = None
        self.begin_date = None
        self.due_date = None
        self.duration = None
        self.complete = None
        self.assigned_to = None


class Phase(Task):
    def __init__(self):
        Task.__init__(self)
        Tasks = []


class GanttProjectLoader:

    def __init__(self, file_name):
        self.root = ET.parse(file_name).getroot()

    def get_phases(self):
        xml_phases = self.root.findall("./tasks/task[task]")

        phases = []
        for xml_phase in xml_phases:
                phase = Phase()
                phase.id = int(xml_phase.attrib["id"])
                phase.description = xml_phase.attrib['name']
                phase.begin_date = dt.datetime.strptime(
                                               xml_phase.attrib["start"],
                                               "%Y-%m-%d")
                phase.duration = int(xml_phase.attrib["duration"])
                phase.due_date = phase.begin_date + \
                                            dt.timedelta(days=phase.duration)
                phases.append(phase)
                phase.complete = int(xml_phase.attrib["complete"])

        return phases


