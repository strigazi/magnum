#!/bin/bash

set +x
. /etc/sysconfig/heat-params

set -x

ssh_cmd="ssh -F /srv/magnum/.ssh/config root@localhost"

echo "configuring kubernetes (minion)"

if [ ! -z "$HTTP_PROXY" ]; then
    export HTTP_PROXY
fi

if [ ! -z "$HTTPS_PROXY" ]; then
    export HTTPS_PROXY
fi

if [ ! -z "$NO_PROXY" ]; then
    export NO_PROXY
fi

_prefix=${CONTAINER_INFRA_PREFIX:-docker.io/openstackmagnum/}

_addtl_mounts=''
${ssh_cmd} mkdir -p /opt/cni
_addtl_mounts=',{"type":"bind","source":"/opt/cni","destination":"/opt/cni","options":["bind","rw","slave","mode=777"]}'

if [ "$NETWORK_DRIVER" = "calico" ]; then
    if [ "`systemctl status NetworkManager.service | grep -o "Active: active"`" = "Active: active" ]; then
        CALICO_NM=/etc/NetworkManager/conf.d/calico.conf
        [ -f ${CALICO_NM} ] || {
        echo "Writing File: $CALICO_NM"
        mkdir -p $(dirname ${CALICO_NM})
        cat << EOF > ${CALICO_NM}
[keyfile]
unmanaged-devices=interface-name:cali*;interface-name:tunl*
EOF
}
        ${ssh_cmd} systemctl restart NetworkManager
    fi
fi

mkdir -p /srv/magnum/kubernetes/
cat > /srv/magnum/kubernetes/install-kubernetes.sh <<EOF
#!/bin/bash -x
atomic install --storage ostree --system --system-package=no --set=ADDTL_MOUNTS='${_addtl_mounts}' --name=kubelet ${_prefix}kubernetes-kubelet:${KUBE_TAG}
atomic install --storage ostree --system --system-package=no --name=kube-proxy ${_prefix}kubernetes-proxy:${KUBE_TAG}
EOF
chmod +x /srv/magnum/kubernetes/install-kubernetes.sh
$ssh_cmd "/srv/magnum/kubernetes/install-kubernetes.sh"
