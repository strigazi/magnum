#!/bin/bash

set +x
. /etc/sysconfig/heat-params

set -x

ssh_cmd="ssh -F /srv/magnum/.ssh/config root@localhost"

echo "configuring kubernetes (master)"

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

${ssh_cmd} atomic install --storage ostree --system --system-package=no --name=kube-apiserver ${_prefix}kubernetes-apiserver:${KUBE_TAG}
${ssh_cmd} atomic install --storage ostree --system --system-package=no --name=kube-controller-manager ${_prefix}kubernetes-controller-manager:${KUBE_TAG}
${ssh_cmd} atomic install --storage ostree --system --system-package=no --name=kube-scheduler ${_prefix}kubernetes-scheduler:${KUBE_TAG}

CERT_DIR=/etc/kubernetes/certs

sed -i '
    /^KUBE_ALLOW_PRIV=/ s/=.*/="--allow-privileged='"$KUBE_ALLOW_PRIV"'"/
    /^KUBE_MASTER=/ s|=.*|="--master=http://127.0.0.1:8080"|
' /etc/kubernetes/config

KUBE_API_ARGS="--runtime-config=api/all=true"
KUBE_API_ARGS="$KUBE_API_ARGS --kubelet-preferred-address-types=InternalIP,Hostname,ExternalIP"
KUBE_API_ARGS="$KUBE_API_ARGS $KUBEAPI_OPTIONS"
if [ "$TLS_DISABLED" == "True" ]; then
    KUBE_API_ADDRESS="--insecure-bind-address=0.0.0.0 --insecure-port=$KUBE_API_PORT"
else
    KUBE_API_ADDRESS="--bind-address=0.0.0.0 --secure-port=$KUBE_API_PORT"
    # insecure port is used internaly
    KUBE_API_ADDRESS="$KUBE_API_ADDRESS --insecure-bind-address=127.0.0.1 --insecure-port=8080"
    KUBE_API_ARGS="$KUBE_API_ARGS --authorization-mode=Node,RBAC --tls-cert-file=$CERT_DIR/server.crt"
    KUBE_API_ARGS="$KUBE_API_ARGS --tls-private-key-file=$CERT_DIR/server.key"
    KUBE_API_ARGS="$KUBE_API_ARGS --client-ca-file=$CERT_DIR/ca.crt"
    KUBE_API_ARGS="$KUBE_API_ARGS --service-account-key-file=${CERT_DIR}/service_account.key"
    KUBE_API_ARGS="$KUBE_API_ARGS --kubelet-certificate-authority=${CERT_DIR}/ca.crt --kubelet-client-certificate=${CERT_DIR}/server.crt --kubelet-client-key=${CERT_DIR}/server.key --kubelet-https=true"
    # Allow for metrics-server/aggregator communication
    KUBE_API_ARGS="${KUBE_API_ARGS} \
        --proxy-client-cert-file=${CERT_DIR}/server.crt \
        --proxy-client-key-file=${CERT_DIR}/server.key \
        --requestheader-allowed-names=front-proxy-client,kube,kubernetes \
        --requestheader-client-ca-file=${CERT_DIR}/ca.crt \
        --requestheader-extra-headers-prefix=X-Remote-Extra- \
        --requestheader-group-headers=X-Remote-Group \
        --requestheader-username-headers=X-Remote-User"
fi

KUBE_ADMISSION_CONTROL=""
if [ -n "${ADMISSION_CONTROL_LIST}" ] && [ "${TLS_DISABLED}" == "False" ]; then
    KUBE_ADMISSION_CONTROL="--admission-control=NodeRestriction,${ADMISSION_CONTROL_LIST}"
fi

