#!/bin/sh

set +x
. /etc/sysconfig/heat-params

set -x

ssh_cmd="ssh -F /srv/magnum/.ssh/config root@localhost"

# make sure we pick up any modified unit files
systemctl daemon-reload

echo "starting services"
for service in etcd docker kube-apiserver kube-controller-manager kube-scheduler kubelet kube-proxy; do
    echo "activating service $service"
    systemctl enable $service
    systemctl --no-block start $service
done
