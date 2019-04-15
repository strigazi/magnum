#!/bin/sh

set +x
. /etc/sysconfig/heat-params
set -x
set -e
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

sed -i '
    /^KUBE_ALLOW_PRIV=/ s/=.*/="--allow-privileged='"$KUBE_ALLOW_PRIV"'"/
    /^KUBE_MASTER=/ s|=.*|=|
' /etc/kubernetes/config

CERT_DIR=/etc/kubernetes/certs
PROTOCOL=https
KUBE_PROTOCOL="https"
KUBELET_KUBECONFIG=/etc/kubernetes/kubelet-config.yaml
PROXY_KUBECONFIG=/etc/kubernetes/proxy-config.yaml

if [ "$TLS_DISABLED" = "True" ]; then
    PROTOCOL=http
    KUBE_PROTOCOL="http"
fi

KUBE_MASTER_URI="$KUBE_PROTOCOL://$KUBE_MASTER_IP:$KUBE_API_PORT"

if [ -z "${KUBE_NODE_IP}" ]; then
    KUBE_NODE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
fi
HOSTNAME_OVERRIDE=$(cat /etc/hostname  | sed 's/.novalocal//')
cat << EOF >> ${KUBELET_KUBECONFIG}
apiVersion: v1
clusters:
- cluster:
    certificate-authority: ${CERT_DIR}/ca.crt
    server: ${KUBE_MASTER_URI}
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: system:node:${HOSTNAME_OVERRIDE}
  name: default
current-context: default
kind: Config
preferences: {}
users:
- name: system:node:${HOSTNAME_OVERRIDE}
  user:
    as-user-extra: {}
    client-certificate: ${CERT_DIR}/kubelet.crt
    client-key: ${CERT_DIR}/kubelet.key
EOF
cat << EOF >> ${PROXY_KUBECONFIG}
apiVersion: v1
clusters:
- cluster:
    certificate-authority: ${CERT_DIR}/ca.crt
    server: ${KUBE_MASTER_URI}
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kube-proxy
  name: default
current-context: default
kind: Config
preferences: {}
users:
- name: kube-proxy
  user:
    as-user-extra: {}
    client-certificate: ${CERT_DIR}/proxy.crt
    client-key: ${CERT_DIR}/proxy.key
EOF

if [ "$TLS_DISABLED" = "True" ]; then
    sed -i 's/^.*user:$//' ${KUBELET_KUBECONFIG}
    sed -i 's/^.*client-certificate.*$//' ${KUBELET_KUBECONFIG}
    sed -i 's/^.*client-key.*$//' ${KUBELET_KUBECONFIG}
    sed -i 's/^.*certificate-authority.*$//' ${KUBELET_KUBECONFIG}
fi

chmod 0644 ${KUBELET_KUBECONFIG}
chmod 0644 ${PROXY_KUBECONFIG}

# NOTE:  Kubernetes plugin for Openstack requires that the node name registered
# in the kube-apiserver be the same as the Nova name of the instance, so that
# the plugin can use the name to query for attributes such as IP, etc.
# The hostname of the node is set to be the Nova name of the instance, and
# the option --hostname-override for kubelet uses the hostname to register the node.
# Using any other name will break the load balancer and cinder volume features.
mkdir -p /etc/kubernetes/manifests
KUBELET_ARGS="--pod-manifest-path=/etc/kubernetes/manifests --cadvisor-port=0 --kubeconfig ${KUBELET_KUBECONFIG} --hostname-override=${HOSTNAME_OVERRIDE}"
KUBELET_ARGS="${KUBELET_ARGS} --address=${KUBE_NODE_IP} --port=10250 --read-only-port=0 --anonymous-auth=false --authorization-mode=Webhook --authentication-token-webhook=true"
KUBELET_ARGS="${KUBELET_ARGS} --cluster_dns=${DNS_SERVICE_IP} --cluster_domain=${DNS_CLUSTER_DOMAIN}"
KUBELET_ARGS="${KUBELET_ARGS} --volume-plugin-dir=/var/lib/kubelet/volumeplugins"
KUBELET_ARGS="${KUBELET_ARGS} ${KUBELET_OPTIONS}"

