import getpass
import click
from pysync_redmine import (RedmineProject,
                                         GanntProject)


class Sycronizer:
    def __init__(self, repository_1, repository_2):
        pass


@click.command()
@click.option('--project', prompt='Enter the URL of your project',
              help='URL of project at Redmine')
@click.option('--user', prompt='Enter your user key at Redmine',
              help='User key how is goint to update system to Redmine')
@click.option('--file', prompt='Enter path of project file',
              help='Filename of GanntProject')
def run(project_url, user_key, filename):


    # Redmine repository
    psw = getpass.getpass("Enter password for redmine:")
    repository_1 = RedmineProject(project_url, user_key, psw)




if __name__=='__main__':
    run()
