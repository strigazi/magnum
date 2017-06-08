#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import pecan

from magnum.api.controllers import base
from magnum.api.controllers.v1 import types
from magnum.api import expose
from magnum.api import utils as api_utils
from magnum.common import policy


class UpgradeActionController(base.Controller):
    """REST controller for cluster upgrade."""
    def __init__(self):
        super(UpgradeActionController, self).__init__()

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def patch(self, cluster_ident):
        """Upgrade a cluster.

        :param cluster_ident: UUID of a cluster or logical name of the cluster.
        """
        context = pecan.request.context
        cluster = api_utils.get_resource('Cluster', cluster_ident)
        policy.enforce(context, 'cluster:upgrade', cluster,
                       action='cluster:upgrade')

        pecan.request.rpcapi.cluster_upgrade(cluster.uuid)


class ActionsController(base.Controller):
    """REST controller for lifecycle operations for a Cluster."""
    def __init__(self):
        super(ActionsController, self).__init__()

    upgrade = UpgradeActionController()
