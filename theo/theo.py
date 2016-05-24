import base64
import json

import boto3
import docker
import unipath


class Theo(object):
    def __init__(self, profile_name=None,aws_profile_name=None):
        self.load_settings(profile_name)
        self.load_credentials()
        self.load_docker_client()

    def load_settings(self, profile_name):
        try:

            settings_obj = json.load(open('.theo', 'r'))
            if profile_name:
                self.settings = settings_obj[profile_name]
            else:
                self.settings = settings_obj[list(settings_obj.keys())[0]]
        except IOError:
            self.settings = None

    def load_credentials(self):
        """
        Creates the Boto session
        """
        if self.settings is not None:
            self.boto_session = boto3.Session(
                profile_name=self.settings['aws_profile_name'],
                region_name=self.settings['aws_region_name']
            )
        else:
            self.boto_session = boto3.Session()

    def start_project(self, profile_name, aws_profile_name, aws_region_name, cluster, env_file):
        obj_dict = {
            profile_name: {
                'aws_profile_name': aws_profile_name,
                'aws_region_name': aws_region_name,
                'cluster': cluster
            }
        }
        if env_file != '':
            obj_dict[profile_name]['env_file'] = env_file

        file_obj = open('.theo', 'w+')
        obj = json.dump(obj_dict, file_obj, indent=4)
        file_obj.close()
        return obj_dict

    def add_profile(self, profile_name, aws_profile_name, aws_region_name, cluster, env_file):
        with open('.theo', 'r+') as f:
            data = json.load(f)
            data[profile_name] = {
                'aws_profile_name': aws_profile_name,
                'aws_region_name': aws_region_name,
                'cluster': cluster
            }
            if env_file != '':
                data[profile_name]['env_file'] = env_file
            f.seek(0)  # <--- should reset file position to the beginning.
            json.dump(data, f, indent=4)
            return data

    def list_profiles(self):
        file_obj = open('.theo', 'r')
        obj = json.load(file_obj)
        file_obj.close()
        return list(obj.keys())

    def load_docker_client(self):
        self.docker_client = docker.Client(
            base_url='unix://var/run/docker.sock')

    def list_clusters(self,aws_profile_name):
        ecs = boto3.Session(profile_name=aws_profile_name).client('ecs')
        return ecs.list_clusters()['clusterArns']

    def list_tasks(self, aws_profile_name, cluster):
        ecs = boto3.Session(profile_name=aws_profile_name).client('ecs')
        return ecs .list_tasks(
            cluster=cluster)['taskArns']

    def get_ecr_credentials(self, registry_id):
        client = self.boto_session.client('ecr')
        response = client.get_authorization_token(registryIds=[registry_id])
        password = base64.b64decode(
            response['authorizationData'][0]['authorizationToken']).lstrip('AWS:')
        endpoint = response['authorizationData'][0]['proxyEndpoint'].replace('https://', '')
        return (password, endpoint)

    def get_required_parameters(self, filename):
        """
        :param filename: Cloudformation file
        :return: List of required parameter names
        >>> get_required_parameters("cloudformation/ecs.json")
        [u'SecurityGroupID', u'KeyName', u'SubnetID']

        """
        parameters = json.load(
            open(filename, 'r')).get('Parameters', {})
        req_params = [k for k in iter(parameters.items()) if 'Default' not in k[1]]
        return [i[0] for i in req_params]

    def get_template_body(self, template_path):
        return open(template_path, 'r').read()

    def create_cluster(self, stack_name,parameters,aws_profile_name, aws_region_name):
        client = boto3.Session(profile_name=aws_profile_name,
                               region_name=aws_region_name).client('cloudformation')

        template_path = unipath.Path(
            __file__).ancestor(1).child('cloudformation').child('ecs.json')

        response = client.create_stack(
            StackName=stack_name,
            TemplateBody=self.get_template_body(template_path),
            Parameters=parameters,
            Capabilities=[
                'CAPABILITY_IAM',
                ]
            )
        return response['StackId']

    def push_image(self, file_path=None, prebuilt_image_name=None):
        if file_path and prebuilt_image_name:
            raise ValueError('Both file_path an')

    def list_repos(self):
        client = self.boto_session.client('ecr')
        return client.describe_repositories()['repositories']

    def build_dockerfile(self, file_path):
        self.docker_client.build()
