#!/bin/bash

# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# End-to-end test for the MCP endpoint, driven by an external agentic client
# (OpenClaw). Note: execute this file from the project root directory

. /usr/share/beakerlib/beakerlib.sh

HTTPS="https://testing.example.bg"

rlJournalStart
    rlPhaseStartTest "Boot the docker image"
        rlRun -t -c "docker compose -f docker-compose.testing up -d"
        sleep 5

        IP_ADDRESS=$(curl https://ifconfig.me)
        rlLogInfo "--- testing.example.bg: $IP_ADDRESS --"
        # openclaw will not connect to 127.0.0.1, so map the public IP locally
        rlRun -t -c "sudo ip addr add $IP_ADDRESS/32 dev lo"
        rlRun -t -c "sudo sed -i '/testing.example.bg/d' /etc/hosts"
        rlRun -t -c "sudo sh -c \"echo '$IP_ADDRESS    testing.example.bg     empty.testing.example.bg' >> /etc/hosts\""
        rlRun -t -c "cat /etc/hosts"
        rlRun -t -c "dig testing.example.bg"

        sleep 10
        rlRun -t -c "curl -k -L -o- --referer test_mcp $HTTPS/ | grep 'Welcome to Kiwi TCMS'"
    rlPhaseEnd

    rlPhaseStartTest "OAuth login for OpenClaw"
        rlRun -t -c "cat testing/mcp_user.py | docker exec -i web /Kiwi/manage.py shell"
        OPENCLAW="./testing/node_modules/.bin/openclaw"
        rlAssertExists "$OPENCLAW"

        rlRun -t -c "$OPENCLAW mcp add kiwitcms --transport streamable-http --url $HTTPS/mcp/ --auth oauth --oauth-scope 'kiwitcms:view kiwitcms:add kiwitcms:change kiwitcms:delete' --ssl-verify false"

        # start the OAuth flow: the CLI prints the authorization URL and waits for the callback
        $OPENCLAW mcp login kiwitcms > mcp-login.log 2>&1 &
        LOGIN_PID=$!

        AUTH_URL=""
        for _ in $(seq 1 30); do
            AUTH_URL=$(grep -m1 -oP '^https?://\S+$' mcp-login.log)
            [ -n "$AUTH_URL" ] && break
            sleep 1
        done
        rlAssertNotEquals "OAuth authorization URL obtained" "$AUTH_URL" ""

        # complete the authorization in the browser (login + consent)
        export AUTH_URL
        rlRun -t -c "robot testing/mcp_oauth.robot"

        wait "$LOGIN_PID"
        rlAssertEquals "OAuth login completed" "$?" "0"
    rlPhaseEnd

    rlPhaseStartTest "OpenClaw MCP sanity checks"
        rlRun -t -c "$OPENCLAW mcp probe kiwitcms --json > mcp-probe.json"
        rlRun -t -c "cat mcp-probe.json"
        rlRun -t -c "jq -e '.servers | length > 0' mcp-probe.json"
        rlRun -t -c "jq -e '.tools | length > 100' mcp-probe.json"
    rlPhaseEnd

    rlPhaseStartTest "execute OpenClaw agent"
        # use the local Ollama model
        rlRun -t -c "$OPENCLAW config set models.providers.ollama.baseUrl http://127.0.0.1:11434"
        rlRun -t -c "$OPENCLAW config set models.providers.ollama.params.num_ctx 16384"
        rlRun -t -c "$OPENCLAW config set models.providers.ollama.timeoutSeconds 3600"
        rlRun -t -c "$OPENCLAW config set agents.defaults.timeoutSeconds 3600"
        rlRun -t -c "$OPENCLAW config set agents.defaults.model.primary ollama/qwen2.5:7b"
        rlRun -t -c "$OPENCLAW config set agents.defaults.experimental.localModelLean true"
        rlRun -t -c "$OPENCLAW config set tools.toolSearch false"
        rlRun -t -c "$OPENCLAW config patch --file testing/openclaw_tools.json"
        export OLLAMA_API_KEY=ollama-local

        rlRun -t -c "$OPENCLAW mcp tools kiwitcms --include 'KiwiTCMS.version'"
        rlRun -t -c "$OPENCLAW agent --local --timeout 3600 -m 'What is the current Kiwi TCMS version' --json > mcp-agent.json 2> mcp-agent.log"
        rlRun -t -c "cat mcp-agent.json"

        # plain-text view of the same run, no second agent invocation
        rlRun -t -c "jq -r '.terminalReply.text // .meta.terminalReply.text // .final // .payloads[0].text' mcp-agent.json > test-mcp-agent.txt"
        rlRun -t -c "cat test-mcp-agent.txt"

        # the MCP tool ran and did not fail
        rlRun -t -c "jq -e '(.meta.toolSummary // .toolSummary) | .calls >= 1' mcp-agent.json"
        rlRun -t -c "jq -e '(.meta.toolSummary // .toolSummary) | (.failures // 0) == 0' mcp-agent.json"

        # it was the Kiwi TCMS MCP tool, not a built-in
        rlRun -t -c "jq -e '((.meta.toolSummary // .toolSummary).tools // []) | join(\",\") | ascii_downcase | test(\"kiwitcms[-.]version\")' mcp-agent.json"

        # the answer matches the version served by the web container
        rlRun -t -c "docker exec -i web /venv/bin/python -c 'import tcms; print(tcms.__version__)' > test-expected-version.txt"
        EXPECTED_VERSION=$(cat test-expected-version.txt)
        rlAssertNotEquals "expected version obtained" "$EXPECTED_VERSION" ""
        rlAssertGrep "Kiwi TCMS is $EXPECTED_VERSION" test-mcp-agent.txt
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker compose -f docker-compose.testing logs --no-color > docker.log"
        rlRun -t -c "docker compose -f docker-compose.testing down"
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
