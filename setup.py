from setuptools import setup

setup(
        name='chainer_extensions',
        version='0.1.0',
        packages=['chextensions'],
        install_requires=[
            'chainer==2.0.2',
            'google-cloud==0.27.0',
            'PyYAML',
            'slackweb'],
        )