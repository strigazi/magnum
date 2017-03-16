#!/bin/sh

. /etc/sysconfig/heat-params

set -x

if [ "${IS_PRIMARY_MASTER}" = "True" ]; then
    /usr/bin/docker swarm init --advertise-addr "${SWARM_NODE_IP}"
else
    if [ "$TLS_DISABLED" = 'False'  ]; then
        tls="--tlsverify"
        tls=$tls" --tlscacert=/etc/docker/ca.crt"
        tls=$tls" --tlskey=/etc/docker/server.key"
        tls=$tls" --tlscert=/etc/docker/server.crt"
    fi
    token=$(/usr/bin/docker $tls -H $PRIMARY_MASTER_IP swarm join-token --quiet manager)
    /usr/bin/docker swarm join --token $token  $PRIMARY_MASTER_IP:2377
fi

UUID=$(uuidgen)
/usr/bin/curl -k -i -X POST -H "Content-Type: application/json" -H "X-Auth-Token: ${WAIT_HANDLE_TOKEN}" \
    --data-binary "{\"Status\": \"SUCCESS\", \"Reason\": \"Setup complete\", \"Data\": \"OK\", \"Id\": \"$UUID\"}" \
    "$WAIT_HANDLE_ENDPOINT"
