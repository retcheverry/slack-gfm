"""Renderer for GitHub Flavored Markdown (GFM).

Converts AST to GFM string format.

This module now uses a visitor-based renderer for proper handling of
complex nested styles.
"""

from ..ast import AnyNode
from .gfm_visitor import render_gfm_visitor


def render_gfm(node: AnyNode) -> str:
    """Render an AST node to GitHub Flavored Markdown.

    Slack-specific features (user mentions, channel mentions, broadcasts) are
    converted to GFM links with custom slack:// URLs to preserve all information
    for round-trip conversion.

    Args:
        node: AST node to render

    Returns:
        GFM string

    Example:
        >>> from slack_gfm.ast import Document, Paragraph, Text
        >>> doc = Document(children=[Paragraph(children=[Text(content="Hello")])])
        >>> gfm = render_gfm(doc)
        >>> print(gfm)
        Hello
    """
    return render_gfm_visitor(node)
