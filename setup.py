from setuptools import setup, find_packages

NAME = 'volumesh'

required_packages = find_packages()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name=NAME,
    version='1.2.0',
    packages=required_packages,
    entry_points={
        'console_scripts': [
          'volumesh = volumesh.__main__:main',
        ],
      },
    url='https://github.com/cansik/mesh-sequence-player',
    license='MIT License',
    author='Florian Bruggisser',
    author_email='github@broox.ch',
    description='A utility to work with volumesh files.',
    install_requires=required,
)
