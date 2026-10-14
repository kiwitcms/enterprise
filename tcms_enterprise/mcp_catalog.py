# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import inspect

from modernrpc.introspection import DocstringParser, Introspector

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


def build_catalog(registry):
    catalog = []
    for name, method in sorted(registry.items()):
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
            json_type = _JSON_TYPE_BY_DOC.get(parser.args_types.get(arg, ""))
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
