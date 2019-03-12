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

import json

from string import ascii_letters
from string import digits

from oslo_config import cfg
from oslo_utils import strutils

from magnum.common import clients
from magnum.common import keystone
from magnum.common import short_id
from magnum.common.x509 import operations as x509
from magnum.common import utils
from magnum.conductor import utils as conductor_utils
from magnum.drivers.common import k8s_monitor
from magnum.drivers.heat import driver
from magnum.drivers.k8s_fedora_atomic_v2 import template_def
from magnum import objects

from heatclient.common import template_utils

CONF = cfg.CONF


class Driver(driver.HeatDriver):

    @property
    def provides(self):
        return [
            {'server_type': 'vm',
             'os': 'fedora-atomic',
             'coe': 'kubernetes-ng'},
        ]

    def get_template_definition(self):
        return template_def.AtomicK8sNGTemplateDefinition()

    def get_monitor(self, context, cluster):
        return k8s_monitor.K8sMonitor(context, cluster)

    def _create_stack(self, context, osc, cluster, cluster_create_timeout):
        template_path, heat_params, env_files = (
            self._extract_template_definition(context, cluster))

        master_ng_count = 0
        ng_count = 0
        for ng in cluster.nodegroups:
            if ng.role == 'master':
                master_ng_count += 1
            else:
                ng_count += 1
        heat_params['master_ng_count'] = master_ng_count
        heat_params['ng_count'] = ng_count
        tpl_files, template = template_utils.get_template_contents(
            template_path)

        environment_files, env_map = self._get_env_files(template_path,
                                                         env_files)
        tpl_files.update(env_map)

        # Make sure we end up with a valid hostname
        valid_chars = set(ascii_letters + digits + '-')

        # valid hostnames are 63 chars long, leaving enough room
        # to add the random id (for uniqueness)
        stack_name = cluster.name[:30]
        stack_name = stack_name.replace('_', '-')
        stack_name = stack_name.replace('.', '-')
        stack_name = ''.join(filter(valid_chars.__contains__, stack_name))

        # Make sure no duplicate stack name
        stack_name = '%s-%s' % (stack_name, short_id.generate_id())
        stack_name = stack_name.lower()
        if cluster_create_timeout:
            heat_timeout = cluster_create_timeout
        else:
            # no cluster_create_timeout value was passed in to the request
            # so falling back on configuration file value
            heat_timeout = cfg.CONF.cluster_heat.create_timeout
        fields = {
            'stack_name': stack_name,
            'parameters': heat_params,
            'environment_files': environment_files,
            'template': template,
            'files': tpl_files,
            'timeout_mins': heat_timeout
        }
        created_stack = osc.heat().stacks.create(**fields)

        return created_stack

    #def _create_stack(self, context, osc, cluster, cluster_create_timeout):
    #    cluster_template = conductor_utils.retrieve_cluster_template(context,
    #                                                                 cluster)
    #    template_path, heat_params, env_files = (
    #        self._extract_template_definition(context, cluster))

    #    tpl_files, template = template_utils.get_template_contents(
    #        template_path)

    #    environment_files, env_map = self._get_env_files(template_path,
    #                                                     env_files)
    #    tpl_files.update(env_map)

    #    # Make sure we end up with a valid hostname
    #    valid_chars = set(ascii_letters + digits + '-')

    #    heat_params = {
    #        "master_ng_uuids": [],
    #        "master_ng_count": 1,
    #        "ng_uuids": [],
    #        "ng_count": 1,
    #        "node_counts": {},
    #        "names": {},
    #        "image_ids": {},
    #        "key_name": "",
    #        "flavors": {},
    #        "groups_to_remove": [],
    #        "nodes_to_remove": {},
    #        "nodegroup_roles": {},
    #        "dns_nameserver": cluster_template.dns_nameserver,
    #        "http_proxy": cluster_template.http_proxy,
    #        "https_proxy": cluster_template.https_proxy,
    #        "no_proxy": cluster_template.no_proxy,
    #        "trustee_domain_id": osc.keystone().trustee_domain_id,
    #        "trustee_user_id": cluster.trustee_user_id,
    #        "trustee_username": cluster.trustee_username,
    #        "trustee_password": cluster.trustee_password,
    #        "verify_ca": CONF.drivers.verify_ca,
    #        "openstack_ca": utils.get_openstack_ca(),
    #        "cluster_uuid": cluster.uuid,
    #        "kube_version": cluster.coe_version,
    #        "external_network": cluster_template.external_network_id,
    #        "insecure_registry_url": cluster_template.insecure_registry
    #    }

    #    params = [
    #        "fixed_network",
    #        "fixed_subnet",
    #        "network_driver",
    #        "volume_driver",
    #        "tls_disabled",
    #        "registry_enabled",
    #    ]
    #    for param in params:
    #        heat_params[param] = getattr(cluster_template, param)

    #    #heat_params['discovery_url'] = self.get_discovery_url(cluster)
    #    heat_params['magnum_url'] = osc.magnum_url()

    #    if cluster_template.tls_disabled:
    #        heat_params['loadbalancing_protocol'] = 'HTTP'
    #        heat_params['kubernetes_port'] = 8080

    #    heat_params['octavia_enabled'] = keystone.is_octavia_enabled()

    #    label_list = ['flannel_network_cidr', 'flannel_backend',
    #                  'flannel_network_subnetlen',
    #                  'system_pods_initial_delay',
    #                  'system_pods_timeout',
    #                  'admission_control_list',
    #                  'prometheus_monitoring',
    #                  'grafana_admin_passwd',
    #                  'kube_dashboard_enabled',
    #                  'etcd_volume_size',
    #                  'cert_manager_api',
    #                  'ingress_controller',
    #                  'ingress_controller_role',
    #                  'kubelet_options',
    #                  'kubeapi_options',
    #                  'kubeproxy_options',
    #                  'kubecontroller_options',
    #                  'kubescheduler_options',
    #                  'influx_grafana_dashboard_enabled']

    #    for label in label_list:
    #        heat_params[label] = cluster.labels.get(label)

    #    cluser_ip_range = cluster.labels.get('service_cluster_ip_range')
    #    if cluser_ip_range:
    #        heat_params['portal_network_cidr'] = cluser_ip_range

    #    if cluster_template.registry_enabled:
    #        heat_params['swift_region'] = CONF.docker_registry.swift_region
    #        heat_params['registry_container'] = (
    #            CONF.docker_registry.swift_registry_container)

    #    heat_params['username'] = context.user_name
    #    heat_params['region_name'] = osc.cinder_region_name()
    #    docker_volume_type = cluster.labels.get(
    #        'docker_volume_type', CONF.cinder.default_docker_volume_type)
    #    heat_params['docker_volume_type'] = docker_volume_type
    #    heat_params['nodes_affinity_policy'] = \
    #        CONF.cluster.nodes_affinity_policy

    #    if cluster_template.network_driver == 'flannel':
    #        heat_params["pods_network_cidr"] = \
    #            cluster.labels.get('flannel_network_cidr', '10.100.0.0/16')
    #    if cluster_template.network_driver == 'calico':
    #        heat_params["pods_network_cidr"] = \
    #            cluster.labels.get('calico_ipv4pool', '192.168.0.0/16')

    #    # check cloud provider and cinder options. If cinder is selected,
    #    # the cloud provider needs to be enabled.
    #    cloud_provider_enabled = cluster.labels.get(
    #        'cloud_provider_enabled', 'true').lower()
    #    if (cluster_template.volume_driver == 'cinder'
    #            and cloud_provider_enabled == 'false'):
    #        raise exception.InvalidParameterValue(_(
    #            '"cinder" volume driver needs "cloud_provider_enabled" label '
    #            'to be true or unset.'))

    #    label_list = ['kube_tag', 'container_infra_prefix',
    #                  'availability_zone',
    #                  'cgroup_driver',
    #                  'calico_tag', 'calico_cni_tag',
    #                  'calico_kube_controllers_tag', 'calico_ipv4pool',
    #                  'etcd_tag', 'flannel_tag',
    #                  'cloud_provider_enabled',
    #                  'cloud_provider_tag',
    #                  'prometheus_tag',
    #                  'grafana_tag',
    #                  'heat_container_agent_tag']

    #    for label in label_list:
    #        label_value = cluster.labels.get(label)
    #        if label_value:
    #            heat_params[label] = label_value

    #    csr_keys = x509.generate_csr_and_key(u"Kubernetes Service Account")

    #    heat_params['kube_service_account_key'] = \
    #        csr_keys["public_key"].replace("\n", "\\n")
    #    heat_params['kube_service_account_private_key'] = \
    #        csr_keys["private_key"].replace("\n", "\\n")

    #    cert_manager_api = cluster.labels.get('cert_manager_api')
    #    if strutils.bool_from_string(cert_manager_api):
    #        heat_params['cert_manager_api'] = cert_manager_api
    #        ca_cert = cert_manager.get_cluster_ca_certificate(cluster)
    #        heat_params['ca_key'] = x509.decrypt_key(
    #            ca_cert.get_private_key(),
    #            ca_cert.get_private_key_passphrase()).replace("\n", "\\n")

    #    # Only pass trust ID into the template if allowed by the config file
    #    if CONF.trust.cluster_user_trust:
    #        heat_params['trust_id'] = cluster.trust_id
    #    else:
    #        heat_params['trust_id'] = ""

    #    cluster_nodegroups = objects.NodeGroup.list(context, cluster.uuid,
    #                                                sort_key='id')
    #    for ng in cluster_nodegroups:
    #        if ng.role == "master":
    #            heat_params['master_ng_uuids'].append(ng.uuid)
    #        else:
    #            heat_params['ng_uuids'].append(ng.uuid)
    #        heat_params['node_counts'].update({ng.uuid: ng.node_count})
    #        heat_params['names'].update({ng.uuid: ng.name})
    #        heat_params['image_ids'].update({ng.uuid: ng.image_id})
    #        heat_params['flavors'].update({ng.uuid: ng.flavor_id})
    #        heat_params['nodes_to_remove'].update({ng.uuid: ""})
    #        heat_params['nodegroup_roles'].update({ng.uuid: ng.role})

    #    # valid hostnames are 63 chars long, leaving enough room
    #    # to add the random id (for uniqueness)
    #    stack_name = cluster.name[:30]
    #    stack_name = stack_name.replace('_', '-')
    #    stack_name = stack_name.replace('.', '-')
    #    stack_name = ''.join(filter(valid_chars.__contains__, stack_name))

    #    # Make sure no duplicate stack name
    #    stack_name = '%s-%s' % (stack_name, short_id.generate_id())
    #    stack_name = stack_name.lower()
    #    if cluster_create_timeout:
    #        heat_timeout = cluster_create_timeout
    #    else:
    #        # no cluster_create_timeout value was passed in to the request
    #        # so falling back on configuration file value
    #        heat_timeout = cfg.CONF.cluster_heat.create_timeout
    #    fields = {
    #        'stack_name': stack_name,
    #        'parameters': heat_params,
    #        # 'environment_files': environment_files,
    #        'template': template,
    #        'files': tpl_files,
    #        'timeout_mins': heat_timeout
    #    }
    #    created_stack = osc.heat().stacks.create(**fields)

    #    return created_stack

    def create_nodegroup(self, context, nodegroup):
        osc = clients.OpenStackClients(context)
        stack = osc.heat().stacks.get(nodegroup.cluster.stack_id)
        heat_params = stack.parameters

        def update_json_value(key, ng_uuid, value):
            json_ = json.loads(heat_params[key])
            json_[ng_uuid] = value
            heat_params[key] = json.dumps(json_)

        # add the new nodegroup in the total count
        heat_params['ng_count'] = str(int(heat_params['ng_count'])+1)

        # ng's uuid is the key for all the ng specific configs so we need to
        # add it in the list. If there is an already removed index we can
        # reuse it, if not just append to the list.
        if heat_params['groups_to_remove'] != "":
            removed_indexes = heat_params['groups_to_remove'].split(',')
            # pop the first removed index
            new_index = int(removed_indexes[0])
            heat_params['groups_to_remove'] = ",".join(removed_indexes[1:])
            uuids = heat_params['ng_uuids'].split(',')
            # and then reuse it
            uuids[new_index] = nodegroup.uuid
            heat_params['ng_uuids'] = ",".join(uuids)
        else:
            heat_params['ng_uuids'] += ",%s" % nodegroup.uuid

        # add specific ng config
        update_json_value('node_counts', nodegroup.uuid, nodegroup.node_count)
        update_json_value('names', nodegroup.uuid, nodegroup.name)
        update_json_value('image_ids', nodegroup.uuid, nodegroup.image_id)
        update_json_value('flavors', nodegroup.uuid, nodegroup.flavor_id)
        update_json_value('nodes_to_remove', nodegroup.uuid, "")
        update_json_value('nodegroup_roles', nodegroup.uuid, nodegroup.role)

        fields = {
            'parameters': heat_params,
            'existing': True,
            'disable_rollback': True
        }
        osc.heat().stacks.update(nodegroup.cluster.stack_id, **fields)

    def delete_nodegroup(self, context, nodegroup):
        osc = clients.OpenStackClients(context)
        stack = osc.heat().stacks.get(nodegroup.cluster.stack_id)
        heat_params = stack.parameters

        heat_params['ng_count'] = str(int(heat_params['ng_count'])-1)

        uuids = heat_params['ng_uuids'].split(",")

        if nodegroup.uuid == uuids[-1]:
            # if it's last in the list just remove it
            heat_params['ng_uuids'] = ",".join(uuids[:-1])
        else:
            # if not we need to keep it to mainain the indexes
            heat_index = uuids.index(nodegroup.uuid)
            # add the ng's index to this list to remove it
            if heat_params['groups_to_remove'] == "":
                heat_params['groups_to_remove'] = str(heat_index)
            else:
                heat_params['groups_to_remove'] += ",%s" % heat_index

        def delete_json_value(key, ng_uuid):
            json_ = json.loads(heat_params[key])
            del json_[ng_uuid]
            heat_params[key] = json.dumps(json_)

        # delete specific ng config from all jsons
        delete_json_value('node_counts', nodegroup.uuid)
        delete_json_value('names', nodegroup.uuid)
        delete_json_value('image_ids', nodegroup.uuid)
        delete_json_value('flavors', nodegroup.uuid)
        delete_json_value('nodes_to_remove', nodegroup.uuid)
        delete_json_value('nodegroup_roles', nodegroup.uuid)

        fields = {
            'parameters': heat_params,
            'existing': True,
            'disable_rollback': True
        }
        osc.heat().stacks.update(nodegroup.cluster.stack_id, **fields)

    def update_nodegroup(self, context, nodegroup, node_to_remove=None):
        osc = clients.OpenStackClients(context)
        stack = osc.heat().stacks.get(nodegroup.cluster.stack_id)
        heat_params = stack.parameters

        def update_json_value(key, ng_uuid, value):
            json_ = json.loads(heat_params[key])
            json_[ng_uuid] = value
            heat_params[key] = json.dumps(json_)

        update_json_value('node_counts', nodegroup.uuid, nodegroup.node_count)
        update_json_value('names', nodegroup.uuid, nodegroup.name)
        update_json_value('image_ids', nodegroup.uuid, nodegroup.image_id)
        update_json_value('flavors', nodegroup.uuid, nodegroup.flavor_id)
        update_json_value('nodes_to_remove', nodegroup.uuid, "")
        update_json_value('nodegroup_roles', nodegroup.uuid, nodegroup.role)

        fields = {
            'parameters': heat_params,
            'existing': True,
            'disable_rollback': True
        }
        osc.heat().stacks.update(nodegroup.cluster.stack_id, **fields)


