import base64
import boto3
import docker
import json
import utils

class Theo(object):

    def __init__(self,profile_name=None,region_name=None):
        """

        :param profile_name: AWS profile name. Usually found in the credentials file at ~/.aws/credentials
        :param region_name: AWS region

        """
        self.load_credentials(profile_name,region_name)
        self.load_docker_client()

    def load_credentials(self,profile_name,region_name):
        """
        Creates the Boto session
        :param profile_name: AWS Profile name. Usually found in the credentials file at ~/.aws/credentials
        :param region_name: AWS region

        """
        if not region_name:
            region_name = boto3.Session().region_name

        if profile_name:
            self.boto_session = boto3.Session(profile_name=profile_name,region_name=region_name)
        else:
            self.boto_session = boto3.Session(region_name=region_name)

    def load_docker_client(self):
        self.docker_client = docker.Client(base_url='unix://var/run/docker.sock')

    def list_clusters(self):
        ecs = self.boto_session.client('ecs')
        return ecs.list_clusters()

    def list_tasks(self,cluster):
        return self.boto_session.client('ecs').list_tasks(cluster=cluster)

    def get_ecr_credentials(self,registry_id):
        client = self.boto_session.client('ecr')
        response = client.get_authorization_token(registryIds=[registry_id])
        password = base64.b64decode(response['authorizationData'][0]['authorizationToken']).lstrip('AWS:')
        endpoint = response['authorizationData'][0]['proxyEndpoint'].replace('https://','')
        return (password,endpoint)

    def get_required_parameters(self,filename):
        """
        :param filename: Cloudformation file
        :return: List of required parameter names
        >>> get_required_parameters("cloudformation/ecs.json")
        [u'SecurityGroupID', u'KeyName', u'SubnetID']

        """
        parameters = json.load(
            open(filename, 'r')).get('Parameters',{})
        req_params = filter(lambda k: not k[1].has_key('Default'),
                        parameters.iteritems())
        return [i[0] for i in req_params]

    def create_stack(self,stack_name,template_body='cloudformation/ecs.json'):
        client = self.boto_session.client('cloudformation')
        response = client.create_stack(StackName=stack_name,TemplateBody)

    def push_image(self,file_path=None,prebuilt_image_name=None):
        if file_path and image_name:
            raise ValueError('Both file_path an')


    def build_dockerfile(self,file_path):
        self.docker_client.build()