if [ "$(echo "${CLOUD_PROVIDER_ENABLED}" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    KUBELET_ARGS="${KUBELET_ARGS} --cloud-provider=external"
fi

## Workaround for Cinder support (fixed in k8s >= 1.6)
#if [ ! -f /usr/bin/udevadm ]; then
#    ln -s /sbin/udevadm /usr/bin/udevadm
#fi

# For using default log-driver, other options should be ignored
sed -i 's/\-\-log\-driver\=journald//g' /etc/sysconfig/docker

KUBELET_ARGS="${KUBELET_ARGS} --pod-infra-container-image=${CONTAINER_INFRA_PREFIX:-gcr.io/google_containers/}pause:3.0"
if [ -n "${INSECURE_REGISTRY_URL}" ]; then
    echo "INSECURE_REGISTRY='--insecure-registry ${INSECURE_REGISTRY_URL}'" >> /etc/sysconfig/docker
fi

KUBELET_ARGS="${KUBELET_ARGS} --client-ca-file=${CERT_DIR}/ca.crt --tls-cert-file=${CERT_DIR}/kubelet.crt --tls-private-key-file=${CERT_DIR}/kubelet.key"

# specified cgroup driver
KUBELET_ARGS="${KUBELET_ARGS} --cgroup-driver=${CGROUP_DRIVER}"

${ssh_cmd} systemctl stop docker
${ssh_cmd} systemctl disable docker
if ${ssh_cmd} "cat /usr/lib/systemd/system/docker.service" | grep 'native.cgroupdriver'; then
        ${ssh_cmd} cp /usr/lib/systemd/system/docker.service /etc/systemd/system/
        sed -i "s/\(native.cgroupdriver=\)\w\+/\1$CGROUP_DRIVER/" \
                /etc/systemd/system/docker.service
else
        cat > /etc/systemd/system/docker.service.d/cgroupdriver.conf << EOF
ExecStart=---exec-opt native.cgroupdriver=$CGROUP_DRIVER
EOF

fi

${ssh_cmd} systemctl daemon-reload
${ssh_cmd} systemctl enable docker

cat > /etc/kubernetes/get_require_kubeconfig.sh <<EOF
#!/bin/bash

KUBE_VERSION=\$(kubelet --version | awk '{print \$2}')
min_version=v1.8.0
if [[ "\${min_version}" != \$(echo -e "\${min_version}\n\${KUBE_VERSION}" | sort -s -t. -k 1,1 -k 2,2n -k 3,3n | head -n1) && "\${KUBE_VERSION}" != "devel" ]]; then
    echo "--require-kubeconfig"
fi
EOF
chmod +x /etc/kubernetes/get_require_kubeconfig.sh

KUBELET_ARGS="${KUBELET_ARGS} --network-plugin=cni --cni-conf-dir=/etc/cni/net.d --cni-bin-dir=/opt/cni/bin"

sed -i '
    /^KUBELET_ADDRESS=/ s/=.*/="--address=0.0.0.0"/
    /^KUBELET_HOSTNAME=/ s/=.*/=""/
    s/^KUBELET_API_SERVER=.*$//
    /^KUBELET_ARGS=/ s|=.*|="'"\$(/etc/kubernetes/get_require_kubeconfig.sh) ${KUBELET_ARGS}"'"|
' /etc/kubernetes/kubelet

cat > /etc/kubernetes/proxy << EOF
KUBE_PROXY_ARGS="--kubeconfig=${PROXY_KUBECONFIG} --cluster-cidr=${PODS_NETWORK_CIDR}"
EOF

${ssh_cmd} "hostname \$(hostname | sed 's/.novalocal//')"
${ssh_cmd} systemctl start docker kubelet kube-proxy --no-block