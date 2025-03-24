#!/bin/bash

# Copyright (c) 2024-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

. /usr/share/beakerlib/beakerlib.sh

HTTPS="https://testing.example.bg:8443"

WRK_DIR=$(mktemp -d ./wrk-logs-XXXX)
chmod go+rwx "$WRK_DIR"

assert_up_and_running() {
    sleep 10
    # HTTP redirects; HTTPS displays the login page
    rlRun -t -c "curl       -o- --referer assert_up_and_running http://testing.example.bg:8080/  | grep '301 Moved Permanently'"
    rlRun -t -c "curl -k -L -o- --referer assert_up_and_running $HTTPS/ | grep 'Welcome to Kiwi TCMS'"
}

get_dashboard() {
    rlRun -t -c "curl -k -L -o- --referer get_dashboard -c ./testcookies.txt $1/"
    CSRF_TOKEN=$(grep csrftoken ./testcookies.txt | cut -f 7)
    rlRun -t -c "curl --referer $1/accounts/login/ -d username=ldap_atodorov -d password=h3llo-w0rld \
        -d csrfmiddlewaretoken=$CSRF_TOKEN -k -L -i -o ./testdata.txt \
        -b ./testcookies.txt -c ./login-cookies.txt $1/accounts/login/"
    rlAssertGrep "<title>Kiwi TCMS - Dashboard</title>" ./testdata.txt
}


exec_wrk() {
    URL=$1
    LOGS_DIR=$2
    LOG_BASENAME=$3
    EXTRA_HEADERS=${4:-"Referer: wrk-for-$LOG_BASENAME"}

    WRK_FILE="$LOGS_DIR/$LOG_BASENAME.log"

    wrk -d10s -t4 -c4 --script ./testing/print-non-limited-requests.lua -H "$EXTRA_HEADERS" "$URL" > "$WRK_FILE"

    COMPLETED_REQUESTS=$(grep 'non-429 request status=' "$WRK_FILE" | wc -l)

    # this is the number of all completed requests across 10 seconds
    echo "$COMPLETED_REQUESTS"
}


