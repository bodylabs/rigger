version = '0.1.2'

with open('requirements.txt', 'r') as f:
    install_requires = [x.strip() for x in f.readlines()]

from setuptools import setup, find_packages

setup(
    name='bodylabs-rigger',
    version=version,
    author='Body Labs',
    author_email='david.smith@bodylabs.com',
    description="Utilities for rigging a mesh from Body Labs' BodyKit API.",
    url='https://github.com/bodylabs/rigger',
    license='BSD',
    packages=find_packages(),
    package_data={
        'bodylabs_rigger.static': ['rig_assets.json']
    },
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
