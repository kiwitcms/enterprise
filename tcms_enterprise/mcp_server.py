# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import inspect
import json
from http import HTTPStatus

from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_tenants.utils import get_public_schema_name

from modernrpc.constants import Protocol
from modernrpc.core import RpcRequestContext
from modernrpc.exceptions import RPCInvalidRequest
from modernrpc.introspection import DocstringParser, Introspector
from modernrpc.jsonrpc.handler import JsonRpcHandler
from modernrpc.server import RpcServer

from tcms import __version__
from tcms.rpc.handlers import KiwiTCMSHandlerMixin

from tcms_enterprise.mcp_scopes import SCOPES, has_required_scopes, required_scopes


class MCPHandler(JsonRpcHandler):
    PROTOCOL_VERSION = "2026-07-28"
    SUPPORTED_VERSIONS = (
        "2026-07-28",
        "DRAFT-2026-v1",
        "2025-11-25",
        "2025-06-18",
        "2025-03-26",
        "2024-11-05",
        "2024-10-07",
    )
    UNSUPPORTED_PROTOCOL_VERSION = -32022
    META_PROTOCOL_VERSION = "io.modelcontextprotocol/protocolVersion"
    HANDSHAKE_METHODS = (
        "initialize",
        "notifications/initialized",
        "server/discover",
    )

    def process_single_request(self, rpc_request, context):
        if rpc_request.method_name not in self.HANDSHAKE_METHODS:
            kwargs = getattr(rpc_request, "kwargs", None) or {}
            meta = kwargs.get("_meta") or {}
            requested = meta.get(self.META_PROTOCOL_VERSION)

            # _meta is optional; clients which negotiated via initialize()
            # don't send it. Only reject an explicitly unsupported version.
            if requested is not None and requested not in self.SUPPORTED_VERSIONS:
                return self.build_error_result(
                    request=rpc_request,
                    code=self.UNSUPPORTED_PROTOCOL_VERSION,
                    message="Unsupported protocol version",
                    data={
                        "supported": list(self.SUPPORTED_VERSIONS),
                        "requested": requested,
                    },
                )

        return super().process_single_request(rpc_request, context)

    def build_success_result(self, request, data):
        if isinstance(data, dict):
            data = {**data, "resultType": "complete"}

        return super().build_success_result(request, data)


