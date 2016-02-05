import getpass
import click
import pysync_redmine.repositories as repos


class Syncronizer:
    def __init__(self, repo1, repo2):
        pass


@click.command()
@click.option('--project', prompt='Enter the URL of your project',
              help='URL of project at Redmine')
@click.option('--user', prompt='Enter your user login at Redmine',
              help='User key how is goint to update system to Redmine')
@click.option('--password', prompt='Enter your password', hide=True)
@click.option('--file', prompt='Enter path of project file',
              help='Filename of GanntProject')
def sync_red_ganttproject(project_url, user_key, psw, filename):

    redmine = repos.redmine.RedmineRepo(project_url, user_key, psw)
    gantt_project = repos.ganntproject.GanttRepo(filename)








if __name__=='__main__':
    run()