clean_params = {
    "master_index": "index",
    "api_public_address": "api_lb, floating_address",
    "api_private_address": "api_lb, address",
    "server_image": "server_image",
    "flavor": "flavor",
    "network_driver": "network_driver",
    "flannel_network_cidr": "flannel_network_cidr",
    "portal_network_cidr": "portal_network_cidr",
    "cluster_uuid": "cluster_uuid",
    "magnum_url": "magnum_url",
    "region_name": "region_name",
    "api_pool_id": "api_lb, pool_id",
    "etcd_pool_id": "etcd_lb, pool_id",
    "username": "username",
    "verify_ca": "verify_ca",
    "secgroup_kube_master_id": "secgroup_kube_master",
    "trustee_user_id": "trustee_user_id",
    "auth_url": "auth_url",
    "cloud_provider_enabled": "cloud_provider_enabled",
    "etcd_lb_vip": "[etcd_lb, address]",
    "dns_service_ip": "dns_service_ip",
    "openstack_ca": "openstack_ca",
    "nodes_server_group_id": "nodes_server_group",
    "ca_key": "ca_key",
    "pods_network_cidr": "pods_network_cidr",
    "kube_service_account_key": "kube_service_account_key",
    "kube_service_account_private_key": "kube_service_account_private_key",
    "prometheus_tag": "prometheus_tag",
    "grafana_tag": "grafana_tag",
    "heat_container_agent_tag": "heat_container_agent_tag",
    # minion specific params
    "kube_master_ip": "[api_address_lb_switch, private_ip]",
    "etcd_server_ip": "[etcd_address_lb_switch, private_ip]",
    "secgroup_kube_minion_id": "secgroup_kube_minion",
    "trustee_username": "trustee_username",
    "trustee_domain_id": "trustee_domain_id",
}

