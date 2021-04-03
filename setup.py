from setuptools import setup

setup(
    name='tasker',
    version='0.0.0',
    packages=['tasker', 'tasker.drivers'],
    entry_points={
        'console_scripts': ['tasker=tasker.main:main'],
    }
)
