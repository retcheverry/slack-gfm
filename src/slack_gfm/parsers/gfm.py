"""Parser for GitHub Flavored Markdown (GFM).

Converts GFM string to AST using markdown-it-py.
"""

from urllib.parse import parse_qs, urlparse

from markdown_it import MarkdownIt
from markdown_it.token import Token

from ..ast import (
    AnyBlock,
    AnyInline,
    Bold,
    Broadcast,
    ChannelMention,
    Code,
    CodeBlock,
    DateTimestamp,
    Document,
    Heading,
    HorizontalRule,
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


def parse_gfm(gfm_text: str) -> Document:
    """Parse GitHub Flavored Markdown to AST.

    Recognizes custom slack:// URLs and converts them back to Slack-specific nodes.

    Args:
        gfm_text: GFM markdown string

    Returns:
        Document AST node

    Example:
        >>> gfm = "**Hello** world"
        >>> doc = parse_gfm(gfm)
    """
    md = MarkdownIt("gfm-like").enable(["table", "strikethrough"])
    tokens = md.parse(gfm_text)
    return _parse_tokens(tokens)


def _parse_tokens(tokens: list[Token]) -> Document:
    """Parse markdown-it tokens into Document AST."""
    blocks: list[AnyBlock] = []
    i = 0
    while i < len(tokens):
        block, consumed = _parse_block_token(tokens, i)
        if block:
            blocks.append(block)
        i += consumed

    return Document(children=blocks)


def _parse_block_token(tokens: list[Token], start_idx: int) -> tuple[AnyBlock | None, int]:
    """Parse a block-level token.

    Returns:
        (block_node, tokens_consumed)
    """
    token = tokens[start_idx]

    if token.type == "heading_open":
        return _parse_heading(tokens, start_idx)
    elif token.type == "paragraph_open":
        return _parse_paragraph(tokens, start_idx)
    elif token.type == "fence" or token.type == "code_block":
        return _parse_code_block(token), 1
    elif token.type == "blockquote_open":
        return _parse_blockquote(tokens, start_idx)
    elif token.type == "bullet_list_open" or token.type == "ordered_list_open":
        return _parse_list(tokens, start_idx)
    elif token.type == "hr":
        return HorizontalRule(), 1
    else:
        # Unknown or already handled
        return None, 1


def _parse_heading(tokens: list[Token], start_idx: int) -> tuple[Heading, int]:
    """Parse heading tokens."""
    heading_open = tokens[start_idx]
    level = int(heading_open.tag[1])  # h1 -> 1, h2 -> 2, etc.

    # Find inline content and closing tag
    inline_idx = start_idx + 1
    inlines = _parse_inline_tokens(tokens[inline_idx]) if inline_idx < len(tokens) else []

    # heading_open, inline, heading_close = 3 tokens
    return Heading(level=level, children=inlines), 3


def _parse_paragraph(tokens: list[Token], start_idx: int) -> tuple[Paragraph, int]:
    """Parse paragraph tokens."""
    # paragraph_open, inline, paragraph_close
    inline_idx = start_idx + 1
    inlines = _parse_inline_tokens(tokens[inline_idx]) if inline_idx < len(tokens) else []

    return Paragraph(children=inlines), 3


def _parse_code_block(token: Token) -> CodeBlock:
    """Parse code block token."""
    content = token.content
    language = token.info if token.info else None
    return CodeBlock(content=content, language=language)


def _parse_blockquote(tokens: list[Token], start_idx: int) -> tuple[Quote, int]:
    """Parse blockquote tokens."""
    # Find matching close token
    close_idx = _find_closing_token(tokens, start_idx, "blockquote_open", "blockquote_close")

    # Parse children
    children: list[AnyBlock] = []
    i = start_idx + 1
    while i < close_idx:
        block, consumed = _parse_block_token(tokens, i)
        if block:
            children.append(block)
        i += consumed

    consumed_total = close_idx - start_idx + 1
    return Quote(children=children), consumed_total


def _parse_list(tokens: list[Token], start_idx: int) -> tuple[List, int]:
    """Parse list tokens."""
    list_open = tokens[start_idx]
    ordered = list_open.type == "ordered_list_open"

    # Find closing token
    close_type = "ordered_list_close" if ordered else "bullet_list_close"
    close_idx = _find_closing_token(tokens, start_idx, list_open.type, close_type)

    # Parse list items
    items: list[ListItem] = []
    i = start_idx + 1
    while i < close_idx:
        if tokens[i].type == "list_item_open":
            item, consumed = _parse_list_item(tokens, i)
            items.append(item)
            i += consumed
        else:
            i += 1

    consumed_total = close_idx - start_idx + 1
    return List(ordered=ordered, children=items), consumed_total


def _parse_list_item(tokens: list[Token], start_idx: int) -> tuple[ListItem, int]:
    """Parse list item tokens."""
    # Find closing token
    close_idx = _find_closing_token(tokens, start_idx, "list_item_open", "list_item_close")

    # Parse children (can be paragraphs or other blocks)
    children: list[AnyInline | AnyBlock] = []
    i = start_idx + 1
    while i < close_idx:
        if tokens[i].type == "paragraph_open":
            para, consumed = _parse_paragraph(tokens, i)
            # For list items, extract inline content directly
            children.extend(para.children)
            i += consumed
        else:
            block, consumed = _parse_block_token(tokens, i)
            if block:
                children.append(block)
            i += consumed

    consumed_total = close_idx - start_idx + 1
    return ListItem(children=children), consumed_total


def _parse_inline_tokens(inline_token: Token) -> list[AnyInline]:
    """Parse inline token children."""
    if not inline_token.children:
        return []

    inlines: list[AnyInline] = []
    i = 0
    tokens = inline_token.children

    while i < len(tokens):
        token = tokens[i]

        if token.type == "text":
            inlines.append(Text(content=token.content))
        elif token.type == "code_inline":
            inlines.append(Code(content=token.content))
        elif token.type == "strong_open":
            # Find children until strong_close
            children, consumed = _parse_styled_inline(tokens, i, "strong_open", "strong_close")
            inlines.append(Bold(children=children))
            i += consumed - 1  # -1 because loop will increment
        elif token.type == "em_open":
            children, consumed = _parse_styled_inline(tokens, i, "em_open", "em_close")
            inlines.append(Italic(children=children))
            i += consumed - 1
        elif token.type == "s_open":
            children, consumed = _parse_styled_inline(tokens, i, "s_open", "s_close")
            inlines.append(Strikethrough(children=children))
            i += consumed - 1
        elif token.type == "link_open":
            link, consumed = _parse_link(tokens, i)
            inlines.append(link)
            i += consumed - 1
        elif token.type == "softbreak":
            inlines.append(Text(content="\n"))
        elif token.type == "hardbreak":
            inlines.append(Text(content="\n"))

        i += 1

    return inlines


def _parse_styled_inline(
    tokens: list[Token], start_idx: int, open_type: str, close_type: str
) -> tuple[list[AnyInline], int]:
    """Parse styled inline content (bold, italic, strikethrough)."""
    children: list[AnyInline] = []
    i = start_idx + 1

    while i < len(tokens) and tokens[i].type != close_type:
        token = tokens[i]
        if token.type == "text":
            children.append(Text(content=token.content))
        elif token.type == "code_inline":
            children.append(Code(content=token.content))
        i += 1

    consumed = i - start_idx + 1  # Including close token
    return children, consumed


def _parse_link(tokens: list[Token], start_idx: int) -> tuple[AnyInline, int]:
    """Parse link token.

    Recognizes slack:// URLs and converts them to appropriate AST nodes.
    """
    link_open = tokens[start_idx]
    url_attr = link_open.attrGet("href")
    url = str(url_attr) if url_attr is not None else ""

    # Parse link text
    children: list[AnyInline] = []
    i = start_idx + 1
    while i < len(tokens) and tokens[i].type != "link_close":
        token = tokens[i]
        if token.type == "text":
            children.append(Text(content=token.content))
        elif token.type == "code_inline":
            children.append(Code(content=token.content))
        i += 1

    consumed = i - start_idx + 1

    # Check if this is a slack:// URL
    if isinstance(url, str) and url.startswith("slack://"):
        slack_node = _parse_slack_url(url, children)
        if slack_node:
            return slack_node, consumed

    # Regular link
    return Link(url=url, children=children), consumed


def _parse_slack_url(url: str, children: list[AnyInline]) -> AnyInline | None:
    """Parse a slack:// URL into a Slack-specific AST node."""
    parsed = urlparse(url)
    path = parsed.netloc  # In slack://user?id=U123, netloc is "user"
    params = parse_qs(parsed.query)

    if path == "user":
        user_id = params.get("id", [""])[0]
        username = params.get("name", [None])[0]
        return UserMention(user_id=user_id, username=username)
    elif path == "channel":
        channel_id = params.get("id", [""])[0]
        channel_name = params.get("name", [None])[0]
        return ChannelMention(channel_id=channel_id, channel_name=channel_name)
    elif path == "usergroup":
        usergroup_id = params.get("id", [""])[0]
        usergroup_name = params.get("name", [None])[0]
        return UsergroupMention(usergroup_id=usergroup_id, usergroup_name=usergroup_name)
    elif path == "broadcast":
        broadcast_type = params.get("type", ["here"])[0]
        return Broadcast(type=broadcast_type)
    elif path == "date":
        timestamp = int(params.get("ts", ["0"])[0])
        date_format = params.get("format", [None])[0]
        # Extract fallback from children text
        fallback = "".join(child.content for child in children if isinstance(child, Text))
        return DateTimestamp(timestamp=timestamp, format=date_format, fallback=fallback or None)

    return None


def _find_closing_token(
    tokens: list[Token], start_idx: int, open_type: str, close_type: str
) -> int:
    """Find the index of the matching closing token."""
    depth = 1
    i = start_idx + 1

    while i < len(tokens) and depth > 0:
        if tokens[i].type == open_type:
            depth += 1
        elif tokens[i].type == close_type:
            depth -= 1
        i += 1

    return i - 1  # Index of closing token
