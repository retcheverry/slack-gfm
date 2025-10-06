"""Renderer for GitHub Flavored Markdown (GFM).

Converts AST to GFM string format.
"""

from urllib.parse import urlencode

from ..ast import (
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
    HorizontalRule,
    Italic,
    Link,
    List,
    ListItem,
    Paragraph,
    Quote,
    Strikethrough,
    Table,
    Text,
    UsergroupMention,
    UserMention,
)


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
    return _render_node(node)


def _render_node(node: AnyNode) -> str:
    """Dispatch rendering to appropriate handler."""
    if isinstance(node, Document):
        return _render_document(node)
    elif isinstance(node, Paragraph):
        return _render_paragraph(node)
    elif isinstance(node, Heading):
        return _render_heading(node)
    elif isinstance(node, CodeBlock):
        return _render_codeblock(node)
    elif isinstance(node, Quote):
        return _render_quote(node)
    elif isinstance(node, List):
        return _render_list(node)
    elif isinstance(node, ListItem):
        return _render_listitem(node)
    elif isinstance(node, HorizontalRule):
        return _render_horizontal_rule()
    elif isinstance(node, Table):
        return _render_table(node)
    elif isinstance(node, Text):
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
        return ""


# Block renderers


def _render_document(doc: Document) -> str:
    """Render Document node."""
    blocks = [_render_node(child) for child in doc.children]
    # Join blocks with double newline
    return "\n\n".join(block for block in blocks if block)


def _render_paragraph(para: Paragraph) -> str:
    """Render Paragraph node."""
    return "".join(_render_node(child) for child in para.children)


def _render_heading(heading: Heading) -> str:
    """Render Heading node."""
    level = max(1, min(6, heading.level))  # Clamp to 1-6
    prefix = "#" * level + " "
    content = "".join(_render_node(child) for child in heading.children)
    return prefix + content


def _render_codeblock(codeblock: CodeBlock) -> str:
    """Render CodeBlock node."""
    lang = codeblock.language or ""
    return f"```{lang}\n{codeblock.content}\n```"


def _render_quote(quote: Quote) -> str:
    """Render Quote node."""
    # Render children and prefix each line with >
    content_parts = []
    for child in quote.children:
        child_content = _render_node(child)
        lines = child_content.split("\n")
        quoted_lines = [f"> {line}" if line else ">" for line in lines]
        content_parts.append("\n".join(quoted_lines))
    return "\n".join(content_parts)


def _render_list(list_node: List) -> str:
    """Render List node."""
    items = []
    for i, item in enumerate(list_node.children):
        if list_node.ordered:
            num = list_node.start + i
            prefix = f"{num}. "
        else:
            prefix = "- "

        item_content = _render_listitem_content(item)
        # Handle multiline items
        lines = item_content.split("\n")
        if lines:
            items.append(prefix + lines[0])
            # Indent continuation lines
            for line in lines[1:]:
                items.append("  " + line)

    return "\n".join(items)


def _render_listitem(item: ListItem) -> str:
    """Render ListItem node (used by _render_list)."""
    return _render_listitem_content(item)


def _render_listitem_content(item: ListItem) -> str:
    """Render ListItem content."""
    return "".join(_render_node(child) for child in item.children)


def _render_horizontal_rule() -> str:
    """Render HorizontalRule node."""
    return "---"


def _render_table(table: Table) -> str:
    """Render Table node."""
    lines = []

    # Header row
    if table.header:
        header_cells = [
            "".join(_render_node(cell) for cell in row) for row in table.header
        ]
        lines.append("| " + " | ".join(header_cells) + " |")

        # Separator row with alignments
        sep_cells = []
        for align in table.alignments:
            if align == "left":
                sep_cells.append(":---")
            elif align == "right":
                sep_cells.append("---:")
            elif align == "center":
                sep_cells.append(":---:")
            else:
                sep_cells.append("---")
        lines.append("| " + " | ".join(sep_cells) + " |")

    # Data rows
    for row in table.rows:
        row_cells = [
            "".join(_render_node(cell) for cell in row_cells) for row_cells in row
        ]
        lines.append("| " + " | ".join(row_cells) + " |")

    return "\n".join(lines)


# Inline renderers


def _render_text(text: Text) -> str:
    """Render Text node."""
    # Escape special markdown characters
    content = text.content
    # Escape backslashes first
    content = content.replace("\\", "\\\\")
    # Escape markdown special chars
    for char in ["*", "_", "`", "[", "]", "(", ")", "#", "+", "-", ".", "!", "|"]:
        content = content.replace(char, f"\\{char}")
    return content


def _render_bold(bold: Bold) -> str:
    """Render Bold node."""
    content = "".join(_render_node(child) for child in bold.children)
    return f"**{content}**"


def _render_italic(italic: Italic) -> str:
    """Render Italic node."""
    content = "".join(_render_node(child) for child in italic.children)
    return f"*{content}*"


def _render_strikethrough(strike: Strikethrough) -> str:
    """Render Strikethrough node."""
    content = "".join(_render_node(child) for child in strike.children)
    return f"~~{content}~~"


def _render_code(code: Code) -> str:
    """Render inline Code node."""
    # Escape backticks in code content
    content = code.content.replace("`", "\\`")
    return f"`{content}`"


def _render_link(link: Link) -> str:
    """Render Link node."""
    text = "".join(_render_node(child) for child in link.children) if link.children else link.url
    # Escape special chars in URL
    url = link.url.replace("(", "%28").replace(")", "%29")
    return f"[{text}]({url})"


def _render_user_mention(mention: UserMention) -> str:
    """Render UserMention as GFM link with slack:// URL."""
    display = f"@{mention.username}" if mention.username else mention.user_id
    params = {"id": mention.user_id}
    if mention.username:
        params["name"] = mention.username
    url = f"slack://user?{urlencode(params)}"
    return f"[{display}]({url})"


def _render_channel_mention(mention: ChannelMention) -> str:
    """Render ChannelMention as GFM link with slack:// URL."""
    display = f"#{mention.channel_name}" if mention.channel_name else mention.channel_id
    params = {"id": mention.channel_id}
    if mention.channel_name:
        params["name"] = mention.channel_name
    url = f"slack://channel?{urlencode(params)}"
    return f"[{display}]({url})"


def _render_usergroup_mention(mention: UsergroupMention) -> str:
    """Render UsergroupMention as GFM link with slack:// URL."""
    display = (
        f"@{mention.usergroup_name}" if mention.usergroup_name else mention.usergroup_id
    )
    params = {"id": mention.usergroup_id}
    if mention.usergroup_name:
        params["name"] = mention.usergroup_name
    url = f"slack://usergroup?{urlencode(params)}"
    return f"[{display}]({url})"


def _render_broadcast(broadcast: Broadcast) -> str:
    """Render Broadcast as GFM link with slack:// URL."""
    display = f"@{broadcast.type}"
    url = f"slack://broadcast?type={broadcast.type}"
    return f"[{display}]({url})"


def _render_emoji(emoji: Emoji) -> str:
    """Render Emoji."""
    if emoji.unicode:
        return emoji.unicode
    else:
        return f":{emoji.name}:"


def _render_date(date: DateTimestamp) -> str:
    """Render DateTimestamp as GFM link with slack:// URL."""
    display = date.fallback or str(date.timestamp)
    params = {"ts": str(date.timestamp)}
    if date.format:
        params["format"] = date.format
    url = f"slack://date?{urlencode(params)}"
    return f"[{display}]({url})"
