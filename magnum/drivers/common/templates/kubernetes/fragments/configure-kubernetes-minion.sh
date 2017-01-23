#!/bin/sh

. /etc/sysconfig/heat-params

echo "configuring kubernetes (minion)"

if [ -z "$KUBE_NODE_IP" ]; then
  # FIXME(yuanying): Set KUBE_NODE_IP correctly
  KUBE_NODE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
fi

CERT_DIR=/srv/kubernetes
PROTOCOL=https
FLANNEL_OPTIONS="-etcd-cafile $CERT_DIR/ca.crt \
-etcd-certfile $CERT_DIR/client.crt \
-etcd-keyfile $CERT_DIR/client.key"
ETCD_CURL_OPTIONS="--cacert $CERT_DIR/ca.crt \
--cert $CERT_DIR/client.crt --key $CERT_DIR/client.key"
ETCD_SERVER_IP=${ETCD_SERVER_IP:-$KUBE_MASTER_IP}
KUBE_PROTOCOL="https"
KUBE_CONFIG=""
FLANNELD_CONFIG=/etc/sysconfig/flanneld

if [ "$TLS_DISABLED" = "True" ]; then
    PROTOCOL=http
    FLANNEL_OPTIONS=""
    ETCD_CURL_OPTIONS=""
fi

sed -i '/FLANNEL_OPTIONS/'d $FLANNELD_CONFIG

cat >> $FLANNELD_CONFIG <<EOF
FLANNEL_OPTIONS="$FLANNEL_OPTIONS"
EOF

if [ "$TLS_DISABLED" = "True" ]; then
    KUBE_PROTOCOL="http"
else
    KUBE_CONFIG="--kubeconfig=/srv/kubernetes/kubeconfig.yaml"
fi
KUBE_MASTER_URI="$KUBE_PROTOCOL://$KUBE_MASTER_IP:$KUBE_API_PORT"

sed -i '
  /^KUBE_ALLOW_PRIV=/ s/=.*/="--allow_privileged='"$KUBE_ALLOW_PRIV"'"/
  /^KUBE_ETCD_SERVERS=/ s|=.*|="--etcd_servers=http://'"$ETCD_SERVER_IP"':2379"|
  /^KUBE_MASTER=/ s|=.*|="--master='"$KUBE_MASTER_URI"'"|
' /etc/kubernetes/config

# NOTE:  Kubernetes plugin for Openstack requires that the node name registered
# in the kube-apiserver be the same as the Nova name of the instance, so that
# the plugin can use the name to query for attributes such as IP, etc.
# The hostname of the node is set to be the Nova name of the instance, and
# the option --hostname-override for kubelet uses the hostname to register the node.
# Using any other name will break the load balancer and cinder volume features.
HOSTNAME=$(hostname -I | cut -d' ' -f1)
KUBELET_ARGS="--config=/etc/kubernetes/manifests --cadvisor-port=4194 --hostname-override=${HOSTNAME} --cluster-dns=10.254.10.10 --cluster-domain=cluster.local --volume-plugin-dir /var/lib/kubelet/plugins/volume/exec ${KUBE_CONFIG}"

if [ -n "${INSECURE_REGISTRY_URL}" ]; then
    KUBELET_ARGS="${KUBELET_ARGS} --pod-infra-container-image=${INSECURE_REGISTRY_URL}/google_containers/pause\:0.8.0"
    echo "INSECURE_REGISTRY='--insecure-registry ${INSECURE_REGISTRY_URL}'" >> /etc/sysconfig/docker
fi

sed -i '
  /^KUBELET_ADDRESS=/ s/=.*/="--address=0.0.0.0"/
  /^KUBELET_HOSTNAME=/ s/=.*/=""/
  /^KUBELET_API_SERVER=/ s|=.*|="--api_servers='"$KUBE_MASTER_URI"'"|
  /^KUBELET_ARGS=/ s|=.*|="'"${KUBELET_ARGS}"'"|
' /etc/kubernetes/kubelet

sed -i '
  /^KUBE_PROXY_ARGS=/ s|=.*|='"$KUBE_CONFIG"'|
' /etc/kubernetes/proxy

if [ "$NETWORK_DRIVER" = "flannel" ]; then
    sed -i '
        /^FLANNEL_ETCD_ENDPOINTS=/ s|=.*|="'"$PROTOCOL"'://'"$ETCD_SERVER_IP"':2379"|
    ' $FLANNELD_CONFIG

    # Make sure etcd has a flannel configuration
    . $FLANNELD_CONFIG
    until curl -sf $ETCD_CURL_OPTIONS \
        "$FLANNEL_ETCD_ENDPOINTS/v2/keys${FLANNEL_ETCD_PREFIX}/config?quorum=false&recursive=false&sorted=false"
    do
        echo "Waiting for flannel configuration in etcd..."
        sleep 5
    done
fi

if [ "$VOLUME_DRIVER" = "cinder" ]; then
    CLOUD_CONFIG=/etc/kubernetes/kube_openstack_config
    KUBERNETES=/etc/kubernetes
    if [ ! -d ${KUBERNETES} -o ! -f ${CLOUD_CONFIG} ]; then
        sudo mkdir -p $KUBERNETES
    fi
    AUTH_URL=${AUTH_URL/v3/v2.0}
cat > $CLOUD_CONFIG <<EOF
[Global]
auth-url=$AUTH_URL
username=$USERNAME
password=$PASSWORD
region=$REGION_NAME
tenant-name=$TENANT_NAME
EOF

cat << _EOC_ >> /etc/kubernetes/kubelet
#KUBELET_ARGS="$KUBELET_ARGS --cloud-provider=openstack --cloud-config=/etc/kubernetes/kube_openstack_config"
_EOC_

    if [ ! -f /usr/bin/udevadm ]; then
        sudo ln -s /sbin/udevadm /usr/bin/udevadm
    fi

fi

cat >> /etc/environment <<EOF
KUBERNETES_MASTER=$KUBE_MASTER_URI
EOF

hostname `hostname | sed 's/.novalocal//'`
