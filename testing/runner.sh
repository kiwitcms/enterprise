#!/bin/bash

# Note: execute this file from the project root directory

# setup
rm -rf /var/tmp/beakerlib-*/
export BEAKERLIB_JOURNAL=0

# start and configure Keycloak server
echo "**** STARTING KEYCLOAK ****"
./testing/start_keycloak.sh
echo "**** DEBUG, /tmp/kc.env ****"
cat /tmp/kc.env
echo "**** END DEBUG ****"
echo "**** DONE STARTING KEYCLOAK ****"

# execute test scripts
./testing/test_upstream_nginx_config.sh
./testing/test_docker.sh


# look for failures
cat /var/tmp/beakerlib-*/TestResults || exit 11
grep RESULT_STRING /var/tmp/beakerlib-*/TestResults | grep -v PASS && exit 22

# explicit return code for Makefile
exit 0
