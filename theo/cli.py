import functools
import os

import click
import terminaltables

from .theo import Theo


class TheoSettingsError(Exception):
    pass


def load_settings(theo_ins, profile):
    try:
        theo_ins.load_settings(profile)
    except KeyError:
        click.echo(
            click.style(
                "Your .theo settings doesn't have a profile named {0}. Valid " \
                "profile names: {1}." \
                    .format(profile, theo_ins.list_profiles()), fg='red'))
        exit()


def require_settings(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        if not os.path.exists('.theo'):
            click.echo(click.style(
                'ERROR: The {0} command requires the .theo settings file. ' \
                'Please run theo start_project.'.format(
                    func.__name__), fg='red'))
            exit()
            return
        return func(*args, **kwargs)

    return func_wrapper


#######################################
#
#  Theo Commands
#
#######################################


@click.group()
@click.pass_context
def theo(ctx):
    ctx.obj = {}
    ctx.obj['theo'] = Theo()


@theo.command()
@click.option('--aws_profile', prompt=True, default=Theo().boto_session.profile_name)
@click.pass_context
def list_clusters(ctx, aws_profile):
    theo_ins = ctx.obj['theo']
    result = theo_ins.list_clusters(aws_profile)
    click.echo(click.style('List of Amazon ECS Clusters (ARNs):', fg='green'))
    table_data = [[i] for i in result]
    table_data.insert(0, ['ARN'])
    click.echo(terminaltables.AsciiTable(table_data).table)


@theo.command(
    help="Create a AWS Cloudformation ECS stack using Theo's default template."
)
@click.argument('stack_name')
@click.option('--key_name', prompt=True, help='EC2 Key Pair')
@click.option('--security_group_id',
              prompt=True, help='EC2 Security Group ID ex. sg-xxxxxxxx')
@click.option('--subnet_id', prompt=True,
              help='VPC subnet ID ex. subnet-xxxxxxxx')
@click.option('--desired_capacity', prompt=True,
              help='Number of EC2 instances', default='2')
@click.option('--autoscaling_max_size', prompt=True,
              help='Maximum number of EC2 instances', default='10')
@click.option('--instance_type', prompt=True, help='EC2 Instance Type',
              default='t2.micro')
@click.option('--aws_profile', prompt=True,
              default=Theo().boto_session.profile_name)
@click.option('--aws_region_name', default='us-east-1', prompt=True,
              help="The AWS region name.")
@click.pass_context
def create_cluster(ctx, stack_name, **kwargs):
    template_param_keys = ['key_name', 'security_group_id', 'subnet_id',
                           'desired_capacity', 'instance_type', 'autoscaling_max_size']
    parameters = [
        {'ParameterKey': k.replace('_', ''),
         'ParameterValue': v} for k, v in kwargs.items() if k in template_param_keys
        ]
    theo_ins = ctx.obj['theo']

    result = theo_ins.create_cluster(stack_name, parameters,
                                     kwargs['aws_profile'], kwargs['aws_region_name'])

    click.echo(click.style(
        'Here is the ARN for your new cloudformation stack: {0}'.format(
            result), fg='green'))


@theo.command(help='Ex: theo clusters list_services <cluster_id>')
@click.option('--aws_profile', prompt=True, default=Theo().boto_session.profile_name)
@click.option('--cluster', prompt=True,
              help='The Amazon ARN for the cluster that you want a list of ' \
                   'tasks from. ex. arn:aws:ecs:us-east-1:5354534534534:cluster/test')
@click.pass_context
def list_tasks(ctx, aws_profile, cluster):
    theo_ins = ctx.obj['theo']
    result = theo_ins.list_tasks(aws_profile, cluster)
    click.echo(click.style(
        'List of Amazon ECS Task Definitions (ARNs) for' \
        ' the cluster specified:', fg='green'))
    table_data = [[i] for i in result]
    table_data.insert(0, ['ARN'])
    click.echo(terminaltables.AsciiTable(table_data).table)


@theo.command()
@click.option('--profile_name', default='staging', prompt=True,
              help='The profile name')
@click.option('--aws_profile_name', default='default', prompt=True,
              help="The AWS profile name found in ~/.aws/credentials")
@click.option('--aws_region_name', default='us-east-1', prompt=True,
              help="The AWS region name.")
@click.option('--cluster', prompt=True,
              help='The ECS cluster this profile should interact with')
@click.option('--env_file', prompt=True,default='',
              help='Environment variables file ex: s3://mybucketname:path/to/my/settings.py')
@click.pass_context
def start_project(ctx, profile_name, aws_profile_name, aws_region_name,
                  cluster, env_file):
    theo_ins = ctx.obj['theo']
    theo_ins.start_project(profile_name, aws_profile_name,
                           aws_region_name, cluster, env_file)
    click.echo(click.style(
        'Created .theo settings with an intial profile named {0}.'.format(
            profile_name), fg='green'))


@theo.command()
@click.option('--profile_name', default='staging', prompt=True,
              help='The profile name')
@click.option('--aws_profile_name', default='default', prompt=True,
              help="The AWS profile name found in ~/.aws/credentials")
@click.option('--aws_region_name', default='us-east-1', prompt=True,
              help="The AWS region name.")
@click.option('--cluster', prompt=True,
              help='The ECS cluster this profile should interact with')
@click.option('--env_file', prompt=True,default='',
              help='Environment variables file ex: s3://mybucketname:path/to/my/settings.py')
@click.pass_context
@require_settings
def add_profile(ctx, profile_name, aws_profile_name, aws_region_name, cluster, env_file):
    theo_ins = ctx.obj['theo']
    resp = theo_ins.add_profile(profile_name, aws_profile_name,
                                aws_region_name, cluster, env_file)
    click.echo(click.style('Updated .theo settings with a new profile ' \
                           'named {0}. Current profiles: {1}'.format(
        profile_name, list(resp.keys())), fg='green'))


@theo.command()
@click.pass_context
@require_settings
def list_profiles(ctx):
    theo_ins = ctx.obj['theo']
    result = theo_ins.list_profiles()
    click.echo(click.style('List of Theo profiles:', fg='green'))
    table_data = [[i] for i in result]
    table_data.insert(0, ['Profile Name'])
    click.echo(terminaltables.AsciiTable(table_data).table)


def deploy(ctx, profile_name):
    pass


def update(ctx, profile_name):
    pass


#####################################
#
# ECR Repository Commands
#
#####################################


@theo.group()
@click.argument('profile')
@click.pass_context
@require_settings
def repos(ctx, profile):
    theo_ins = ctx.obj['theo']
    load_settings(theo_ins, profile)


@repos.command()
@click.pass_context
def push_image(ctx):
    pass


@repos.command()
@click.pass_context
def list_repos(ctx):
    theo_ins = ctx.obj['theo']
    result = theo_ins.list_repos()
    table_data = [
        [i['registryId'], i['repositoryName'], i['repositoryArn'],
         i['repositoryUri']]
        for i in result
        ]
    table_data.insert(0, ['ID', 'Name', 'ARN', 'URL', ])
    table = terminaltables.AsciiTable(table_data)
    click.echo(table.table)


if __name__ == '__main__':
    theo(obj={})