#params = {
#    "master_index": "index"
#    "api_public_address": "api_lb, floating_address",
#    "api_private_address": "api_lb, address",
#    "ssh_key_name": "ssh_key_name",
#    "server_image": "server_image",
#    "flavor": "flavor",
#    "external_network": "external_network",
#    "kube_allow_priv": "kube_allow_priv",
#    "etcd_volume_size": "etcd_volume_size",
#    "docker_volume_size": "docker_volume_size",
#    "docker_volume_type": "docker_volume_type",
#    "docker_storage_driver": "docker_storage_driver",
#    "cgroup_driver": "cgroup_driver",
#    "wait_condition_timeout": "wait_condition_timeout",
#    "network_driver": "network_driver",
#    "flannel_network_cidr": "flannel_network_cidr",
#    "flannel_network_subnetlen": "flannel_network_subnetlen",
#    "flannel_backend": "flannel_backend",
#    "system_pods_initial_delay": "system_pods_initial_delay",
#    "system_pods_timeout": "system_pods_timeout",
#    "portal_network_cidr": "portal_network_cidr",
#    "admission_control_list": "admission_control_list",
#    "discovery_url": "discovery_url",
#    "cluster_uuid": "cluster_uuid",
#    "magnum_url": "magnum_url",
#    "volume_driver": "volume_driver",
#    "region_name": "region_name",
#    "fixed_network": "network, fixed_network",
#    "fixed_subnet": "network, fixed_subnet",
#    "api_pool_id": "api_lb, pool_id",
#    "etcd_pool_id": "etcd_lb, pool_id",
#    "username": "username",
#    "password": "password",
#    "kubernetes_port": "kubernetes_port",
#    "tls_disabled": "tls_disabled",
#    "kube_dashboard_enabled": "kube_dashboard_enabled",
#    "influx_grafana_dashboard_enabled": "influx_grafana_dashboard_enabled",
#    "verify_ca": "verify_ca",
#    "secgroup_kube_master_id": "secgroup_kube_master",
#    "http_proxy": "http_proxy",
#    "https_proxy": "https_proxy",
#    "no_proxy": "no_proxy",
#    "kube_tag": "kube_tag",
#    "kube_version": "kube_version",
#    "etcd_tag": "etcd_tag",
#    "flannel_tag": "flannel_tag",
#    "kube_dashboard_version": "kube_dashboard_version",
#    "trustee_user_id": "trustee_user_id",
#    "auth_url": "auth_url",
#    "cloud_provider_enabled": "cloud_provider_enabled",
#    "insecure_registry_url": "insecure_registry_url",
#    "container_infra_prefix": "container_infra_prefix",
#    "etcd_lb_vip": "[etcd_lb, address]",
#    "dns_service_ip": "dns_service_ip",
#    "dns_cluster_domain": "dns_cluster_domain",
#    "openstack_ca": "openstack_ca",
#    "nodes_server_group_id": "nodes_server_group",
#    "availability_zone": "availability_zone",
#    "ca_key": "ca_key",
#    "cert_manager_api": "cert_manager_api",
#    "calico_tag": "calico_tag",
#    "calico_cni_tag": "calico_cni_tag",
#    "calico_kube_controllers_tag": "calico_kube_controllers_tag",
#    "calico_ipv4pool": "calico_ipv4pool",
#    "pods_network_cidr": "pods_network_cidr",
#    "ingress_controller": "ingress_controller",
#    "ingress_controller_role": "ingress_controller_role",
#    "kubelet_options": "kubelet_options",
#    "kubeapi_options": "kubeapi_options",
#    "kubeproxy_options": "kubeproxy_options",
#    "kubecontroller_options": "kubecontroller_options",
#    "kubescheduler_options": "kubescheduler_options",
#    "octavia_enabled": "octavia_enabled",
#    "kube_service_account_key": "kube_service_account_key",
#    "kube_service_account_private_key": "kube_service_account_private_key",
#    "prometheus_tag": "prometheus_tag",
#    "grafana_tag": "grafana_tag",
#    "heat_container_agent_tag": "heat_container_agent_tag",
#    # minion params
#    "kube_master_ip": "[api_address_lb_switch, private_ip]",
#    "etcd_server_ip": "[etcd_address_lb_switch, private_ip]",
#    "registry_enabled": "registry_enabled",
#    "registry_port": "registry_port",
#    "swift_region": "swift_region",
#    "registry_container": "registry_container",
#    "registry_insecure": "registry_insecure",
#    "registry_chunksize": "registry_chunksize",
#    "secgroup_kube_minion_id": "secgroup_kube_minion",
#    "trustee_username": "trustee_username",
#    "trustee_domain_id": "trustee_domain_id",
#}
