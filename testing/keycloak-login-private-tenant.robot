# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${EMPTY_TENANT_SERVER}          https://empty.testing.example.bg
${BROWSER}                      Headless Firefox
${DELAY}                        0
${EMPTY_TENANT_LOGIN_URL}       ${EMPTY_TENANT_SERVER}/accounts/login/
${EMPTY_TENANT_DASHBOARD_URL}   ${EMPTY_TENANT_SERVER}/


*** Test Cases ***
Login via OAuth2 redirect from non-public tenant login page
    Open Browser    https://testing.example.bg/accounts/login/    ${BROWSER}
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

    # follow redirect back to the non-public tenant dashboard
    Wait Until Location Contains        ${EMPTY_TENANT_DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    [Teardown]    Close Browser
