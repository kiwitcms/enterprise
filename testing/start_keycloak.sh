#!/bin/bash

# Copyright (c) 2021-2022 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

set -x


docker network create enterprise_default || echo "Moving on"

docker run --rm -d -p 8080:8080 --name keycloak_server \
    --network=enterprise_default \
    -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin quay.io/keycloak/keycloak:16.1.1

sleep 10

KC_ADDRESS=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' keycloak_server`

if [ -z "$(grep kc.example.bg /etc/hosts)" ]; then
    echo "--- kc.example.bg: $IP_ADDRESS --"
    sudo sh -c "echo '$KC_ADDRESS    kc.example.bg' >> /etc/hosts"
fi

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080/auth \
        --realm master --user admin --password admin

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh create realms -s realm=kiwi -s enabled=true

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh create clients \
        -r kiwi -s clientId=kiwitcms-web-app -s enabled=true -s protocol=openid-connect \
        -s attributes='{"user.info.response.signature.alg": "RS256"}' \
        -s publicClient=false -s rootUrl=https://testing.example.bg:8443 -o > kc_client.json
KC_CLIENT_ID=`cat kc_client.json | jq -r '.id'`

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh create clients/$KC_CLIENT_ID/protocol-mappers/models \
    -r kiwi -s name='Audience Mapper' -s protocol=openid-connect \
    -s protocolMapper=oidc-audience-mapper \
    -s config='{"included.client.audience": "kiwitcms-web-app", "access.token.claim": "true"}'

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh get keys -r kiwi > kc_realm_keys.json
KC_PUBLIC_KEY=`cat kc_realm_keys.json | jq -r '.keys | .[] | select(.algorithm | contains("RS256")) | .publicKey'`

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh get clients/$KC_CLIENT_ID/client-secret -r kiwi > kc_client_secret.json
KC_CLIENT_SECRET=`cat kc_client_secret.json | jq -r '.value'`

echo "KC_PUBLIC_KEY=\"$KC_PUBLIC_KEY\"" > /tmp/kc.env
echo "KC_CLIENT_SECRET=\"$KC_CLIENT_SECRET\"" >> /tmp/kc.env

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh create users -r kiwi -s username=kc_bot -s enabled=false

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh create users -r kiwi -s username=kc_atodorov -s enabled=true \
        -s email=atodorov@kc.example.bg -o --fields id > kc_atodorov.json

cat kc_atodorov.json
KC_USER_ID=`cat kc_atodorov.json | jq -r ".id"`

docker exec -i keycloak_server \
    /opt/jboss/keycloak/bin/kcadm.sh update users/$KC_USER_ID/reset-password \
        -r kiwi -s type=password -s value=h3llo-w0rld -s temporary=false -n
