# Copyright (c) 2021 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://testing.example.bg:8443
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/login/keycloak
${DASHBOARD_URL}        ${SERVER}/


*** Test Cases ***
Login via Keycloak
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Sign in to kiwi

    Input Text    username    kc_atodorov
    Input Text    password    h3llo-w0rld
    Click Button  Sign In

    # follow redirect
    Wait Until Location Contains        ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    [Teardown]    Close Browser
