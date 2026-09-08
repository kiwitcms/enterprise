# Copyright (c) 2021-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://testing.example.bg
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/accounts/login/
${DASHBOARD_URL}        ${SERVER}/


*** Test Cases ***
Login via OAuth2 redirect from Kiwi TCMS login page
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    # click on the Keycloak image which redirects to the OAuth2 authorization endpoint
    Wait Until Page Contains Element    id:login-icon-keycloak
    Click Element   id:login-icon-keycloak

    # we're now on the Keycloak login page
    Wait Until Location Contains    kc.example.bg:8080
    Title Should Be    Sign in to kiwi

    Input Text    username    kc_atodorov
    Input Text    password    h3llo-w0rld
    Click Button  Sign In

    # follow redirect back to Kiwi TCMS
    Wait Until Location Contains        ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    [Teardown]    Close Browser
