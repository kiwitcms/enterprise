*** Settings ***
Library           OperatingSystem
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://testing.example.bg:8443
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/accounts/login/
${DASHBOARD_URL}        ${SERVER}/
${TEST_PLAN_URL}        ${SERVER}/plan/1/


*** Test Cases ***
Uploading file works via file upload
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    super-root
    Input Text    inputPassword    secret-2a9a34cd-e51d-4039-b709-b45f629a5595
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${TEST_PLAN_URL}
    Create File   ${TEMPDIR}${/}hello-robots.txt   Hello Robots
    Choose File   id:id_attachment_file    ${TEMPDIR}${/}hello-robots.txt
    Click Button  Add attachment
    Page Should Contain   Your attachment was uploaded

    [Teardown]    Close Browser