rlJournalStart
    rlPhaseStartTest "Sanity test - boot the docker image"
        rlRun -t -c "docker compose -f docker-compose.testing up -d"
        sleep 5

        IP_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web)
        rlLogInfo "--- testing.example.bg: $IP_ADDRESS --"
        rlRun -t -c "sudo sh -c \"echo '$IP_ADDRESS    testing.example.bg     empty.testing.example.bg' >> /etc/hosts\""

        KC_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' keycloak_server)
        rlLogInfo "--- kc.example.bg: $KC_ADDRESS --"

        # Kiwi TCMS container needs to know how to resolve the Keycloak server address
        rlRun -t -c "docker exec -u 0 -i web /bin/bash -c \"echo '$KC_ADDRESS    kc.example.bg' >> /etc/hosts\""
    rlPhaseEnd

    rlPhaseStartTest "Extract and list files in /Kiwi/static/"
        rlRun -t -c "make extract-static-files"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - initial configuration"
        # need to monkey-patch createsuperuser.py b/c it rejects input when not using a TTY
        rlRun -t -c 'docker exec -i web sed -i "s/raise NotRunningInTTYException/pass/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py'
        rlRun -t -c 'docker exec -i web sed -i "s/getpass.getpass/input/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py'
        rlRun -t -c 'echo -e "super-root\nroot@example.com\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\n" | docker exec -i web /Kiwi/manage.py initial_setup'

        # assert only after initial configuration has been applied
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - missing migrations"
        rlRun -t -c "docker exec -i web /Kiwi/manage.py makemigrations --check"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - download CA.crt for self-signed SSL"
        rlRun -t -c "curl -k --fail -o- $HTTPS/static/ca.crt"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - download login page"
        rlRun -t -c "curl -k -L -o page.html $HTTPS/"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - check page.html"
        # version is Enterprise
        rlAssertGrep "Version.*-Enterprise" page.html

        # plugins are listed
        rlAssertGrep 'href="/admin/trackers_integration/apitoken/' page.html
        rlAssertGrep 'href="/kiwitcms_tenants/' page.html
        rlAssertGrep 'href="/kiwitcms_github_app/' page.html

        # template override for social icons
        rlAssertGrep "or Continue With" page.html

        # social backends are listed
        # for ICON in tcms_enterprise/static/images/social_auth/backends/*.png; do
        #    BACKEND=`basename $ICON | sed 's/.png//'`
        # check only the backends enabled in test_settings.py b/c the directory above
        # contains more images than backends which can be enabled during testing
        for BACKEND in kerberos keycloak gitlab github github-app fedora; do
            rlAssertGrep "/login/$BACKEND/" page.html
            rlAssertGrep "<img src='/static/images/social_auth/backends/$BACKEND.*.png'" page.html
        done

        # social icons are present
        for URL in `cat page.html | grep "/static/images/social_auth/backends/" | cut -d= -f2 | cut -d"'" -f2`; do
            rlLogInfo "Verify image $URL is present"
            rlRun -t -c "curl -k -f -o /dev/null $HTTPS/$URL"
        done

        # social icons point to correct backend login URL, even with port
        for BACKEND in `cat page.html | grep "/static/images/social_auth/backends/" | cut -d= -f2 | cut -d"'" -f2 | cut -f6 -d/ | cut -f1 -d.`; do
            rlLogInfo "Verify $BACKEND login is present"
            rlAssertGrep "https://testing.example.bg/login/$BACKEND/?next=/" page.html
        done
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - LDAP login and sync"
        LDAP_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' openldap_server)

        # import users from the local config file and query the LDAP server
        rlRun -t -c "ldapadd -x -H ldap://$LDAP_ADDRESS:389 -D cn=Manager,dc=example,dc=com -w admin -f testing/ldap.ldif"
        rlRun -t -c "ldapsearch -x -LLL -H ldap://$LDAP_ADDRESS:389 -b dc=example,dc=com objectClass=person"

        rlRun -t -c "robot testing/ldap.robot"

        rlRun -t -c "docker exec -i web /Kiwi/manage.py ldap_sync_users"
        rlRun -t -c "cat testing/ldap.py | docker exec -i web /Kiwi/manage.py shell"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - container is healthy"
        STATE=$(docker inspect web | jq -r ".[].State.Health.Status")
        rlAssertEquals "container state is healthy" "$STATE" "healthy"
    rlPhaseEnd

    rlPhaseStartTest "Container restart"
        rlRun -t -c "docker compose -f docker-compose.testing restart"

        STATE=$(docker inspect web | jq -r ".[].State.Health.Status")
        rlAssertEquals "container state is healthy" "$STATE" "starting"

        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - ADMIN -> Users and Groups menu"
        # WARNING: reuses username/password from the LDAP test above !!!
        rlRun -t -c "cat testing/configure_tenant_users.py | docker exec -i web /Kiwi/manage.py shell"
        rlRun -t -c "robot testing/admin_users_groups_menu.robot"
    rlPhaseEnd

    rlPhaseStartTest "Can upload attachments via browser UI"
        # WARNING: reuses username/password from the LDAP test above !!!

        ARCH=$(uname -m)
        if [ "$ARCH" == "x86_64" ]; then
            # can upload file
            rlRun -t -c "robot testing/test_upload_file.robot"

            # verify file is there
            rlRun -t -c "curl -k -D- --silent $HTTPS/uploads/tenant/public/attachments/testplans_testplan/1/hello-robots.txt | grep '200 OK'"
        fi
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - Keycloak login"
        rlRun -t -c "robot testing/keycloak.robot"
    rlPhaseEnd

    rlPhaseStartTest "Should send ETag header"
        rlRun -t -c "curl -k -D- $HTTPS/static/images/kiwi_h20.png 2>/dev/null | grep 'ETag'"
    rlPhaseEnd

    rlPhaseStartTest "Should NOT send Cache-Control header"
        rlRun -t -c "curl -k -D- $HTTPS/static/images/kiwi_h20.png 2>/dev/null | grep 'Cache-Control'" 1
    rlPhaseEnd

    rlPhaseStartTest "Should send X-Frame-Options header"
        rlRun -t -c "curl -k -D- $HTTPS 2>/dev/null | grep 'X-Frame-Options: DENY'"
    rlPhaseEnd

    rlPhaseStartTest "Should send X-Content-Type-Options header"
        rlRun -t -c "curl -k -D- $HTTPS 2>/dev/null | grep 'X-Content-Type-Options: nosniff'"
    rlPhaseEnd

    rlPhaseStartTest "Should send Content-Security-Policy header"
        rlRun -t -c "curl -k -D- --referer test_scenario_csp $HTTPS 2>&1"
        rlRun -t -c "curl -k -D- --referer test_scenario_csp $HTTPS 2>/dev/null | grep $'Content-Security-Policy: script-src \'self\' cdn.crowdin.com \*.ethicalads.io plausible.io cdn.example.bg;'"
    rlPhaseEnd

    rlPhaseStartTest "Should send uploads with exactly 1 'Content-Type: text/plain' header"
        # copy test file externally b/c Kiwi TCMS v12.2 will prevent its upload
        rlRun -t -c "docker exec -i web /bin/bash -c 'mkdir -p /Kiwi/uploads/attachments/auth_user/2/'"
        rlRun -t -c "docker cp testing/ldap.py web:/Kiwi/uploads/attachments/auth_user/2/"
        rlRun -t -c "curl -k -D- $HTTPS/uploads/attachments/auth_user/2/ldap.py 2>/dev/null | grep 'Content-Type: text/plain'"

        CT_HEADER_COUNT=$(curl -k -D- $HTTPS/uploads/attachments/auth_user/2/ldap.py 2>/dev/null | grep -c 'Content-Type:')
        rlAssertEquals "There should be only 1 Content-Type header" "$CT_HEADER_COUNT" 1
    rlPhaseEnd

    rlPhaseStartTest "Requests to /accounts/register/ are rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/accounts/register/" "$WRK_DIR" "register-account-page")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 10 r/s" "$COMPLETED_REQUESTS" 100
        rlAssertLesserOrEqual  "<= 20 r/s" "$COMPLETED_REQUESTS" 200
    rlPhaseEnd

    rlPhaseStartTest "Requests to /accounts/login/ are rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/accounts/login/" "$WRK_DIR" "login-page")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 10 r/s" "$COMPLETED_REQUESTS" 100
        rlAssertLesserOrEqual  "<= 20 r/s" "$COMPLETED_REQUESTS" 200
    rlPhaseEnd

    rlPhaseStartTest "Requests to /accounts/passwordreset/ are rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/accounts/passwordreset/" "$WRK_DIR" "password-reset-page")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 10 r/s" "$COMPLETED_REQUESTS" 100
        rlAssertLesserOrEqual  "<= 20 r/s" "$COMPLETED_REQUESTS" 200
    rlPhaseEnd

    rlPhaseStartTest "Requests to missing pages (404) are rate limited"
        sleep 90 # chill
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/not/available.html" "$WRK_DIR" "404")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 1 r/m" "$COMPLETED_REQUESTS" 1
        # Note: running wrk with 4 connections in parallel
        rlAssertLesserOrEqual  "<= 2 r/m" "$COMPLETED_REQUESTS" 4
    rlPhaseEnd

    rlPhaseStartTest "Requests to random pages (404) are rate limited"
        sleep 90 # chill
        WRK_FILE="$WRK_DIR/random-404.log"
        START_TIME=$(date +%s)
        for i in `seq 1000`; do
            curl --silent -k -D- $HTTPS/random-file-$i.html >> $WRK_FILE
        done
        END_TIME=$(date +%s)

        COMPLETED_REQUESTS=$(grep "HTTP/1.1 404" "$WRK_FILE" | wc -l)
        ELAPSED_TIME=$(($END_TIME - $START_TIME))

        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in $ELAPSED_TIME seconds"
        rlAssertGreaterOrEqual ">= 1 r/m" "$COMPLETED_REQUESTS" 1
        rlAssertLesserOrEqual  "<= 2 r/m" "$COMPLETED_REQUESTS" $(($(($ELAPSED_TIME / 60)) + 2))
    rlPhaseEnd

    rlPhaseStartTest "Requests for static files are rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/static/images/kiwi_h20.png" "$WRK_DIR" "static-image")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 300 r/s" "$COMPLETED_REQUESTS" 3000
        rlAssertLesserOrEqual  "<= 400 r/s" "$COMPLETED_REQUESTS" 4000
    rlPhaseEnd

    rlPhaseStartTest "Requests for uploaded files are rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/uploads/attachments/auth_user/2/ldap.py" "$WRK_DIR" "uploaded-file")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"

        # WARNING: the defaults are overriden in docker-compose.testing
        rlAssertGreaterOrEqual ">= 55 r/s" "$COMPLETED_REQUESTS" 550
        rlAssertLesserOrEqual  "<= 75 r/s" "$COMPLETED_REQUESTS" 750
    rlPhaseEnd

    rlPhaseStartTest "Requests for /favicon.ico are NOT rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/favicon.ico" "$WRK_DIR" "favicon")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 1000 r/s" "$COMPLETED_REQUESTS" 10000
    rlPhaseEnd

    rlPhaseStartTest "Requests for robots.txt are NOT rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/robots.txt" "$WRK_DIR" "robots-txt")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 1000 r/s" "$COMPLETED_REQUESTS" 10000
    rlPhaseEnd

    rlPhaseStartTest "Authenticated requests under / are rate limited"
        # login and create the cookies file
        get_dashboard "$HTTPS"

        SESSION_ID=$(grep sessionid ./login-cookies.txt | cut -f 7)
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/" "$WRK_DIR" "dashboard" "Cookie: sessionid=$SESSION_ID")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 35 r/s" "$COMPLETED_REQUESTS" 350
    rlPhaseEnd

    rlPhaseStartTest "Should render Mermaid.JS diagrams"
        rlRun -t -c "curl -L -k -b ./login-cookies.txt -o plan.html $HTTPS/plan/1/ 2>/dev/null"
        rlAssertGrep "https://mermaid.ink/img/" plan.html
        rlAssertNotGrep "flowchart LR" plan.html
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker kill keycloak_server"
        rlRun -t -c "docker compose -f docker-compose.testing logs --no-color > docker.log"
        rlRun -t -c "docker compose -f docker-compose.testing down"
        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm enterprise_db_data"
        fi
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
