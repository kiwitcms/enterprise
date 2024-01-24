#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

rlJournalStart
    rlPhaseStartTest "Check if upstream nginx.conf has changed"
        UPSTREAM_NGINX_CONF="upstream-nginx.conf"
        rlRun -t -c "curl -o $UPSTREAM_NGINX_CONF https://raw.githubusercontent.com/kiwitcms/Kiwi/master/etc/nginx.conf"

        VENDORED_NGINX_CONF="etc/nginx.vendored"
        rlRun -t -c "diff -Naur $VENDORED_NGINX_CONF $UPSTREAM_NGINX_CONF"
        if [ $? == 0 ]; then
            rlLogInfo "All good. No need to do anything downstream!"
        else
            rlLogFatal "Downstream changes required!"
            rlLogFatal "Carry over the relevant diff into etc/nginx.openresty and update $VENDORED_NGINX_CONF"
        fi
    rlPhaseEnd

rlJournalEnd

rlJournalPrintText
