#!/bin/sh

. /etc/sysconfig/heat-params

if [ "$CVMFS_ENABLED" = "False" ]; then
    exit 0
fi

chattr -i /
mkdir /cvmfs
chattr +i /

atomic install gitlab-registry.cern.ch/cloud-infrastructure/docker-volume-cvmfs:${CVMFS_TAG}

# add selinux policy
docker cp docker-volume-cvmfs:/dockercvmfs.pp /tmp
semodule -i /tmp/dockercvmfs.pp

# install kubernetes volume plugin
mkdir -p /var/lib/kubelet/plugins/volume/exec/cern~cvmfs
docker cp docker-volume-cvmfs:/usr/sbin/docker-volume-cvmfs /var/lib/kubelet/plugins/volume/exec/cern~cvmfs/cvmfs

# TODO: drop this requirement (kubelet seems to need the binary there on start)
systemctl restart kubelet
