#!/usr/bin/env python

# Copyright 2008-2018 Univa Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: skip-file

import os
import subprocess
from pathlib import Path
from setuptools import setup, find_packages
import setuptools.command.build_py
import setuptools.command.sdist

srcRoot = 'tortuga'
module_name = 'tortuga-core'

maj_version = '6.3'
version = maj_version + '.0'
module_version = version


if os.getenv('BUILD_NUMBER'):
    module_version += '.dev{0}'.format(os.getenv('BUILD_NUMBER'))


def walkfiles(d):
    for f in d.iterdir():
        if f.is_dir():
            for item in walkfiles(f):
                yield item

            continue
        else:
            yield f


def generate_release_file(build_identifier=None):
    with open('etc/tortuga-release', 'w') as fp:
        buf = 'Tortuga %s' % (version)

        if build_identifier is not None:
            buf += ' (%s)' % (build_identifier)
        else:
            cmd = 'git rev-parse --short HEAD'

            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            result, _ = p.communicate()
            p.wait()

            buf += ' (Git {0})'.format(result.decode().rstrip())

        fp.write(buf + '\n')


class CommonBuildStep(object):
    def pre_build(self):
        generate_release_file()


class BuildPyCommand(setuptools.command.build_py.build_py, CommonBuildStep):
    """
    Override 'build_py' command to generate files before build
    """

    def run(self):
        self.pre_build()

        setuptools.command.build_py.build_py.run(self)


class SdistCommand(setuptools.command.sdist.sdist, CommonBuildStep):
    def run(self):
        self.pre_build()

        setuptools.command.sdist.sdist.run(self)


setup(
    name=module_name,
    version=module_version,
    description='Tortuga core component',
    author='Univa Corporation',
    author_email='engineering@univa.com',
    url='http://univa.com',
    license='Apache 2.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    scripts=[str(script_file) for script_file in Path('bin').iterdir()],
    data_files=[
        ('etc', [str(fn) for fn in Path('etc').iterdir()]),
        ('man/man8', [
            str(fn) for fn in Path(Path('man') / Path('man8')).iterdir()]),
    ],
    install_requires=[
        'marshmallow',
        'pip2pi',
        'passlib',
    ],
    zip_safe=False,
    namespace_packages=['tortuga'],
    cmdclass={
        'build_py': BuildPyCommand,
        'sdist': SdistCommand,
    },
    entry_points={
        'console_scripts': [
            'activate-node=tortuga.scripts.activate_node:main',
            'adapter-mgmt=tortuga.scripts.adapter_mgmt:main',
            'add-admin=tortuga.scripts.add_admin:main',
            'add-admin-to-profile=tortuga.scripts.add_admin_to_profile:main',
            'add-network=tortuga.scripts.add_network:main',
            'add-nodes=tortuga.scripts.add_nodes:main',
            'checkpoint-node=tortuga.scripts.checkpoint_node:main',
            'copy-hardware-profile=tortuga.scripts.copy_hardware_profile:main',
            'copy-software-profile=tortuga.scripts.copy_software_profile:main',
            'create-hardware-profile=tortuga.scripts.create_hardware_profile:main',
            'create-software-profile=tortuga.scripts.create_software_profile:main',
            'delete-admin=tortuga.scripts.delete_admin:main',
            'delete-admin-from-profile=tortuga.scripts.delete_admin_from_profile:main',
            'delete-hardware-profile=tortuga.scripts.delete_hardware_profile:main',
            'delete-kit=tortuga.scripts.delete_kit:main',
            'delete-network=tortuga.scripts.delete_network:main',
            'delete-node=tortuga.scripts.delete_node:main',
            'delete-profile-mapping=tortuga.scripts.delete_profile_mapping:main',
            'delete-software-profile=tortuga.scripts.delete_software_profile:main',
            'disable-component=tortuga.scripts.disable_component:main',
            'enable-component=tortuga.scripts.enable_component:main',
            'get-admin=tortuga.scripts.get_admin:main',
            'get-admin-list=tortuga.scripts.get_admin_list:main',
            'get-component-list=tortuga.scripts.get_component_list:main',
            'get-component-node-list=tortuga.scripts.get_component_node_list:main',
            'get-hardware-profile=tortuga.scripts.get_hardware_profile:main',
            'get-hardware-profile-list=tortuga.scripts.get_hardware_profile_list:main',
            'get-idle-software-profile-list=tortuga.scripts.get_idle_software_profile_list:main',
            'get-kit=tortuga.scripts.get_kit:main',
            'get-kit-list=tortuga.scripts.get_kit_list:main',
            'get-network=tortuga.scripts.get_network:main',
            'get-network-list=tortuga.scripts.get_network_list:main',
            'get-node-requests=tortuga.scripts.get_node_requests:main',
            'get-node-status=tortuga.scripts.get_node_status:main',
            'get-provisioning-networks=tortuga.scripts.get_provisioning_networks:main',
            'get-resource-adapter-list=tortuga.scripts.get_resource_adapter_list:main',
            'get-software-profile=tortuga.scripts.get_software_profile:main',
            'get-software-profile-list=tortuga.scripts.get_software_profile_list:main',
            'get-software-profile-nodes=tortuga.scripts.get_software_profile_nodes:main',
            'idle-node=tortuga.scripts.idle_node:main',
            'migrate-node=tortuga.scripts.migrate_node:main',
            'reboot-node=tortuga.scripts.reboot_node:main',
            'revert-node-to-checkpoint=tortuga.scripts.revert_node_to_checkpoint:main',
            'schedule-update=tortuga.scripts.schedule_update:main',
            'set-profile-mapping=tortuga.scripts.set_profile_mapping:main',
            'shutdown-node=tortuga.scripts.shutdown_node:main',
            'transfer-node=tortuga.scripts.transfer_node:main',
            'uc-tag=tortuga.scripts.uc_tag:main',
            'ucparam=tortuga.scripts.ucparam:main',
            'update-hardware-profile=tortuga.scripts.update_hardware_profile:main',
            'update-software-profile=tortuga.scripts.update_software_profile:main',
            'update-admin=tortuga.scripts.update_admin:main',
            'update-network=tortuga.scripts.update_network:main',
        ],
    },
)
