#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""add cluster_attributes table

Revision ID: 14b595466e7b
Revises: bc46ba6cf949
Create Date: 2016-11-08 14:31:35.975275

"""

# revision identifiers, used by Alembic.
revision = '14b595466e7b'
down_revision = 'bc46ba6cf949'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, MetaData, select
from oslo_utils import uuidutils


docker_storage_driver_enum = sa.Enum('devicemapper', 'overlay',
                                     name='docker_storage_driver')


def upgrade():
    # Create cluster_attributes tables
    op.create_table(
        'cluster_attributes',
        sa.Column('id', sa.String(length=36), nullable=False,
                  primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('apiserver_port', sa.Integer(), nullable=True),
        sa.Column('cluster_distro', sa.String(length=255), nullable=True),
        sa.Column('coe', sa.String(length=255), nullable=True),
        sa.Column('create_timeout', sa.Integer(), nullable=True),
        sa.Column('discovery_url', sa.String(length=255), nullable=True),
        sa.Column('dns_nameserver', sa.String(length=255), nullable=True),
        sa.Column('docker_storage_driver', docker_storage_driver_enum,
                  nullable=True),
        sa.Column('docker_volume_size', sa.Integer(), nullable=True),
        sa.Column('external_network', sa.String(length=255), nullable=True),
        sa.Column('fixed_network', sa.String(length=255), nullable=True),
        sa.Column('fixed_subnet', sa.String(length=255), nullable=True),
        sa.Column('flavor', sa.String(length=255), nullable=True),
        sa.Column('floating_ip_enabled', sa.Boolean(), default=True),
        sa.Column('http_proxy', sa.String(length=255), nullable=True),
        sa.Column('https_proxy', sa.String(length=255), nullable=True),
        sa.Column('image', sa.String(length=255), nullable=True),
        sa.Column('insecure_registry', sa.String(length=255), nullable=True),
        sa.Column('keypair', sa.String(length=255), nullable=True),
        sa.Column('labels', sa.Text(), nullable=True),
        sa.Column('master_count', sa.Integer(), nullable=True),
        sa.Column('master_flavor', sa.String(length=255), nullable=True),
        sa.Column('master_lb_enabled', sa.Boolean(), default=False),
        sa.Column('network_driver', sa.String(length=255), nullable=True),
        sa.Column('no_proxy', sa.String(length=255), nullable=True),
        sa.Column('node_count', sa.Integer(), nullable=True),
        sa.Column('registry_enabled', sa.Boolean(), default=False),
        sa.Column('server_type', sa.String(length=255), nullable=True,
                  server_default='vm'),
        sa.Column('tls_disabled', sa.Boolean(), default=False),
        sa.Column('volume_driver', sa.String(length=255), nullable=True),
        mysql_ENGINE='InnoDB',
        mysql_DEFAULT_CHARSET='UTF8'
    )

    # Add cluster_attributes_id column in cluster_template
    op.add_column('cluster_template',
                  sa.Column('cluster_attributes_id',
                            sa.String(length=36),
                            nullable=False))

    # Add cluster_attributes_id column in cluster
    op.add_column('cluster',
                  sa.Column('cluster_attributes_id',
                            sa.String(length=36),
                            nullable=False))

    # Transfer data from cluster_template to cluster_attributes
    # we need also to generate the ids in cluster_attributes
    ct_table = Table('cluster_template', MetaData(),
                     sa.Column('id', sa.Integer, primary_key=True),
                     sa.Column('cluster_attributes_id', sa.String())
                     )
    cluster_table = Table('cluster', MetaData(),
                          sa.Column('id', sa.Integer, primary_key=True),
                          sa.Column('cluster_attributes_id', sa.String())
                          )
    connection = op.get_bind()
    for row in connection.execute(select([ct_table.c.id])):
        connection.execute(
            ct_table.update().
            values(cluster_attributes_id=uuidutils.generate_uuid()).
            where(ct_table.c.id == row['id'])
        )
    for row in connection.execute(select([cluster_table.c.id])):
        connection.execute(
            cluster_table.update().
            values(cluster_attributes_id=uuidutils.generate_uuid()).
            where(cluster_table.c.id == row['id'])
        )

    op.create_unique_constraint("uniq_cluster_template0cluster_attributes_id",
                                "cluster_template", ["cluster_attributes_id"])

    op.create_unique_constraint("uniq_cluster0cluster_attributes_id",
                                "cluster", ["cluster_attributes_id"])

    op.execute("INSERT INTO cluster_attributes "
               "(id, "
               "apiserver_port, "
               "cluster_distro, "
               "coe, "
               "dns_nameserver, "
               "docker_storage_driver, "
               "docker_volume_size, "
               "external_network, "
               "fixed_network, "
               "fixed_subnet, "
               "flavor, "
               "floating_ip_enabled, "
               "http_proxy, "
               "https_proxy, "
               "image, "
               "insecure_registry, "
               "keypair, "
               "labels, "
               "master_flavor, "
               "master_lb_enabled, "
               "network_driver, "
               "no_proxy, "
               "registry_enabled, "
               "server_type, "
               "tls_disabled, "
               "volume_driver) "
               "SELECT "
               "cluster_attributes_id, "
               "apiserver_port, "
               "cluster_distro, "
               "coe, "
               "dns_nameserver, "
               "docker_storage_driver, "
               "docker_volume_size, "
               "external_network_id, "
               "fixed_network, "
               "fixed_subnet, "
               "flavor_id, "
               "floating_ip_enabled, "
               "http_proxy, "
               "https_proxy, "
               "image_id, "
               "insecure_registry, "
               "keypair_id, "
               "labels, "
               "master_flavor_id, "
               "master_lb_enabled, "
               "network_driver, "
               "no_proxy, "
               "registry_enabled, "
               "server_type, "
               "tls_disabled, "
               "volume_driver "
               "FROM cluster_template"
               )

    op.execute("INSERT INTO cluster_attributes "
               "(id, "
               "create_timeout, "
               "discovery_url, "
               "keypair, "
               "master_count, "
               "node_count) "
               "SELECT "
               "cluster_attributes_id, "
               "create_timeout, "
               "discovery_url, "
               "keypair, "
               "master_count, "
               "node_count "
               "FROM cluster"
               )

    op.create_foreign_key('cluster_template_cluster_attributes',
                          'cluster_template', 'cluster_attributes',
                          ['cluster_attributes_id'], ['id'], ondelete='CASCADE')

    op.create_foreign_key('cluster_cluster_attributes',
                          'cluster', 'cluster_attributes',
                          ['cluster_attributes_id'], ['id'], ondelete='CASCADE')
