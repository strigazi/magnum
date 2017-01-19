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

from oslo_utils import uuidutils
from oslo_versionedobjects import fields

from magnum.common import exception
from magnum.db import api as dbapi
from magnum.objects import base
from magnum.objects import fields as m_fields


@base.MagnumObjectRegistry.register
class ClusterAttributes(base.MagnumPersistentObject, base.MagnumObject,
                        base.MagnumObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.StringField(nullable=True),
        'image': fields.StringField(nullable=True),
        'flavor': fields.StringField(nullable=True),
        'master_flavor': fields.StringField(nullable=True),
        'keypair': fields.StringField(nullable=True),
        'dns_nameserver': fields.StringField(nullable=True),
        'external_network': fields.StringField(nullable=True),
        'fixed_network': fields.StringField(nullable=True),
        'fixed_subnet': fields.StringField(nullable=True),
        'network_driver': fields.StringField(nullable=True),
        'volume_driver': fields.StringField(nullable=True),
        'apiserver_port': fields.IntegerField(nullable=True),
        'docker_volume_size': fields.IntegerField(nullable=True),
        'docker_storage_driver': m_fields.DockerStorageDriverField(
            nullable=True),
        'cluster_distro': fields.StringField(nullable=True),
        'coe': m_fields.ClusterTypeField(nullable=True),
        'http_proxy': fields.StringField(nullable=True),
        'https_proxy': fields.StringField(nullable=True),
        'no_proxy': fields.StringField(nullable=True),
        'registry_enabled': fields.BooleanField(default=False),
        'labels': fields.DictOfStringsField(nullable=True),
        'tls_disabled': fields.BooleanField(default=False),
        'server_type': fields.StringField(nullable=True),
        'insecure_registry': fields.StringField(nullable=True),
        'master_lb_enabled': fields.BooleanField(default=False),
        'floating_ip_enabled': fields.BooleanField(default=True),
        'node_count': fields.IntegerField(nullable=True),
        'master_count': fields.IntegerField(nullable=True),
        'discovery_url': fields.StringField(nullable=True),
        'create_timeout': fields.IntegerField(nullable=True),

    }

    @staticmethod
    def _from_db_object(cluster_attributes, db_cluster_attributes):
        """Converts a database entity to a formal object."""
        for field in cluster_attributes.fields:
            cluster_attributes[field] = db_cluster_attributes[field]

        cluster_attributes.obj_reset_changes()
        return cluster_attributes

    @base.remotable_classmethod
    def get(cls, context, cluster_attributes_id):
        """Find and return a ClusterAttributes object based on its id.

        :param cluster_attributes_id: the id of a ClusterAttributes entry.
        :param context: Security context
        :returns: a :class:`ClusterAttributes` object.
        """
        if uuidutils.is_uuid_like(cluster_attributes_id):
            return cls.get_by_id(context, cluster_attributes_id)
        else:
            raise exception.InvalidIdentity(identity=cluster_attributes_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, cluster_attributes_id):
        """Find and return ClusterAttributes object based on its integer id.

        :param cluster_attributes_id: the id of a ClusterAttributes.
        :param context: Security context
        :returns: a :class:`ClusterAttributes` object.
        """
        db_cluster_attributes = cls.dbapi.get_cluster_attributes_by_id(
            context, cluster_attributes_id)
        cluster_attributes = ClusterAttributes._from_db_object(
            cls(context),
            db_cluster_attributes)
        return cluster_attributes

    @base.remotable
    def create(self, context=None):
        """Create a ClusterAttributes record in the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: ClusterAttributes(context)

        """
        values = self.obj_get_changes()
        db_cluster_attributes = self.dbapi.create_cluster_attributes(values)
        self._from_db_object(self, db_cluster_attributes)

    @base.remotable
    def destroy(self, context=None):
        """Delete the ClusterAttributes from the DB.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: ClusterAttributes(context)
        """
        self.dbapi.destroy_cluster_attributes(self.uuid)
        self.obj_reset_changes()

    @base.remotable
    def save(self, context=None):
        """Save updates to this ClusterAttributes.

        Updates will be made column by column based on the result
        of self.what_changed().

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: ClusterAttributes(context)
        """
        updates = self.obj_get_changes()
        self.dbapi.update_cluster_attributes(self.uuid, updates)

        self.obj_reset_changes()

    @base.remotable
    def refresh(self, context=None):
        """Loads updates for this ClusterAttributes.

        Loads a ClusterAttributes with the same uuid from the database and
        checks for updated attributes. Updates are applied from
        the loaded ClusterAttributes column by column, if there are any
        updates.

        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: ClusterAttributes(context)
        """
        current = self.__class__.get_by_uuid(self._context, uuid=self.uuid)
        for field in self.fields:
            if self.obj_attr_is_set(field) and self[field] != current[field]:
                self[field] = current[field]
