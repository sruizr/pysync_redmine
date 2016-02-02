import getpass
import click


class Sycronizer:
    def __init__(self, repository_1, repository_2):





@click.command()
@click.option('--project', prompt='Enter the URL of your project',
              help='URL of project at Redmine')
@click.option('--user', prompt='Enter your user key at Redmine',
              help='User key how is goint to update system to Redmine')
@click.option('--file', prompt='Enter path of project file',
              help='Filename of GanntProject')
def run(project_url, user_key):
    psw = getpass.getpass("Enter password:")



if __name__=='__main__':
    run()
