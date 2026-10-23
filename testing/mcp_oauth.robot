# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${BROWSER}        Headless Firefox

*** Test Cases ***
Authorize The MCP Client
    Open Browser    %{AUTH_URL}    ${BROWSER}
    Maximize Browser Window
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    openclaw-dev
    Input Text    inputPassword    password
    Click Button    Log in

    Wait Until Page Contains Element    name=allow
    Click Element    name=allow

    Wait Until Page Contains    Authorization received

    [Teardown]    Close Browser
