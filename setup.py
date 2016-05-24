from setuptools import setup

setup(
    name='theo',
    version='0.1',
    py_modules=['theo.cli'],
    install_requires=[
        'Click',
        'unipath',
        'docker-py',
        'terminaltables',
        'boto3',
    ],
    entry_points='''
        [console_scripts]
        theo=theo.cli:theo
    ''',
)