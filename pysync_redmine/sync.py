import json
import click
import pysync_redmine.repositories as base
from pysync_redmine.domain import (
                                    RelationSet,
                                    Task,
                                    Member,
                                    Phase,
                                    Syncronizer
                                    )
import pdb


@click.group()
def sync():
    pass


def foo():

    gantt = base.RepoFactory.create('GanttRepo')
    redmine = base.RepoFactory.create('RedmineRepo')

    import os.path
    if not os.path.isfile(filename):
        raise(ValueError('Filename doesn t exist'))

    gantt.open_source(filename=filename)
    tokens = url.split('/')
    project_key = tokens.pop(-1)
    tokens.pop(-1)
    url = '/'.join(tokens)

    redmine.open_source(url=url, username=user, password=password,
                        project_key=project_key)

    syncronizer = Syncronizer()
    syncronizer.deploy(gantt, redmine)

    data_name = '{}.json'.format(redmine.project.key)
    with open(data_name, 'w') as outfile:
        json.dump(syncronizer.sync_data, outfile)


@sync.command()
@click.option('--filename', prompt='Enter path of project file',
              help='Filename of GanntProject')
@click.option('--url', prompt='Enter the URL of your project',
              help='URL of Redmine application')
@click.option('--user', prompt='Enter your user login at Redmine',
              help='User key how is goint to update system to Redmine')
@click.option('--password', prompt='Enter your password', hide_input=True)
def upload(filename, url, user, password):
    syncronizer = Syncronizer()
    print('Allí va uno {}'.format(syncronizer))
    syncronizer.add_redmine_project(url, user, password)
    syncronizer.add_ganttproject(filename)

    # pdb.set_trace()
    syncronizer.deploy_to_redmine()


@sync.command()
@click.option('--filename', prompt='Enter path of project file',
              help='Filename of GanntProject')
@click.option('--url', prompt='Enter the URL of your project',
              help='URL of Redmine application')
@click.option('--user', prompt='Enter your user login at Redmine',
              help='User key how is goint to update system to Redmine')
@click.option('--password', prompt='Enter your password', hide_input=True)
def download(filename, url, user, password):
    syncronizer = Syncronizer()
    syncronizer.add_redmine_project(url, user, password)
    syncronizer.add_ganttproject(filename)
    # pdb.set_trace()

    syncronizer.deploy_to_ganttproject()

if __name__ == '__main__':
    sync()
