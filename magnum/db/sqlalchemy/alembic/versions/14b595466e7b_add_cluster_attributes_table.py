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


docker_storage_driver_enum = sa.Enum('devicemapper', 'overlay',
                                     name='docker_storage_driver')


def upgrade():
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

    op.add_column('cluster',
                  sa.Column('cluster_attributes_id',
                            sa.String(length=36),
                            sa.ForeignKey('cluster_attributes.id',
                                          ondelete='CASCADE'),
                            nullable=False))

    op.create_unique_constraint("uniq_cluster0cluster_attributes_id",
                                "cluster", ["cluster_attributes_id"])

    op.add_column('cluster_template',
                  sa.Column('cluster_attributes_id',
                            sa.String(length=36),
                            sa.ForeignKey('cluster_attributes.id',
                                          ondelete='CASCADE'),
                            nullable=False))

    op.create_unique_constraint("uniq_cluster_template0cluster_attributes_id",
                                "cluster_template", ["cluster_attributes_id"])
