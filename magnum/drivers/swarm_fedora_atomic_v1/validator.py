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

from magnum.api import validation
import magnum.conf

CONF = magnum.conf.CONF


class SwarmValidator(validation.Validator):

    supported_network_drivers = ['docker', 'flannel']
    supported_server_types = ['vm', 'bm']
    allowed_network_drivers = (CONF.cluster_template.
                               swarm_allowed_network_drivers)
    default_network_driver = (CONF.cluster_template.
                              swarm_default_network_driver)

    supported_volume_driver = ['rexray']
