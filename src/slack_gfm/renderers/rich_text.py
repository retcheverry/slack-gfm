"""Renderer for Slack Rich Text format.

Converts AST to Slack Rich Text JSON structure.
"""

from typing import Any

from ..ast import (
    AnyBlock,
    AnyInline,
    AnyNode,
    Bold,
    Broadcast,
    ChannelMention,
    Code,
    CodeBlock,
    DateTimestamp,
    Document,
    Emoji,
    Heading,
    InlineNode,
    Italic,
    Link,
    List,
    Paragraph,
    Quote,
    Strikethrough,
    Text,
    UsergroupMention,
    UserMention,
)


def render_rich_text(node: AnyNode) -> dict[str, Any]:
    """Render an AST node to Slack Rich Text JSON.

    Args:
        node: AST node to render (typically a Document)

    Returns:
        Rich Text block dict

    Example:
        >>> from slack_gfm.ast import Document, Paragraph, Text
        >>> doc = Document(children=[Paragraph(children=[Text(content="Hello")])])
        >>> rich_text = render_rich_text(doc)
    """
    if isinstance(node, Document):
        elements = [_render_block(child) for child in node.children]
        return {"type": "rich_text", "elements": elements}
    else:
        # Single block
        return {"type": "rich_text", "elements": [_render_block(node)]}  # type: ignore


def _render_block(node: AnyBlock) -> dict[str, Any]:
    """Render a block-level node."""
    if isinstance(node, Paragraph):
        return _render_paragraph(node)
    elif isinstance(node, Heading):
        # Rich Text doesn't have headings - render as bold paragraph
        return _render_heading_as_paragraph(node)
    elif isinstance(node, CodeBlock):
        return _render_codeblock(node)
    elif isinstance(node, Quote):
        return _render_quote(node)
    elif isinstance(node, List):
        return _render_list(node)
    else:
        # Unknown block type - render as empty section
        return {"type": "rich_text_section", "elements": []}


def _render_paragraph(para: Paragraph) -> dict[str, Any]:
    """Render Paragraph as rich_text_section."""
    elements = [_render_inline(child) for child in para.children]
    return {"type": "rich_text_section", "elements": elements}


def _render_heading_as_paragraph(heading: Heading) -> dict[str, Any]:
    """Render Heading as bold paragraph (Rich Text doesn't support headings)."""
    # Render children as bold text
    elements = []
    for child in heading.children:
        inline_elem = _render_inline(child)
        # Wrap in bold style if it's a text element
        if inline_elem.get("type") == "text":
            style = inline_elem.get("style", {})
            style["bold"] = True
            inline_elem["style"] = style
        elements.append(inline_elem)

    return {"type": "rich_text_section", "elements": elements}


def _render_codeblock(codeblock: CodeBlock) -> dict[str, Any]:
    """Render CodeBlock as rich_text_preformatted."""
    return {
        "type": "rich_text_preformatted",
        "elements": [{"type": "text", "text": codeblock.content}],
    }


def _render_quote(quote: Quote) -> dict[str, Any]:
    """Render Quote as rich_text_quote."""
    # Flatten children into inline elements
    elements = []
    for child in quote.children:
        if isinstance(child, Paragraph):
            elements.extend([_render_inline(e) for e in child.children])
        # Add newline between blocks
        if child != quote.children[-1]:
            elements.append({"type": "text", "text": "\n"})

    return {"type": "rich_text_quote", "elements": elements}


def _render_list(list_node: List) -> dict[str, Any]:
    """Render List as rich_text_list."""
    style = "ordered" if list_node.ordered else "bullet"
    elements = []

    for item in list_node.children:
        # Each item is a rich_text_section
        # Filter only inline elements from ListItem children
        inline_children = [c for c in item.children if isinstance(c, InlineNode)]
        item_elements = [_render_inline(child) for child in inline_children]
        elements.append({"type": "rich_text_section", "elements": item_elements})

    return {
        "type": "rich_text_list",
        "style": style,
        "elements": elements,
        "indent": 0,
    }


