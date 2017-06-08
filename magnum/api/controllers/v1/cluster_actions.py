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
from wsme import types as wtypes

from magnum.api.controllers import base
from magnum.api.controllers.v1 import types
from magnum.api import expose
from magnum.api import utils as api_utils
from magnum.common import policy


class ClusterUpgradeRequest(base.APIBase):
    """API object for handling upgrade requests.

    This class enforces type checking and value constraints.
    """

    max_batch_size = wtypes.IntegerType(minimum=1)
    """Max batch size of nodes to be upraded in parallel"""

    nodegroup = wtypes.StringType(min_length=1, max_length=255)
    """Group of nodes to be uprgaded (master or node)"""

    parameters = wtypes.DictType(str, str)
    """Parameters to be modified"""


class UpgradeActionController(base.Controller):
    """REST controller for cluster upgrade."""
    def __init__(self):
        super(UpgradeActionController, self).__init__()

    @expose.expose(None, types.uuid_or_name,
                   body=ClusterUpgradeRequest, status_code=204)
    def patch(self, cluster_ident, cluster_upgrade_req):
        """Upgrade a cluster.

        :param cluster_ident: UUID of a cluster or logical name of the cluster.
        """
        context = pecan.request.context
        cluster = api_utils.get_resource('Cluster', cluster_ident)
        policy.enforce(context, 'cluster:upgrade', cluster,
                       action='cluster:upgrade')

        pecan.request.rpcapi.cluster_upgrade(cluster)


class ActionsController(base.Controller):
    """REST controller for lifecycle operations for a Cluster."""
    def __init__(self):
        super(ActionsController, self).__init__()

    upgrade = UpgradeActionController()
