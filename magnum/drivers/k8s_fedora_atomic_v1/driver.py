# Copyright 2016 Rackspace Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from magnum.common import clients
from magnum.drivers.common import k8s_monitor
from magnum.drivers.common.k8s_scale_manager import K8sScaleManager
from magnum.drivers.heat import driver
from magnum.drivers.k8s_fedora_atomic_v1 import template_def


class Driver(driver.HeatDriver):

    @property
    def provides(self):
        return [
            {'server_type': 'vm',
             'os': 'fedora-atomic',
             'coe': 'kubernetes'},
        ]

    def get_template_definition(self):
        return template_def.AtomicK8sTemplateDefinition()

    def get_monitor(self, context, cluster):
        return k8s_monitor.K8sMonitor(context, cluster)

    def get_scale_manager(self, context, osclient, cluster):
        return K8sScaleManager(context, osclient, cluster)

    def upgrade_cluster(self, context, cluster, scale_manager=None,
                        rollback=False):
        raise Exception("strigazi")
        return
        #osc = clients.OpenStackClients(context)
        #template_path, heat_params, env_files = (
        #    self._extract_template_definition(context, cluster,
        #                                      scale_manager=scale_manager))

        #tpl_files, template = template_utils.get_template_contents(
        #    template_path)
        #environment_files, env_map = self._get_env_files(template_path,
        #                                                 env_files)
        #tpl_files.update(env_map)

        #fields = {
        #    'parameters': heat_params,
        #    'environment_files': environment_files,
        #    'template': template,
        #    'files': tpl_files,
        #    'disable_rollback': not rollback
        #}

        #osc.heat().stacks.update(cluster.stack_id, **fields)
