from setuptools import setup

setup(
        name='chainer_extensions',
        version='0.1.0',
        packages=['chextensions'],
        install_requires=[
            'google-cloud',
            'PyYAML',
            'slackweb'],
        )