# Copyright (c) 2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://testing.example.bg:8443
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/accounts/login/
${DASHBOARD_URL}        ${SERVER}/


*** Test Cases ***
Login with LDAP username and password
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    ldap_atodorov
    Input Text    inputPassword    h3llo-w0rld
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    [Teardown]    Close Browser
