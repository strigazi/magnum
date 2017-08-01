#!/bin/sh

. /etc/sysconfig/heat-params

KUBE_OS_CLOUD_CONFIG=/etc/kubernetes/kube_openstack_config

# Generate a the configuration for Kubernetes services
# to talk to OpenStack Neutron
cat > $KUBE_OS_CLOUD_CONFIG <<EOF
[Global]
auth-url=$AUTH_URL
user-id=$TRUSTEE_USER_ID
password=$TRUSTEE_PASSWORD
trust-id=$TRUST_ID
[LoadBalancer]
subnet-id=$CLUSTER_SUBNET
create-monitor=yes
monitor-delay=1m
monitor-timeout=30s
monitor-max-retries=3
EOF


KUBE_NUMERIC_VERSION=${KUBE_VERSION:1}
IFS=. read KUBE_MAJOR KUBE_MINOR KUBE_PATCH <<EOF
${KUBE_NUMERIC_VERSION##*-}
EOF

if [ "$KUBE_MAJOR" -eq "1" -a "$KUBE_MINOR" -ge "7" ] || [ "$KUBE_MAJOR" -ge "2" ]; then
    cat >> $KUBE_OS_CLOUD_CONFIG <<EOF
[BlockStorage]
bs-version=v2
EOF
fi