#!/bin/sh

. /etc/sysconfig/heat-params

set -x

if [ "${TLS_DISABLED}" = 'False'  ]; then
    tls="--tlsverify"
    tls=$tls" --tlscacert=/etc/docker/ca.crt"
    tls=$tls" --tlskey=/etc/docker/server.key"
    tls=$tls" --tlscert=/etc/docker/server.crt"
fi
token=$(/usr/bin/docker $tls -H $SWARM_API_IP swarm join-token --quiet worker)
/usr/bin/docker swarm join --token $token  $SWARM_API_IP:2377

UUID=$(uuidgen)
/usr/bin/curl -k -i -X POST -H "Content-Type: application/json" -H "X-Auth-Token: ${WAIT_HANDLE_TOKEN}" \
    --data-binary "{\"Status\": \"SUCCESS\", \"Reason\": \"Node joined swarm\", \"Data\": \"OK\", \"Id\": \"$UUID\"}" \
    "$WAIT_HANDLE_ENDPOINT"
