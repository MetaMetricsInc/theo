import ConfigParser, os
import yaml
import botocore


ECS_MAP = {
    'mem_limit':'memory',
    'read_only':'readonlyRootFilesystem',
    'security_opt':'dockerSecurityOptions'
}
class NoSectionWrapper(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[vars]\n'

    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()


def _raise_invalid_port(port):
    raise ValueError('Invalid port "%s", should be '
                     '[[remote_ip:]remote_port[-remote_port]:]'
                     'port[/protocol]' % port)


def split_port_protocol(port_str):
    try:
        port, protocol = port_str.split('/')
    except ValueError:
        port, protocol = port_str, 'tcp'
    return (port, protocol)


def convert_volumes_from(volumes_str):
    volumes_parts = volumes_str.split(':')
    if len(volumes_parts) >= 3:
        raise ValueError(
            'The volumes_from argument in your Docker Compose'\
            ' file should follow the version 1 format.')
    if len(volumes_parts) == 2:
        read_only = True
        if volumes_parts[1] == 'rw':
            read_only = False
        return {
            'sourceContainer': volumes_parts[0],
            'readOnly': read_only
            }
    if len(volumes_parts) == 1:
        return {
            'sourceContainer': volumes_parts[0],
            'readOnly': True
            }


def convert_ports(port_str):
    port_parts = port_str.split(':')
    port_len = len(port_parts)

    if not 1 <= port_len <= 3:
        _raise_invalid_port(port_str)
    if port_len == 1:
        port, protocol = split_port_protocol(port_parts[0])
        return {
            'containerPort': port,
            'protocol': protocol,
            'hostPort': port
        }
    if port_len == 2:
        port, port2 = port_parts
        port_dict = {
            'hostPort': port,
        }
        port_dict['containerPort'], port_dict['protocol'] = split_port_protocol(port2)
        return port_dict

    port, port2 = '{0}:{1}'.format(port_parts[0], port_parts[1]), port_parts[2]
    port_dict = {
        'hostPort': port
    }
    port_dict['containerPort'], port_dict['protocol'] = split_port_protocol(port2)
    return port_dict


class ComposeECS(object):
    def __init__(self, theo_ins, family_name, file_path):
        self.theo_ins = theo_ins
        self.family_name = family_name
        self.file_path = file_path
        self.compose = yaml.load(open(self.file_path))
        self.compose_services = self.compose.get('services', {})
        self.compose_volumes = self.compose.get('volumes', {})

    def containers(self):
        # Create the list of containers that we will eventually return
        ecs_list = []
        # Loop over the compose_services dict
        for name, obj in self.compose_services.items():
            # Create ecs dict that we will add to the ecs_list
            ecs_dict = {
                'name': name
            }
            for k in obj.keys():
                meth_name = 'convert_{0}'.format(k)
                # Check to see if we have a method for converting this key
                if hasattr(self, meth_name):
                    ecs_dict = getattr(self, meth_name)(obj, ecs_dict)
                elif k in list(ECS_MAP.keys()):
                    ecs_name = ECS_MAP[k]
                    ecs_dict[ecs_name] = obj[k]
                else:
                    # If we don't have a method for converting the key
                    # just set it and forget it
                    ecs_dict[k] = obj[k]

            ecs_list.append(ecs_dict)
        return ecs_list

    def convert_dns(self,compose_dict, ecs_dict):
        dns = compose_dict['dns']
        if isinstance(dns,list):
            ecs_dict['dnsServers'] = dns
        else:
            ecs_dict['dnsServers'] = [dns]
        return ecs_dict

    def convert_dns_search(self, compose_dict, ecs_dict):
        dns = compose_dict['dns_search']
        if isinstance(dns, list):
            ecs_dict['dnsSearchDomains'] = dns
        else:
            ecs_dict['dnsSearchDomains'] = [dns]
        return ecs_dict

    def convert_command(self, compose_dict, ecs_dict):
        cmd = compose_dict['command']

        if isinstance(cmd, list):
            ecs_dict['command'] = [i.replace(' ', ',') for i in cmd]
        else:
            ecs_dict['command'] = [cmd.replace(' ', ',')]
        return ecs_dict

    def convert_volumes_from(self, compose_dict, ecs_dict):
        ecs_dict['volumesFrom']= []
        for i in compose_dict['volumes_from']:
            ecs_dict['volumesFrom'].append(convert_volumes_from(i))
        return ecs_dict

    def convert_working_dir(self, compose_dict, ecs_dict):
        ecs_dict['workingDirectory'] = compose_dict['working_dir'][0]
        return ecs_dict

    def convert_ulimits(self, compose_dict, ecs_dict):
        ecs_dict['ulimits'] = []
        for k,v in compose_dict['ulimits'].items():
            if isinstance(v,dict):


                ecs_dict['ulimits'].append({
                    'name':k,
                    'softLimit':v['soft'],
                    'hardLimit':v['hard']
                })
            else:
                ecs_dict['ulimits'].append({
                    'name':k,
                    'softLimit':v,
                    'hardLimit':v
                })
        return ecs_dict

    def convert_logging(self, compose_dict, ecs_dict):
        
        return ecs_dict

    def convert_labels(self, compose_dict, ecs_dict):
        labels = compose_dict['labels']
        if isinstance(labels,dict):
            ecs_dict['dockerLabels'] = labels
        else:
            ecs_dict['dockerLabels'] = {}

            for i in labels:
                try:
                    k,v = i.split('=')
                    ecs_dict['dockerLabels'][k] = v
                except ValueError:
                    ecs_dict['dockerLabels'][i] = None
        return ecs_dict

    def convert_extra_hosts(self, compose_dict, ecs_dict):
        extra_hosts = compose_dict['extra_hosts']
        ecs_dict['extraHosts'] = []
        for i in extra_hosts:
            host_parts = i.split(':')
            ecs_dict['extraHosts'].append({
                'hostname': host_parts[0],
                'ipAddress': host_parts[1]
            })
        return ecs_dict

    2

    def convert_env_file(self, compose_dict, ecs_dict):
        if 'env_file' in self.theo_ins.settings.keys():
            env_file = self.theo_ins.settings['env_file']
        else:
            env_file = compose_dict['env_file']
        ecs_dict['environment'] = self.convert_docker_env(env_file)
        return ecs_dict

    def convert_ports(self, compose_dict, ecs_dict):
        ecs_dict['portMappings'] = []
        for i in compose_dict['ports']:
            ecs_dict['portMappings'].append(convert_ports(i))
        return ecs_dict

    def volumes(self):
        return

    def convert_docker_env(self,file_path):
        is_s3 = False
        if file_path.startswith('s3://'):
            file_path = self.download_from_s3(*self.parse_s3_url(file_path))
            is_s3 = True

        config = ConfigParser.ConfigParser()
        config.readfp(NoSectionWrapper(open(file_path)))

        vars_list = [{
                         'name': k.upper(),
                         'value': v
                     } for k, v in config.items('vars')]
        if is_s3:
            self.delete_file(file_path)
        return vars_list

    def delete_file(self,file_path):
        os.remove(file_path)

    def parse_s3_url(self, s3_url):
        """
        Parse the S3 url. Format: s3://mybucket:path/to/my/key
        Example: s3://settings-bucket:/production_settings.py
        :param s3_url: Path to the file hosted on S3
        :return:
        """
        return s3_url.replace('s3://', '').split(':')

    def download_from_s3(self, bucket_name, s3_key,
                             output_filename='.s3_env'):
        """
        Download a file from S3
        :param bucket_name: Name of the S3 bucket (string)
        :param s3_key: Name of the file hosted on S3 (string)
        :param output_filename: Name of the file the download operation
        will create (string)
        :return: False or the value of output_filename
        """
        s3 = self.theo_ins.boto_session.resource('s3')
        bucket = s3.Bucket(bucket_name)
        try:
            s3.meta.client.head_object(Bucket=bucket_name, Key=s3_key)
        except botocore.exceptions.ClientError:
            raise Exception(
                'Your credentials were not able to download {0}'.format(
                    s3_key))
        bucket.download_file(s3_key, output_filename)
        return output_filename

    def render(self):
        return {
            'family': self.family_name,
            'containerDefinitions': self.containers(),
            'volumes': self.volumes()
        }
