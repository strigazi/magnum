#!/bin/bash -x

uprgade_bin_file=/srv/magnum/bin/upgrade
[ -f ${uprgade_bin_file} ] || {
    echo "Writing File: $uprgade_bin_file"
    mkdir -p $(dirname ${uprgade_bin_file})
    cat << EOF > ${uprgade_bin_file}
#!/bin/bash -x

systemctl stop kubelet
systemctl stop kube-proxy

atomic uninstall kubelet
atomic uninstall kube-proxy

atomic pull --storage ostree docker.io/openstackmagnum/kubernetes-kubelet:${kube_tag_input}
atomic pull --storage ostree docker.io/openstackmagnum/kubernetes-proxy:${kube_tag_input}

atomic install --storage ostree --system --system-package=no --name=kubelet docker.io/openstackmagnum/kubernetes-kubelet:${kube_tag_input}
atomic install --storage ostree --system --system-package=no --name=kube-proxy docker.io/openstackmagnum/kubernetes-proxy:${kube_tag_input}

systemctl start kubelet
systemctl start kube-proxy
EOF
    chown root:root ${uprgade_bin_file}
    chmod 0755 ${uprgade_bin_file}
}

KUBE_UPGRADE_SERVICE=/etc/systemd/system/kube-upgrade.service
[ -f ${KUBE_UPGRADE_SERVICE} ] || {
    echo "Writing File: $KUBE_UPGRADE_SERVICE"
    mkdir -p $(dirname ${KUBE_UPGRADE_SERVICE})
    cat << EOF > ${KUBE_UPGRADE_SERVICE}
[Unit]
Description=Kubernetes Worker Uprgade service

[Service]
Type=oneshot
Environment=HOME=/root
ExecStart=${uprgade_bin_file}

[Install]
WantedBy=multi-user.target
EOF
}


chown root:root ${KUBE_UPGRADE_SERVICE}
chmod 0644 ${KUBE_UPGRADE_SERVICE}

systemctl enable kube-upgrade.service
systemctl start kube-upgrade.service
