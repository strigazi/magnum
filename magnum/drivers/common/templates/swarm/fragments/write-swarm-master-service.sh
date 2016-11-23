#!/bin/sh

cat > /etc/systemd/system/swarm-manager.service << END_SERVICE
[Unit]
Description=Swarm Manager
After=docker.service etcd.service
Requires=docker.service
OnFailure=swarm-manager-failure.service

[Service]
Type=oneshot
TimeoutStartSec=0
ExecStart=/usr/bin/docker swarm init --advertise-addr $NODE_IP
ExecStartPost=/usr/bin/curl -k -i -X POST -H 'Content-Type: application/json' -H 'X-Auth-Token: $WAIT_HANDLE_TOKEN' \\
  --data-binary "'"'{"Status": "SUCCESS", "Reason": "Setup complete", "Data": "OK", "UniqueId": "00000"}'"'" \\
  "$WAIT_HANDLE_ENDPOINT"

[Install]
WantedBy=multi-user.target
END_SERVICE

chown root:root /etc/systemd/system/swarm-manager.service
chmod 644 /etc/systemd/system/swarm-manager.service
