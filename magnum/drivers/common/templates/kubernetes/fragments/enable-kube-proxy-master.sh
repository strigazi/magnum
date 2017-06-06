#!/bin/sh

. /etc/sysconfig/heat-params

HYPERKUBE_IMAGE="{$SYSTEM_CONTAINER_IMAGE_PREFIX:gcr.io/google_containers""/hyperkube:${KUBE_VERSION}"

init_templates () {
    local TEMPLATE=/etc/kubernetes/manifests/kube-proxy.yaml
    [ -f ${TEMPLATE} ] || {
        echo "TEMPLATE: $TEMPLATE"
        mkdir -p $(dirname ${TEMPLATE})
        cat << EOF > ${TEMPLATE}
apiVersion: v1
kind: Pod
metadata:
  name: kube-proxy
  namespace: kube-system
spec:
  hostNetwork: true
  containers:
  - name: kube-proxy
    image: ${HYPERKUBE_IMAGE}
    command:
    - /hyperkube
    - proxy
    - --master=http://127.0.0.1:8080
    - --logtostderr=true
    - --v=0
    securityContext:
      privileged: true
EOF
    }
}

init_templates
