# Copyright (c) 2018 European Organization for Nuclear Research.
# All Rights Reserved.
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

import os

import magnum.conf
from magnum.drivers.heat import k8s_fedora_template_def as kftd
from magnum.drivers.heat import k8s_template_def as ktd
from magnum.drivers.heat import template_def as base

CONF = magnum.conf.CONF


class AtomicK8sNGTemplateDefinition(kftd.K8sFedoraTemplateDefinition):
    """Kubernetes template for a Fedora Atomic VM."""

    def __init__(self):
        super(AtomicK8sNGTemplateDefinition, self).__init__()
        self.add_parameter('dns_nameserver',
                           cluster_template_attr='dns_nameserver')
        self.add_parameter('http_proxy',
                           cluster_template_attr='http_proxy')
        self.add_parameter('https_proxy',
                           cluster_template_attr='https_proxy')
        self.add_parameter('no_proxy',
                           cluster_template_attr='no_proxy')
        self.add_parameter('external_network',
                           cluster_template_attr='external_network_id')
        self.add_parameter('insecure_registry_url',
                           cluster_template_attr='insecure_registry')
        self.add_parameter('cluster_uuid',
                           cluster_attr='uuid')
        self.add_parameter('kube_version',
                           cluster_attr='coe_version')
        self.add_output('api_address',
                        cluster_attr='api_address',
                        mapping_type=ktd.K8sApiAddressOutputMapping)

    @property
    def driver_module_path(self):
        return __name__[:__name__.rindex('.')]

    @property
    def template_path(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'templates/cluster.yaml')

    def update_outputs(self, stack, cluster_template, cluster):
        #worker_ng = cluster.default_worker
        #master_ng = cluster.default_master

        #self.add_output('kube_minions',
        #                nodegroup_attr='node_addresses',
        #                nodegroup_uuid=worker_ng.uuid,
        #                mapping_type=NodeAddressOutputMapping)
        #self.add_output('kube_masters',
        #                nodegroup_attr='node_addresses',
        #                nodegroup_uuid=master_ng.uuid,
        #                mapping_type=MasterAddressOutputMapping)
        for ng in cluster.nodegroups:
            self.add_output('ng_node_ips',
                            nodegroup_attr='node_addresses',
                            nodegroup_uuid=ng.uuid,
                            mapping_type=base.NodeGroupJsonOutputMapping)
        super(AtomicK8sNGTemplateDefinition,
              self).update_outputs(stack, cluster_template, cluster)

    def add_nodegroup_params(self, cluster):
        for ng in cluster.nodegroups:
            self.add_parameter('names',
                               nodegroup_attr='name',
                               nodegroup_uuid=ng.uuid,
                               param_type='JSONDict',
                               param_class=base.NodeGroupParameterMapping)
            self.add_parameter('image_ids',
                               nodegroup_attr='image_id',
                               nodegroup_uuid=ng.uuid,
                               param_type='JSONDict',
                               param_class=base.NodeGroupParameterMapping)
            self.add_parameter('nodegroup_roles',
                               nodegroup_attr='role',
                               nodegroup_uuid=ng.uuid,
                               param_type='JSONDict',
                               param_class=base.NodeGroupParameterMapping)
            self.add_parameter('flavors',
                               nodegroup_attr='flavor_id',
                               nodegroup_uuid=ng.uuid,
                               param_type='JSONDict',
                               param_class=base.NodeGroupParameterMapping)
            self.add_parameter('node_counts',
                               nodegroup_attr='node_count',
                               nodegroup_uuid=ng.uuid,
                               param_type='JSONDict',
                               param_class=base.NodeGroupParameterMapping)
            if ng.role == 'master':
                self.add_parameter('master_ng_uuids',
                                   nodegroup_attr='uuid',
                                   nodegroup_uuid=ng.uuid,
                                   param_type='JSONList',
                                   param_class=base.NodeGroupParameterMapping)
            else:
                self.add_parameter('ng_uuids',
                                   nodegroup_attr='uuid',
                                   nodegroup_uuid=ng.uuid,
                                   param_type='JSONList',
                                   param_class=base.NodeGroupParameterMapping)
        #super(AtomicK8sNGTemplateDefinition,
        #      self).add_nodegroup_params(cluster)
