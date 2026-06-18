# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

*** Settings ***
Library           SeleniumLibrary

*** Variables ***
# "empty" tenant is created during initial_setup
${SERVER}               https://testing.example.bg:8443
${BROWSER}              Headless Firefox
${DELAY}                0
${PWD_RESET_URL}        ${SERVER}/accounts/passwordreset/
${PWD_RESET_DONE}       ${SERVER}/accounts/passwordreset/done/


*** Test Cases ***
Regular User Can Request Password Reset
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
    [Teardown]    Close Browser
