#!/bin/sh

. /etc/sysconfig/heat-params

myip="$SWARM_NODE_IP"

cat > /etc/systemd/system/swarm-token.service << EOF
[Unit]
Description=Get Swarm Token
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/sh -c "/usr/bin/echo -n TOKEN= > /etc/sysconfig/swarm-token.env"
ExecStart=/usr/bin/sh -c "/usr/bin/docker \\
--tlsverify \\
--tlscacert=/etc/docker/ca.crt \\
--tlskey=/etc/docker/server.key \\
--tlscert=/etc/docker/server.crt \\
-H $SWARM_API_IP \\
swarm join-token worker | grep token | awk '{print \$2}' >> /etc/sysconfig/swarm-token.env"

[Install]
WantedBy=multi-user.target
EOF

chown root:root /etc/systemd/system/swarm-token.service
chmod 644 /etc/systemd/system/swarm-token.service

systemctl daemon-reload

CONF_FILE=/etc/systemd/system/swarm-agent.service

cat > $CONF_FILE << EOF
[Unit]
Description=Swarm Agent
After=swarm-token.service
Requires=swarm-token.service

[Service]
Type=oneshot
TimeoutStartSec=0
EnvironmentFile=/etc/sysconfig/swarm-token.env
ExecStart=/usr/bin/docker swarm join --token \$TOKEN $SWARM_API_IP:2377

[Install]
WantedBy=multi-user.target
EOF

chown root:root $CONF_FILE
chmod 644 $CONF_FILE

SCRIPT=/usr/local/bin/notify-heat

cat > $SCRIPT << EOF
#!/bin/sh
curl -k -i -X POST -H 'Content-Type: application/json' -H 'X-Auth-Token: $WAIT_HANDLE_TOKEN' \
    --data-binary "'"'{"Status": "SUCCESS", "Reason": "Swarm agent ready", "Data": "OK", "UniqueId": "00000"}'"'" \
    "$WAIT_HANDLE_ENDPOINT"
EOF

chown root:root $SCRIPT
chmod 755 $SCRIPT
