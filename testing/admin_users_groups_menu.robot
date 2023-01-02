*** Settings ***
Library           SeleniumLibrary

*** Variables ***
# "empty" tenant is created during initial_setup
${SERVER}               https://empty.testing.example.bg:8443
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/accounts/login/
${DASHBOARD_URL}        ${SERVER}/
${USER_NAV_URL}         ${SERVER}/accounts/admin-users/
${ADMIN_URL}            ${SERVER}/admin/auth/user/
${USERS_URL}            ${SERVER}/admin/tcms_tenants/tenant_authorized_users/


*** Test Cases ***
When Superuser Clicks User Menu Is Redirected To Admin Panel
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    super-root
    Input Text    inputPassword    secret-2a9a34cd-e51d-4039-b709-b45f629a5595
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${USER_NAV_URL}
    Location Should Be    ${ADMIN_URL}
    Title Should Be       Select user to change | Grappelli

    [Teardown]    Close Browser


When Regular User Clicks User Menu Is Redirected To Authorized Users
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

    Go To                 ${USER_NAV_URL}
    Location Should Be    ${USERS_URL}
    Title Should Be       Select tenant-user relationship to change | Grappelli

    [Teardown]    Close Browser
