#!/bin/sh
KUBE_API_PUBLIC_ADDRESS_TMP=$KUBE_API_PUBLIC_ADDRESS
KUBE_API_PRIVATE_ADDRESS_TMP=$KUBE_API_PRIVATE_ADDRESS
KUBE_NODE_IP_TMP=$KUBE_NODE_IP

cat > /etc/sysconfig/heat-params << END
KUBE_API_PUBLIC_ADDRESS="${KUBE_API_PUBLIC_ADDRESS_TMP:-$(hostname -I | cut -d' ' -f1)}"
KUBE_API_PRIVATE_ADDRESS="${KUBE_API_PRIVATE_ADDRESS_TMP:-$(hostname -I | cut -d' ' -f1)}"
KUBE_API_PORT="$KUBE_API_PORT"
KUBE_NODE_PUBLIC_IP="${KUBE_NODE_IP_TMP:-$(hostname -I | cut -d' ' -f1)}"
KUBE_NODE_IP="${KUBE_NODE_IP_TMP:-$(hostname -I | cut -d' ' -f1)}"
KUBE_ALLOW_PRIV="$KUBE_ALLOW_PRIV"
ENABLE_CINDER="$ENABLE_CINDER"
DOCKER_VOLUME="$DOCKER_VOLUME"
DOCKER_STORAGE_DRIVER="$DOCKER_STORAGE_DRIVER"
NETWORK_DRIVER="$NETWORK_DRIVER"
FLANNEL_NETWORK_CIDR="$FLANNEL_NETWORK_CIDR"
FLANNEL_NETWORK_SUBNETLEN="$FLANNEL_NETWORK_SUBNETLEN"
FLANNEL_BACKEND="$FLANNEL_BACKEND"
PORTAL_NETWORK_CIDR="$PORTAL_NETWORK_CIDR"
ETCD_DISCOVERY_URL="$ETCD_DISCOVERY_URL"
USERNAME="$USERNAME"
PASSWORD="$PASSWORD"
TENANT_NAME="$TENANT_NAME"
CLUSTER_SUBNET="$CLUSTER_SUBNET"
TLS_DISABLED="$TLS_DISABLED"
CLUSTER_UUID="$CLUSTER_UUID"
MAGNUM_URL="$MAGNUM_URL"
HTTP_PROXY="$HTTP_PROXY"
HTTPS_PROXY="$HTTPS_PROXY"
NO_PROXY="$NO_PROXY"
WAIT_CURL="$WAIT_CURL"
KUBE_VERSION="$KUBE_VERSION"
TRUSTEE_USER_ID="$TRUSTEE_USER_ID"
TRUSTEE_PASSWORD="$TRUSTEE_PASSWORD"
TRUST_ID="$TRUST_ID"
AUTH_URL="$AUTH_URL"
INSECURE_REGISTRY_URL="$INSECURE_REGISTRY_URL"
END

chown root:root /etc/sysconfig/heat-params
chmod 644 /etc/sysconfig/heat-params
