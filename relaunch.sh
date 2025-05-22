#!/bin/bash
# Copyright ETSI
# See LICENSE files
#
# Stops or restarts the Docker image containing the web-app for doc2oas
#

CNT=$(docker ps | grep doc2oas | cut -d " " -f1)

if [ "$CNT" != "" ] ; then
    docker stop "$CNT"
fi

if [ "$2" == "stop" ] ; then
    exit 0
fi 

sed -i -E "s/(LAST_COMMIT=).+/\1$(git rev-parse HEAD)/" env

docker build --tag forge.etsi.org:5050/cti/doc2oas:$1 -f Dockerfile .

docker run -d --restart unless-stopped -t -p 5001:5001 --env-file ./env forge.etsi.org:5050/cti/doc2oas:$1

