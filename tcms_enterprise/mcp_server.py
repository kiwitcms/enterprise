# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import inspect
import json

from modernrpc.constants import Protocol
from modernrpc.core import RpcRequestContext
from modernrpc.introspection import DocstringParser, Introspector
from modernrpc.jsonrpc.handler import JsonRpcHandler
from modernrpc.server import RpcServer

from tcms import __version__


class MCPHandler(JsonRpcHandler):
    PROTOCOL_VERSION = "2026-07-28"
    UNSUPPORTED_PROTOCOL_VERSION = -32022
    META_PROTOCOL_VERSION = "io.modelcontextprotocol/protocolVersion"

    def process_single_request(self, rpc_request, context):
        if rpc_request.method_name != "server/discover":
            kwargs = getattr(rpc_request, "kwargs", None) or {}
            meta = kwargs.get("_meta") or {}
            requested = meta.get(self.META_PROTOCOL_VERSION)

            if requested != self.PROTOCOL_VERSION:
                return self.build_error_result(
                    request=rpc_request,
                    code=self.UNSUPPORTED_PROTOCOL_VERSION,
                    message="Unsupported protocol version",
                    data={"supported": [self.PROTOCOL_VERSION], "requested": requested},
                )

        return super().process_single_request(rpc_request, context)

    def build_success_result(self, request, data):
        if isinstance(data, dict):
            data = {**data, "resultType": "complete"}

        return super().build_success_result(request, data)


class MCPServer(RpcServer):
    META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"

    def __init__(self, registry):
        super().__init__(
            supported_protocol=Protocol.JSON_RPC,
            register_system_procedures=False,
        )
        self.registry = registry
        self.handlers = [MCPHandler()]

        self.register_procedure(self.server_discover, name="server/discover", auth=None)
        self.register_procedure(self.tools_list, name="tools/list", auth=None)
        self.register_procedure(
            self.tools_call,
            name="tools/call",
            auth=None,
            context_target="mcp_context",
        )

    def server_discover(self, **kwargs):
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

    def tools_list(self, **kwargs):
        return {"tools": self.build_catalog()}

    def tools_call(self, name, arguments=None, mcp_context=None, **kwargs):
        method = self.registry.get(name)
        if method is None:
            return self.error_result(f"Unknown tool: {name}")

        request = mcp_context.request
        if method.auth is not None and not method.auth(request):
            return self.error_result(f"Authentication failed for {name}")

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
