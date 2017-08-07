#!/bin/sh

kubetagfile=/srv/magnum/kubetagfile.sh
[ -f ${kubetagfile} ] || {
    echo "Writing File: $kubetagfile"
    mkdir -p $(dirname ${kubetagfile})
    cat << EOF > ${kubetagfile}
kube_tag_input
$kube_tag_input
EOF
}
