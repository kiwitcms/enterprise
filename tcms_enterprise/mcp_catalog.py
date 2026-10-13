# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import inspect

from tcms.rpc.views import json_rpc_server

_JSON_TYPE_BY_DOC = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "tuple": "array",
    "set": "array",
    "dict": "object",
}


def build_catalog():
    catalog = []
    for rpc_name, wrapper in sorted(json_rpc_server.procedures.items()):
        # MCP tools are invoked over JSON-RPC so procedures which are not
        # registered for that protocol (e.g. XML-RPC only) cannot be included
        if not wrapper.is_available_in_json_rpc:
            continue

        # exclude the RPC system procedures, they are not part of the API
        if rpc_name.startswith("system."):
            continue

        properties = {}
        required = []
        signature = wrapper.introspector.signature
        for arg, docs in wrapper.arguments.items():
            prop = {}
            if docs.docstring:
                prop["description"] = docs.docstring
            json_type = _JSON_TYPE_BY_DOC.get(docs.documented_type)
            if json_type:
                prop["type"] = json_type
            properties[arg] = prop

            param = signature.parameters.get(arg)
            if param is not None and param.default is inspect.Parameter.empty:
                required.append(arg)

        catalog.append(
            {
                "name": rpc_name,
                "description": wrapper.text_doc or f"Kiwi TCMS API method {rpc_name}",
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": True,
                },
            }
        )

    return catalog
