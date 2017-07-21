#!/bin/bash

. /etc/sysconfig/heat-params

set -ux

_prefix=${CONTAINER_INFRA_PREFIX:-docker.io/openstackmagnum/}
atomic install \
--storage ostree \
--system \
--system-package no \
--name heat-container-agent \
${_prefix}heat-container-agent:rawhide

systemctl start heat-container-agent
