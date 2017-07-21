#!/bin/bash
set -ux

atomic install \
--system-package no \
--system \
--name heat-container-agent \
gitlab-registry.cern.ch/strigazi/heat-container-agent:system-container-rawhide

systemctl start --no-block heat-container-agent