def _render_inline(node: AnyInline) -> dict[str, Any]:
    """Render an inline-level node."""
    if isinstance(node, Text):
        return _render_text(node)
    elif isinstance(node, Bold):
        return _render_bold(node)
    elif isinstance(node, Italic):
        return _render_italic(node)
    elif isinstance(node, Strikethrough):
        return _render_strikethrough(node)
    elif isinstance(node, Code):
        return _render_code(node)
    elif isinstance(node, Link):
        return _render_link(node)
    elif isinstance(node, UserMention):
        return _render_user_mention(node)
    elif isinstance(node, ChannelMention):
        return _render_channel_mention(node)
    elif isinstance(node, UsergroupMention):
        return _render_usergroup_mention(node)
    elif isinstance(node, Broadcast):
        return _render_broadcast(node)
    elif isinstance(node, Emoji):
        return _render_emoji(node)
    elif isinstance(node, DateTimestamp):
        return _render_date(node)
    else:
        return {"type": "text", "text": ""}


def _render_text(text: Text) -> dict[str, Any]:
    """Render Text node."""
    return {"type": "text", "text": text.content}


def _render_bold(bold: Bold) -> dict[str, Any]:
    """Render Bold node."""
    # Extract text from children and apply bold style
    text_content = _extract_text_from_inlines(bold.children)
    return {"type": "text", "text": text_content, "style": {"bold": True}}


def _render_italic(italic: Italic) -> dict[str, Any]:
    """Render Italic node."""
    text_content = _extract_text_from_inlines(italic.children)
    return {"type": "text", "text": text_content, "style": {"italic": True}}


def _render_strikethrough(strike: Strikethrough) -> dict[str, Any]:
    """Render Strikethrough node."""
    text_content = _extract_text_from_inlines(strike.children)
    return {"type": "text", "text": text_content, "style": {"strike": True}}


def _render_code(code: Code) -> dict[str, Any]:
    """Render inline Code node."""
    return {"type": "text", "text": code.content, "style": {"code": True}}


def _render_link(link: Link) -> dict[str, Any]:
    """Render Link node."""
    elem: dict[str, Any] = {"type": "link", "url": link.url}

    # Add text if present
    if link.children:
        text_content = _extract_text_from_inlines(link.children)
        elem["text"] = text_content

    return elem


def _render_user_mention(mention: UserMention) -> dict[str, Any]:
    """Render UserMention node."""
    return {"type": "user", "user_id": mention.user_id}


def _render_channel_mention(mention: ChannelMention) -> dict[str, Any]:
    """Render ChannelMention node."""
    return {"type": "channel", "channel_id": mention.channel_id}


def _render_usergroup_mention(mention: UsergroupMention) -> dict[str, Any]:
    """Render UsergroupMention node."""
    return {"type": "usergroup", "usergroup_id": mention.usergroup_id}


def _render_broadcast(broadcast: Broadcast) -> dict[str, Any]:
    """Render Broadcast node."""
    return {"type": "broadcast", "range": broadcast.range}


def _render_emoji(emoji: Emoji) -> dict[str, Any]:
    """Render Emoji node."""
    elem: dict[str, Any] = {"type": "emoji", "name": emoji.name}
    if emoji.unicode:
        elem["unicode"] = emoji.unicode
    return elem


def _render_date(date: DateTimestamp) -> dict[str, Any]:
    """Render DateTimestamp node."""
    elem: dict[str, Any] = {"type": "date", "timestamp": date.timestamp}
    if date.format:
        elem["format"] = date.format
    if date.fallback:
        elem["fallback"] = date.fallback
    return elem


def _extract_text_from_inlines(inlines: list[AnyInline]) -> str:
    """Extract plain text content from inline nodes."""
    parts = []
    for node in inlines:
        if isinstance(node, Text):
            parts.append(node.content)
        elif isinstance(node, Code):
            parts.append(node.content)
        elif hasattr(node, "children"):
            parts.append(_extract_text_from_inlines(node.children))
    return "".join(parts)
