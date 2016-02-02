import xml.etree.ElementTree as ET
from pysync_redmine.domain import (Project,
                                   Resource
                                   Calendar)


class GanttProject(Project):

    def __init__(self, file_name):
        Project.__init__(self)
        self.filename = file_name

    def _load_xml(self):
        return ET.parse(file_name).getroot()

    def load(self):
        root = self._load_xml()

        self._load_resources(root)
        self._load_calendar(root)
        self._load_phases(root)
        self._load_tasks(root)
        self._link_tasks(root)
        self._assign_tasks(root)

    def _load_phases(self, root):
        xml_phases = self.root.findall("./tasks/task[task]")

        phases = self.phases
        for xml_phase in xml_phases:
                phase = Phase()
                phase.id = int(xml_phase.attrib["id"])
                phase.description = xml_phase.attrib['name']
                phase.start_date = dt.datetime.strptime(
                                               xml_phase.attrib["start"],
                                               "%Y-%m-%d").date()
                phase.duration = int(xml_phase.attrib["duration"])
                phase.due_date = phase.start_date + \
                                            dt.timedelta(days=phase.duration)
                phases.append(phase)
                phase.complete = int(xml_phase.attrib["complete"])

    def _load_resources(self, root):
       # Loading resources
        xml_resources = root.findall('.//resource')
        for xml_resource in xml_resources:
            resource = Resource(xml_resource.attrib['name'])
            self.resources.append(resource)

    def _load_calendar(self, root):
        self.calendar = Calendar()

    def _load_tasks(self, root):
        pass

    def _load_task(self, element, parent=None):



class RedmineProject(Project):
    pass