class MCPServer(RpcServer):
    META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"
    DISCOVERY_METHODS = ("server/discover", "tools/list")

    def __init__(self, registry):
        super().__init__(
            supported_protocol=Protocol.JSON_RPC,
            register_system_procedures=False,
        )
        self.registry = registry
        self.handlers = [MCPHandler()]

        self.register_procedure(self.initialize, name="initialize", auth=None)
        self.register_procedure(
            self.notifications_initialized,
            name="notifications/initialized",
            auth=None,
        )
        self.register_procedure(self.server_discover, name="server/discover", auth=None)
        self.register_procedure(
            self.tools_call,
            name="tools/call",
            auth=None,
            context_target="mcp_context",
        )
        self.register_procedure(self.tools_list, name="tools/list", auth=None)

    @staticmethod
    def request_payload(request):
        return json.loads(request.body)

    def requested_scopes(self, payload):
        if payload.get("method") == "tools/call":
            params = payload.get("params", {})
            method = self.registry.get(params.get("name"))
            if method is not None:
                return required_scopes(method) or {SCOPES["view"]}

        return {SCOPES["view"]}

    def check_request(self, request):
        payload = self.request_payload(request)
        if payload.get("method") in self.DISCOVERY_METHODS:
            return super().check_request(request)

        if request.user.is_authenticated:
            # a user which is not authorized on non-public schema is forbidden
            forbidden = (
                request.tenant.schema_name != get_public_schema_name()
                and not request.tenant.authorized_users.filter(
                    pk=request.user.pk
                ).exists()
            )
        else:
            # a token which was not found on this tenant is forbidden
            forbidden = getattr(
                request, "access_token", None
            ) is None and request.META.get("HTTP_AUTHORIZATION", "")

        if forbidden:
            return HttpResponseForbidden(_("Unauthorized"))

        if not request.user.is_authenticated:
            return self.build_unauthorized_response(
                request, self.requested_scopes(payload)
            )

        return super().check_request(request)

    @staticmethod
    def build_unauthorized_response(request, scopes):
        metadata_url = request.build_absolute_uri(
            reverse("mcp-oauth-protected-resource")
        )
        scope = " ".join(sorted(scopes))
        response = HttpResponse(status=HTTPStatus.UNAUTHORIZED)
        response["WWW-Authenticate"] = (
            f'Bearer resource_metadata="{metadata_url}", scope="{scope}"'
        )
        return response

    @staticmethod
    def initialize(**kwargs):
        negotiated = kwargs.get("protocolVersion")
        if negotiated not in MCPHandler.SUPPORTED_VERSIONS:
            negotiated = MCPHandler.PROTOCOL_VERSION

        return {
            "protocolVersion": negotiated,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "kiwitcms",
                "version": __version__,
            },
        }

    @staticmethod
    def notifications_initialized(**kwargs):
        return None

    def server_discover(self, **kwargs):
        # kept for MCP clients which don't perform initialize at all
        return {
            "supportedVersions": [MCPHandler.PROTOCOL_VERSION],
            "capabilities": {"tools": {}},
            "_meta": {
                self.META_SERVER_INFO: {
                    "name": "kiwitcms",
                    "version": __version__,
                },
            },
        }

    def build_catalog(self):
        json_type_by_doc = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "tuple": "array",
            "set": "array",
            "dict": "object",
        }

        catalog = []
        for name, method in sorted(self.registry.items()):
            parser = DocstringParser(method.func)
            signature = Introspector(method.func).signature

            properties = {}
            required = []
            for arg in signature.parameters:
                # the RPC request context is injected by the server, not a tool argument
                if arg == method.context_target:
                    continue

                prop = {}
                arg_doc = parser.args_docstrings.get(arg)
                if arg_doc:
                    prop["description"] = arg_doc
                json_type = json_type_by_doc.get(parser.args_types.get(arg, ""))
                if json_type:
                    prop["type"] = json_type
                properties[arg] = prop

                if signature.parameters[arg].default is inspect.Parameter.empty:
                    required.append(arg)

            catalog.append(
                {
                    "name": name,
                    "description": parser.docstring or f"Kiwi TCMS API method {name}",
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": True,
                    },
                }
            )

        return catalog

    @staticmethod
    def granted_scopes(request):
        token = getattr(request, "access_token", None)
        if token is None:
            return {"kiwitcms:none"}

        return set(token.scope.split())

    def tools_list(self, **kwargs):
        return {"tools": self.build_catalog()}

    def tools_call(self, name, arguments=None, mcp_context=None, **kwargs):
        method = self.registry.get(name)
        if method is None:
            return self.error_result(f"Unknown tool: {name}")

        try:
            KiwiTCMSHandlerMixin.inspect_rpc_args(name, kwargs=arguments or {})
        except RPCInvalidRequest as exc:
            return self.error_result(exc.message)

        request = mcp_context.request
        if method.auth is not None and not method.auth(request):
            return self.error_result(f"Authentication failed for {name}")

        if not has_required_scopes(
            required_scopes(method), self.granted_scopes(request)
        ):
            return self.error_result(f"Insufficient scope for {name}")

        arguments = dict(arguments or {})
        if method.context_target:
            arguments[method.context_target] = RpcRequestContext(
                request=request,
                server=None,
                handler=mcp_context.handler,
                protocol=Protocol.JSON_RPC,
            )

        try:
            value = method.func(**arguments)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return self.error_result(str(exc))

        text = json.dumps(value, ensure_ascii=False, default=str)
        return {"content": [{"type": "text", "text": text}], "isError": False}

    @staticmethod
    def error_result(message):
        return {"content": [{"type": "text", "text": message}], "isError": True}