if [ -n "$TRUST_ID" ] && [ "$(echo "${CLOUD_PROVIDER_ENABLED}" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    KUBE_API_ARGS="$KUBE_API_ARGS --cloud-provider=external"
fi

if [ "$KEYSTONE_AUTH_ENABLED" == "True" ]; then
    KEYSTONE_WEBHOOK_CONFIG=/etc/kubernetes/keystone_webhook_config.yaml

    [ -f ${KEYSTONE_WEBHOOK_CONFIG} ] || {
echo "Writing File: $KEYSTONE_WEBHOOK_CONFIG"
mkdir -p $(dirname ${KEYSTONE_WEBHOOK_CONFIG})
cat << EOF > ${KEYSTONE_WEBHOOK_CONFIG}
---
apiVersion: v1
kind: Config
preferences: {}
clusters:
  - cluster:
      insecure-skip-tls-verify: true
      server: https://127.0.0.1:8443/webhook
    name: webhook
users:
  - name: webhook
contexts:
  - context:
      cluster: webhook
      user: webhook
    name: webhook
current-context: webhook
EOF
}
    KUBE_API_ARGS="$KUBE_API_ARGS --authentication-token-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml --authorization-webhook-config-file=/etc/kubernetes/keystone_webhook_config.yaml"
    webhook_auth="--authorization-mode=Node,Webhook,RBAC"
    KUBE_API_ARGS=${KUBE_API_ARGS/--authorization-mode=Node,RBAC/$webhook_auth}
fi

sed -i '
    /^KUBE_API_ADDRESS=/ s/=.*/="'"${KUBE_API_ADDRESS}"'"/
    /^KUBE_SERVICE_ADDRESSES=/ s|=.*|="--service-cluster-ip-range='"$PORTAL_NETWORK_CIDR"'"|
    /^KUBE_API_ARGS=/ s|=.*|="'"${KUBE_API_ARGS}"'"|
    /^KUBE_ETCD_SERVERS=/ s/=.*/="--etcd-servers=http:\/\/127.0.0.1:2379"/
    /^KUBE_ADMISSION_CONTROL=/ s/=.*/="'"${KUBE_ADMISSION_CONTROL}"'"/
' /etc/kubernetes/apiserver


# Add controller manager args
KUBE_CONTROLLER_MANAGER_ARGS="--leader-elect=true"
KUBE_CONTROLLER_MANAGER_ARGS="$KUBE_CONTROLLER_MANAGER_ARGS --cluster-name=${CLUSTER_UUID}"
KUBE_CONTROLLER_MANAGER_ARGS="${KUBE_CONTROLLER_MANAGER_ARGS} --allocate-node-cidrs=true"
KUBE_CONTROLLER_MANAGER_ARGS="${KUBE_CONTROLLER_MANAGER_ARGS} --cluster-cidr=${PODS_NETWORK_CIDR}"
KUBE_CONTROLLER_MANAGER_ARGS="$KUBE_CONTROLLER_MANAGER_ARGS $KUBECONTROLLER_OPTIONS"
if [ -n "${ADMISSION_CONTROL_LIST}" ] && [ "${TLS_DISABLED}" == "False" ]; then
    KUBE_CONTROLLER_MANAGER_ARGS="$KUBE_CONTROLLER_MANAGER_ARGS --service-account-private-key-file=$CERT_DIR/service_account_private.key --root-ca-file=$CERT_DIR/ca.crt"
fi

if [ -n "$TRUST_ID" ] && [ "$(echo "${CLOUD_PROVIDER_ENABLED}" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    KUBE_CONTROLLER_MANAGER_ARGS="$KUBE_CONTROLLER_MANAGER_ARGS --cloud-provider=external"
    KUBE_CONTROLLER_MANAGER_ARGS="$KUBE_CONTROLLER_MANAGER_ARGS --external-cloud-volume-plugin=openstack --cloud-config=/etc/kubernetes/cloud-config"
fi


if [ "$(echo $CERT_MANAGER_API | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    KUBE_CONTROLLER_MANAGER_ARGS="$KUBE_CONTROLLER_MANAGER_ARGS --cluster-signing-cert-file=$CERT_DIR/ca.crt --cluster-signing-key-file=$CERT_DIR/ca.key"
fi

sed -i '
    /^KUBELET_ADDRESSES=/ s/=.*/="--machines='""'"/
    /^KUBE_CONTROLLER_MANAGER_ARGS=/ s#\(KUBE_CONTROLLER_MANAGER_ARGS\).*#\1="'"${KUBE_CONTROLLER_MANAGER_ARGS}"'"#
' /etc/kubernetes/controller-manager

sed -i '/^KUBE_SCHEDULER_ARGS=/ s/=.*/="--leader-elect=true"/' /etc/kubernetes/scheduler

