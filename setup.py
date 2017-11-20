from setuptools import setup

setup(
        name='chainer_extensions',
        version='0.1.1',
        packages=['chextensions'],
        install_requires=[
            'google-cloud',
            'PyYAML',
            'slackweb'],
        )
