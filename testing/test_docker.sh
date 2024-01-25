#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

HTTPS="https://testing.example.bg:8443"

WRK_DIR=$(mktemp -d ./wrk-logs-XXXX)
chmod go+rwx "$WRK_DIR"

assert_up_and_running() {
    sleep 10
    # HTTP redirects; HTTPS displays the login page
    rlRun -t -c "curl       -o- http://testing.example.bg:8080/  | grep '301 Moved Permanently'"
    rlRun -t -c "curl -k -L -o- $HTTPS/ | grep 'Welcome to Kiwi TCMS'"
}

get_dashboard() {
    rlRun -t -c "curl -k -L -o- -c /tmp/testcookies.txt $1/"
    CSRF_TOKEN=$(grep csrftoken /tmp/testcookies.txt | cut -f 7)
    rlRun -t -c "curl -e $1/accounts/login/ -d username=ldap_atodorov -d password=h3llo-w0rld \
        -d csrfmiddlewaretoken=$CSRF_TOKEN -k -L -i -o /tmp/testdata.txt \
        -b /tmp/testcookies.txt -c /tmp/login-cookies.txt $1/accounts/login/"
    rlAssertGrep "<title>Kiwi TCMS - Dashboard</title>" /tmp/testdata.txt
}


exec_wrk() {
    URL=$1
    LOGS_DIR=$2
    LOG_BASENAME=$3
    EXTRA_HEADERS=${4:-"X-Dummy-Header: 1"}

    WRK_FILE="$LOGS_DIR/$LOG_BASENAME.log"

    wrk -d10s -t4 -c4 --script ./testing/print-non-limited-requests.lua -H "$EXTRA_HEADERS" "$URL" > "$WRK_FILE"

    COMPLETED_REQUESTS=$(grep 'non-429 request status=' "$WRK_FILE" | wc -l)

    # this is the number of all completed requests across 10 seconds
    echo "$COMPLETED_REQUESTS"
}


rlJournalStart
    rlPhaseStartTest "Sanity test - boot the docker image"
        rlRun -t -c "docker-compose -f docker-compose.testing up -d"
        sleep 5

        IP_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web)
        rlLogInfo "--- testing.example.bg: $IP_ADDRESS --"
        rlRun -t -c "sudo sh -c \"echo '$IP_ADDRESS    testing.example.bg     empty.testing.example.bg' >> /etc/hosts\""

        KC_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' keycloak_server)
        rlLogInfo "--- kc.example.bg: $KC_ADDRESS --"

        # Kiwi TCMS container needs to know how to resolve the Keycloak server address
        rlRun -t -c "docker exec -u 0 -i web /bin/bash -c \"echo '$KC_ADDRESS    kc.example.bg' >> /etc/hosts\""
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - initial configuration"
        # need to monkey-patch createsuperuser.py b/c it rejects input when not using a TTY
        rlRun -t -c 'docker exec -i web sed -i "s/raise NotRunningInTTYException/pass/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py'
        rlRun -t -c 'docker exec -i web sed -i "s/getpass.getpass/input/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py'
        rlRun -t -c 'echo -e "super-root\nroot@example.com\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\ntesting.example.bg\n" | docker exec -i web /Kiwi/manage.py initial_setup'

        # assert only after initial configuration has been applied
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - missing migrations"
        rlRun -t -c "docker exec -i web /Kiwi/manage.py makemigrations --check"
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - download login page"
        rlRun -t -c "curl -k -L -o page.html https://testing.example.bg:8443/"
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
            rlRun -t -c "curl -k -f -o /dev/null https://testing.example.bg:8443/$URL"
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
        rlRun -t -c "docker-compose -f docker-compose.testing restart"

        STATE=$(docker inspect web | jq -r ".[].State.Health.Status")
        rlAssertEquals "container state is healthy" "$STATE" "starting"

        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Sanity test - ADMIN -> Users and Groups menu"
        # WARNING: reuses username/password from the LDAP test above !!!
        rlRun -t -c "cat testing/configure_tenant_users.py | docker exec -i web /Kiwi/manage.py shell"
        rlRun -t -c "robot testing/admin_users_groups_menu.robot"
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
        rlRun -t -c "curl -k -D- $HTTPS 2>/dev/null | grep $'Content-Security-Policy: script-src \'self\' cdn.crowdin.com;'"
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
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS"
        rlAssertGreaterOrEqual ">= 10 r/s" "$COMPLETED_REQUESTS" 100
        rlAssertLesserOrEqual  "<= 20 r/s" "$COMPLETED_REQUESTS" 200
    rlPhaseEnd

    rlPhaseStartTest "Requests to /accounts/login/ are rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/accounts/login/" "$WRK_DIR" "login-page")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS"
        rlAssertGreaterOrEqual ">= 10 r/s" "$COMPLETED_REQUESTS" 100
        rlAssertLesserOrEqual  "<= 20 r/s" "$COMPLETED_REQUESTS" 200
    rlPhaseEnd

    rlPhaseStartTest "Requests to /accounts/passwordreset/ are rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/accounts/passwordreset/" "$WRK_DIR" "password-reset-page")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS"
        rlAssertGreaterOrEqual ">= 10 r/s" "$COMPLETED_REQUESTS" 100
        rlAssertLesserOrEqual  "<= 20 r/s" "$COMPLETED_REQUESTS" 200
    rlPhaseEnd

    rlPhaseStartTest "Requests for static files are NOT rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/static/images/kiwi_h20.png" "$WRK_DIR" "static-image")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS"
        rlAssertGreaterOrEqual ">= 1000 r/s" "$COMPLETED_REQUESTS" 10000
    rlPhaseEnd

    rlPhaseStartTest "Requests for /favicon.ico are NOT rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/favicon.ico" "$WRK_DIR" "favicon")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS in 10 seconds"
        rlAssertGreaterOrEqual ">= 1000 r/s" "$COMPLETED_REQUESTS" 10000
    rlPhaseEnd

    rlPhaseStartTest "Requests for robots.txt are NOT rate limited"
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/robots.txt" "$WRK_DIR" "robots-txt")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS"
        rlAssertGreaterOrEqual ">= 1000 r/s" "$COMPLETED_REQUESTS" 10000
    rlPhaseEnd

    rlPhaseStartTest "Authenticated requests to / are NOT rate limited"
        # login and create the cookies file
        get_dashboard "$HTTPS"

        SESSION_ID=$(grep sessionid /tmp/login-cookies.txt | cut -f 7)
        COMPLETED_REQUESTS=$(exec_wrk "$HTTPS/" "$WRK_DIR" "dashboard" "Cookie: sessionid=$SESSION_ID")
        rlLogInfo "COMPLETED_REQUESTS=$COMPLETED_REQUESTS"
        rlAssertGreaterOrEqual ">= 50 r/s" "$COMPLETED_REQUESTS" 500
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker kill keycloak_server"
        rlRun -t -c "docker-compose -f docker-compose.testing logs --no-color > docker.log"
        rlRun -t -c "docker-compose -f docker-compose.testing down"
        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm enterprise_db_data"
        fi
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
