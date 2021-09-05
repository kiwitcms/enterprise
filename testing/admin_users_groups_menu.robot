*** Settings ***
Library           SeleniumLibrary

*** Variables ***
# "empty" tenant is created during initial_setup
${SERVER}               https://empty.testing.example.bg:8443
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/accounts/login/
${DASHBOARD_URL}        ${SERVER}/
${USER_GROUP_URL}       ${SERVER}/accounts/users-and-groups/
${ADMIN_URL}            ${SERVER}/admin/auth/
${USERS_URL}            ${SERVER}/admin/tcms_tenants/tenant_authorized_users/


*** Test Cases ***
When Superuser Clicks Menu Is Redirected To Admin
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    super-root
    Input Text    inputPassword    secret
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${USER_GROUP_URL}
    Location Should Be    ${ADMIN_URL}
    Title Should Be       Authentication and Authorization administration | Grappelli

    [Teardown]    Close Browser


When Regular User Clicks Menu Is Redirected To Authorized Users
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    # reuse LDAP login b/c that's a regular user account
    Input Text    inputUsername    ldap_atodorov
    Input Text    inputPassword    h3llo-w0rld
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${USER_GROUP_URL}
    Location Should Be    ${USERS_URL}
    Title Should Be       Select tenant-user relationship to change | Grappelli

    [Teardown]    Close Browser
