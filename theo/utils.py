import json


def get_required_parameters(filename):
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()