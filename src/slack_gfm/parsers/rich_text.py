"""Parser for Slack Rich Text format.

Converts Slack Rich Text JSON structure to AST.
"""

from typing import Any

from ..ast import (
    AnyBlock,
    AnyInline,
    BlockNode,
    Bold,
    Broadcast,
    ChannelMention,
    Code,
    CodeBlock,
    DateTimestamp,
    Document,
    Emoji,
    Italic,
    Link,
    List,
    ListItem,
    Paragraph,
    Quote,
    Strikethrough,
    Text,
    UsergroupMention,
    UserMention,
)


def parse_rich_text(rich_text_data: dict[str, Any] | list[dict[str, Any]]) -> Document:
    """Parse Slack Rich Text JSON to AST.

    Args:
        rich_text_data: Rich Text data - either a full rich_text block dict
                       or just the elements array

    Returns:
        Document AST node

    Example:
        >>> rich_text = {
        ...     "type": "rich_text",
        ...     "elements": [
        ...         {
        ...             "type": "rich_text_section",
        ...             "elements": [
        ...                 {"type": "text", "text": "Hello world"}
        ...             ]
        ...         }
        ...     ]
        ... }
        >>> doc = parse_rich_text(rich_text)
    """
    # Handle both full block and just elements array
    if isinstance(rich_text_data, list):
        elements = rich_text_data
    else:
        elements = rich_text_data.get("elements", [])

    children = [_parse_block_element(elem) for elem in elements]
    return Document(children=children)


def _parse_block_element(element: dict[str, Any]) -> AnyBlock:
    """Parse a block-level rich text element."""
    elem_type = element.get("type", "")

    if elem_type == "rich_text_section":
        return _parse_section(element)
    elif elem_type == "rich_text_list":
        return _parse_list(element)
    elif elem_type == "rich_text_preformatted":
        return _parse_preformatted(element)
    elif elem_type == "rich_text_quote":
        return _parse_quote(element)
    else:
        # Unknown block type - treat as paragraph
        return Paragraph(children=[])


def _parse_section(section: dict[str, Any]) -> Paragraph:
    """Parse a rich_text_section into a Paragraph."""
    elements = section.get("elements", [])
    children = [_parse_inline_element(elem) for elem in elements]
    return Paragraph(children=children)


def _parse_list(list_elem: dict[str, Any]) -> List:
    """Parse a rich_text_list into a List."""
    style = list_elem.get("style", "bullet")
    ordered = style == "ordered"
    elements = list_elem.get("elements", [])

    # Each element in a rich_text_list is a rich_text_section
    items = []
    for elem in elements:
        if elem.get("type") == "rich_text_section":
            inline_elements: list[AnyInline] = [
                _parse_inline_element(e) for e in elem.get("elements", [])
            ]
            items.append(ListItem(children=inline_elements))  # type: ignore[arg-type]

    return List(ordered=ordered, children=items)


def _parse_preformatted(preformatted: dict[str, Any]) -> CodeBlock:
    """Parse a rich_text_preformatted into a CodeBlock."""
    elements = preformatted.get("elements", [])
    # Extract text content from elements
    content_parts = []
    for elem in elements:
        if elem.get("type") == "text":
            content_parts.append(elem.get("text", ""))

    content = "".join(content_parts)
    return CodeBlock(content=content)


def _parse_quote(quote: dict[str, Any]) -> Quote:
    """Parse a rich_text_quote into a Quote."""
    elements = quote.get("elements", [])
    # Parse inline elements into paragraphs
    paragraph = Paragraph(children=[_parse_inline_element(e) for e in elements])
    children: list[BlockNode] = [paragraph]
    return Quote(children=children)


def _parse_inline_element(element: dict[str, Any]) -> AnyInline:
    """Parse an inline-level element."""
    elem_type = element.get("type", "")

    if elem_type == "text":
        return _parse_text(element)
    elif elem_type == "link":
        return _parse_link(element)
    elif elem_type == "emoji":
        return _parse_emoji(element)
    elif elem_type == "user":
        return _parse_user(element)
    elif elem_type == "channel":
        return _parse_channel(element)
    elif elem_type == "usergroup":
        return _parse_usergroup(element)
    elif elem_type == "date":
        return _parse_date(element)
    elif elem_type == "broadcast":
        return _parse_broadcast(element)
    else:
        # Unknown inline type - return empty text
        return Text(content="")


def _parse_text(text_elem: dict[str, Any]) -> AnyInline:
    """Parse a text element with optional styles."""
    content = text_elem.get("text", "")
    style = text_elem.get("style", {})

    # Build nested style nodes
    node: AnyInline = Text(content=content)

    if style.get("code"):
        return Code(content=content)

    # Apply styles in order: bold -> italic -> strikethrough
    if style.get("bold"):
        node = Bold(children=[node])
    if style.get("italic"):
        node = Italic(children=[node])
    if style.get("strike"):
        node = Strikethrough(children=[node])

    return node


def _parse_link(link_elem: dict[str, Any]) -> Link:
    """Parse a link element."""
    url = link_elem.get("url", "")
    text = link_elem.get("text")
    style = link_elem.get("style", {})

    # Link text
    children: list[AnyInline] = []
    if text:
        text_node: AnyInline = Text(content=text)
        # Apply styles to link text
        if style.get("bold"):
            text_node = Bold(children=[text_node])
        if style.get("italic"):
            text_node = Italic(children=[text_node])
        if style.get("strike"):
            text_node = Strikethrough(children=[text_node])
        children = [text_node]

    return Link(url=url, children=children)


def _parse_emoji(emoji_elem: dict[str, Any]) -> Emoji:
    """Parse an emoji element."""
    name = emoji_elem.get("name", "")
    unicode_str = emoji_elem.get("unicode")
    return Emoji(name=name, unicode=unicode_str)


def _parse_user(user_elem: dict[str, Any]) -> UserMention:
    """Parse a user mention element."""
    user_id = user_elem.get("user_id", "")
    # Slack doesn't include username in Rich Text, will be filled by transformer
    return UserMention(user_id=user_id)


def _parse_channel(channel_elem: dict[str, Any]) -> ChannelMention:
    """Parse a channel mention element."""
    channel_id = channel_elem.get("channel_id", "")
    return ChannelMention(channel_id=channel_id)


def _parse_usergroup(usergroup_elem: dict[str, Any]) -> UsergroupMention:
    """Parse a usergroup mention element."""
    usergroup_id = usergroup_elem.get("usergroup_id", "")
    return UsergroupMention(usergroup_id=usergroup_id)


def _parse_date(date_elem: dict[str, Any]) -> DateTimestamp:
    """Parse a date element."""
    timestamp = int(date_elem.get("timestamp", 0))
    date_format = date_elem.get("format")
    fallback = date_elem.get("fallback")
    return DateTimestamp(timestamp=timestamp, format=date_format, fallback=fallback)


def _parse_broadcast(broadcast_elem: dict[str, Any]) -> Broadcast:
    """Parse a broadcast element."""
    range_type = broadcast_elem.get("range", "here")
    return Broadcast(type=range_type)
