#!/bin/sh

. /etc/sysconfig/heat-params

$configure_docker_storage_driver

if [ "$DOCKER_STORAGE_DRIVER" = "overlay" ]; then
    if [ $(echo -e "$(uname -r)\n3.18" | sort -V | head -1) \
         = $(uname -r) ]; then
        ERROR_MESSAGE="OverlayFS requires at least Linux kernel 3.18. Cluster node kernel version: $(uname -r)"
        echo "ERROR: ${ERROR_MESSAGE}" >&2
        sh -c "${WAIT_CURL} --data-binary '{\"status\": \"FAILURE\", \"reason\": \"${ERROR_MESSAGE}\"}'"
    else
        configure_overlay
    fi
else
    configure_devicemapper
fi
