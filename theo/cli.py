import argparse
import sys
import theo

THEO_COMMANDS = (
    'list_clusters',
    'list_services',
    'list_tasks'
)
class TheoCli(object):
    def deploy(self):
        pass

    def update(self):
        pass

    def start_project(self):
        pass

    def get_config(self):
        pass

    def _print_response(self,response,var_name):
        for i in response[var_name]:
            print i

    def list_clusters(self):
        resp = self.theo.list_clusters()
        self._print_response(resp,'clusterArns')

    def list_services(self):
        resp = self.theo.services()
        self._print_response(resp,'clusterArns')

    def list_tasks(self,cluster=None):
        if not cluster:
            raise ValueError('The --cluster_name (-c) is required for the "list_tasks" command')
        resp = self.theo.list_tasks(cluster)
        self._print_response(resp,'taskArns')

    def get_default_region(self):
        return theo.boto3.Session().region_name

    def push_image(self):
        pass

    def create_repository(self):
        pass


    def handle(self, argv=None):
        parser = argparse.ArgumentParser(description='Theo - Deploy applications to AWS ECS.\n')
        parser.add_argument('command', metavar='command', type=str,
                            help="Command to execute.")
        parser.add_argument('-p', '--profile_name', type=str, default='default',
                            help='AWS profile name. Default: default')
        parser.add_argument('-r', '--region_name', type=str, default=self.get_default_region(),
                            help=u'AWS region name. Your Default: {0}'.format(self.get_default_region()))
        parser.add_argument('-c','--cluster_name', type=str,
                            help='Name of ECS Cluster',default=None)

        args = parser.parse_args(argv)
        self.theo = theo.Theo(args.profile_name,)
        if args.command in THEO_COMMANDS:
            getattr(self,args.command)()



def handle():
    cli = TheoCli()
    sys.exit(cli.handle())


if __name__ == '__main__':
    handle()
