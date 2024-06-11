# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-few-public-methods

import base64
import markdown


def mermaid2url(src_code):
    """
    Convert a Mermaid source code into a viewable URL where the image
    is generated by the Mermaid.Ink Web Service!
    """
    as_base64 = base64.b64encode(src_code.encode("utf8"))
    as_base64 = as_base64.decode("ascii")
    return f"https://mermaid.ink/img/{as_base64}?type=png"


class MermaidPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
        new_lines = []
        diagram_src = []
        diagram_started = False

        for line in lines:
            if line.lower().find("```mermaid") > -1:
                diagram_started = True
                diagram_src = []
            elif diagram_started and line.lower().strip() == "```":
                diagram_started = False

                image_url = mermaid2url("\n".join(diagram_src))
                new_lines.append(f"![diagram.png]({image_url})")
            elif diagram_started:
                diagram_src.append(line)
            else:
                new_lines.append(line)

        return new_lines


class KiwiTCMSExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        # Insert a preprocessor before ReferencePreprocessor
        md.preprocessors.register(MermaidPreprocessor(md), 'mermaid', 35)


def makeExtension(**kwargs):  # pylint: disable=invalid-name
    return KiwiTCMSExtension(**kwargs)