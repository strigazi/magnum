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
"""add driver field

Revision ID: 8ff3aa54a46c
Revises: bc46ba6cf949
Create Date: 2016-12-09 14:13:21.576050

"""

# revision identifiers, used by Alembic.
revision = '8ff3aa54a46c'
down_revision = 'bc46ba6cf949'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('cluster_template',
                  sa.Column('driver', sa.String(length=255),
                            nullable=False))
