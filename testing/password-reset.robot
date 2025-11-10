# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

*** Settings ***
Library           Process
Library           String
Library           SeleniumLibrary

*** Variables ***
# "empty" tenant is created during initial_setup
${SERVER}               https://testing.example.bg:8443
${BROWSER}              Headless Firefox
${DELAY}                0
${DASHBOARD_URL}        ${SERVER}/
${LOGIN_URL}            ${SERVER}/accounts/login/
${PWD_RESET_URL}        ${SERVER}/accounts/passwordreset/
${PWD_RESET_DONE}       ${SERVER}/accounts/passwordreset/done/
${PWD_RESET_COMPLETE}   ${SERVER}/accounts/passwordreset/complete/


*** Test Cases ***
Regular User Can Reset Their Password
    Open Browser    ${PWD_RESET_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Password reset

    # reset for super-user b/c that's a regular account
    Input Text    inputEmail    root@example.com
    Click Button  Password reset

    Location Should Be    ${PWD_RESET_DONE}
    Page Should Contain   Password reset email was sent!
    Sleep       10s     Waiting for email to be sent

    ${ls}=     Run Process     docker  exec    web     ls       -l      /Kiwi/uploads/email-messages/
    Log    ${ls.stdout}

    ${confirmUrl}=     Run Process     docker  exec    web     grep     -hR     passwordreset/confirm   /Kiwi/uploads/email-messages/
    Log    ${confirmUrl.stdout}

    # replace the domain b/c it doesn't have ports specification
    ${containerUrl}=      Replace String  ${confirmUrl.stdout}    https://testing.example.bg      ${SERVER}
    Log    ${containerUrl}

    Go To                 ${containerUrl}
    Title Should Be       Kiwi TCMS - Enter new password

    Input Text    id_new_password1    Updated-Passw0rd!
    Input Text    id_new_password2    Updated-Passw0rd!
    Click Button  Change password

    Location Should Be  ${PWD_RESET_COMPLETE}
    Title Should Be     Kiwi TCMS - Password reset complete


    # now try logging in with the new password
    Go To               ${LOGIN_URL}
    Title Should Be     Kiwi TCMS - Login

    # reuse LDAP login b/c that's a regular user account
    Input Text    inputUsername    super-root
    Input Text    inputPassword    Updated-Passw0rd!
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    [Teardown]    Close Browser
