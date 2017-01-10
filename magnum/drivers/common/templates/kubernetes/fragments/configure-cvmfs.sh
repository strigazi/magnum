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
mkdir -p /var/lib/kubelet/plugins/volume/cern~cvmfs
docker cp docker-volume-cvmfs:/usr/sbin/docker-volume-cvmfs /var/lib/kubelet/plugins/volume/cern~cvmfs/cvmfs

# TODO: move this elsewhere
lvextend /dev/atomicos/root --size 5G
xfs_growfs /dev/mapper/atomicos-root
