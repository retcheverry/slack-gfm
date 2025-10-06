"""Parser for Slack mrkdwn format.

Converts Slack mrkdwn string to AST.
"""

import re

from ..ast import (
    AnyBlock,
    AnyInline,
    Bold,
    Broadcast,
    ChannelMention,
    Code,
    CodeBlock,
    Document,
    Italic,
    Link,
    Paragraph,
    Quote,
    Strikethrough,
    Text,
    UserMention,
)


def parse_mrkdwn(mrkdwn_text: str) -> Document:
    """Parse Slack mrkdwn format to AST.

    Args:
        mrkdwn_text: Slack mrkdwn string

    Returns:
        Document AST node

    Example:
        >>> mrkdwn = "*Hello* _world_"
        >>> doc = parse_mrkdwn(mrkdwn)
    """
    # Split into blocks by double newline or special block markers
    blocks = _split_into_blocks(mrkdwn_text)
    parsed_blocks = [_parse_block(block) for block in blocks]
    return Document(children=parsed_blocks)


def _split_into_blocks(text: str) -> list[str]:
    """Split text into block-level chunks."""
    # Split by blank lines
    blocks = []
    current_block: list[str] = []
    lines = text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for code block
        if line.startswith("```"):
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []

            # Collect code block
            code_lines = [line]
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                code_lines.append(lines[i])  # Closing ```
            blocks.append("\n".join(code_lines))
            i += 1
            continue

        # Check for quote block
        if line.startswith(">"):
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []

            # Collect quote lines
            quote_lines = []
            while i < len(lines) and lines[i].startswith(">"):
                quote_lines.append(lines[i])
                i += 1
            blocks.append("\n".join(quote_lines))
            continue

        # Regular line
        if line.strip():
            current_block.append(line)
        else:
            # Empty line - end current block
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []

        i += 1

    # Add remaining block
    if current_block:
        blocks.append("\n".join(current_block))

    return blocks


def _parse_block(block_text: str) -> AnyBlock:
    """Parse a block of text."""
    # Check for code block
    if block_text.startswith("```"):
        return _parse_code_block(block_text)

    # Check for quote
    if block_text.startswith(">"):
        return _parse_quote_block(block_text)

    # Otherwise, treat as paragraph
    return _parse_paragraph_block(block_text)


def _parse_code_block(block_text: str) -> CodeBlock:
    """Parse a code block."""
    lines = block_text.split("\n")
    # First line is ```language
    first_line = lines[0][3:].strip()  # Remove ```
    language = first_line if first_line else None

    # Content is everything between ``` markers
    if len(lines) > 2 and lines[-1].startswith("```"):
        content = "\n".join(lines[1:-1])
    else:
        content = "\n".join(lines[1:])

    return CodeBlock(content=content, language=language)


def _parse_quote_block(block_text: str) -> Quote:
    """Parse a quote block."""
    lines = block_text.split("\n")
    # Remove > prefix from each line
    content_lines = [line[1:].strip() if line.startswith(">") else line for line in lines]
    content = "\n".join(content_lines)

    # Parse content as inline elements
    inlines = _parse_inline(content)
    return Quote(children=[Paragraph(children=inlines)])


def _parse_paragraph_block(block_text: str) -> Paragraph:
    """Parse a paragraph block."""
    inlines = _parse_inline(block_text)
    return Paragraph(children=inlines)


def _parse_inline(text: str) -> list[AnyInline]:
    """Parse inline content using regex tokenization."""
    tokens = _tokenize_inline(text)
    return _tokens_to_inlines(tokens)


def _tokenize_inline(text: str) -> list[tuple[str, str]]:
    """Tokenize inline text into (type, content) tuples."""
    tokens: list[tuple[str, str]] = []

    # Patterns for mrkdwn inline elements
    patterns = [
        # Code (must come before other patterns)
        (r"`([^`]+)`", "code"),
        # Links: <url|text> or <url>
        (r"<(https?://[^|>]+)\|([^>]+)>", "link_with_text"),
        (r"<(https?://[^>]+)>", "link"),
        # User mention: <@U123|username> or <@U123>
        (r"<@([A-Z0-9]+)\|([^>]+)>", "user_with_name"),
        (r"<@([A-Z0-9]+)>", "user"),
        # Channel: <#C123|channel> or <#C123>
        (r"<#([A-Z0-9]+)\|([^>]+)>", "channel_with_name"),
        (r"<#([A-Z0-9]+)>", "channel"),
        # Broadcast: <!here>, <!channel>, <!everyone>
        (r"<!(here|channel|everyone)>", "broadcast"),
        # Bold: *text*
        (r"\*([^\*]+)\*", "bold"),
        # Italic: _text_
        (r"_([^_]+)_", "italic"),
        # Strikethrough: ~text~
        (r"~([^~]+)~", "strike"),
    ]

    pos = 0
    while pos < len(text):
        matched = False

        for pattern, token_type in patterns:
            regex = re.compile(pattern)
            match = regex.match(text, pos)
            if match:
                tokens.append((token_type, match.group(0)))
                pos = match.end()
                matched = True
                break

        if not matched:
            # Plain text - find next special character
            next_special = len(text)
            for pattern, _ in patterns:
                regex = re.compile(pattern)
                match = regex.search(text, pos)
                if match:
                    next_special = min(next_special, match.start())

            if next_special > pos:
                tokens.append(("text", text[pos:next_special]))
                pos = next_special
            else:
                # Single character
                tokens.append(("text", text[pos]))
                pos += 1

    return tokens


def _tokens_to_inlines(tokens: list[tuple[str, str]]) -> list[AnyInline]:
    """Convert tokens to AST inline nodes."""
    inlines: list[AnyInline] = []

    for token_type, content in tokens:
        if token_type == "text":
            if content:  # Skip empty text
                inlines.append(Text(content=content))

        elif token_type == "code":
            # Extract content from backticks
            match = re.match(r"`([^`]+)`", content)
            if match:
                inlines.append(Code(content=match.group(1)))

        elif token_type == "link":
            # <url>
            match = re.match(r"<([^>]+)>", content)
            if match:
                url = match.group(1)
                inlines.append(Link(url=url, children=[]))

        elif token_type == "link_with_text":
            # <url|text>
            match = re.match(r"<([^|>]+)\|([^>]+)>", content)
            if match:
                url = match.group(1)
                link_text = match.group(2)
                inlines.append(Link(url=url, children=[Text(content=link_text)]))

        elif token_type == "user":
            # <@U123>
            match = re.match(r"<@([A-Z0-9]+)>", content)
            if match:
                user_id = match.group(1)
                inlines.append(UserMention(user_id=user_id))

        elif token_type == "user_with_name":
            # <@U123|username>
            match = re.match(r"<@([A-Z0-9]+)\|([^>]+)>", content)
            if match:
                user_id = match.group(1)
                username = match.group(2)
                inlines.append(UserMention(user_id=user_id, username=username))

        elif token_type == "channel":
            # <#C123>
            match = re.match(r"<#([A-Z0-9]+)>", content)
            if match:
                channel_id = match.group(1)
                inlines.append(ChannelMention(channel_id=channel_id))

        elif token_type == "channel_with_name":
            # <#C123|channel>
            match = re.match(r"<#([A-Z0-9]+)\|([^>]+)>", content)
            if match:
                channel_id = match.group(1)
                channel_name = match.group(2)
                inlines.append(ChannelMention(channel_id=channel_id, channel_name=channel_name))

        elif token_type == "broadcast":
            # <!here>, <!channel>, <!everyone>
            match = re.match(r"<!(here|channel|everyone)>", content)
            if match:
                broadcast_type = match.group(1)
                inlines.append(Broadcast(type=broadcast_type))

        elif token_type == "bold":
            # *text*
            match = re.match(r"\*([^\*]+)\*", content)
            if match:
                text_content = match.group(1)
                inlines.append(Bold(children=[Text(content=text_content)]))

        elif token_type == "italic":
            # _text_
            match = re.match(r"_([^_]+)_", content)
            if match:
                text_content = match.group(1)
                inlines.append(Italic(children=[Text(content=text_content)]))

        elif token_type == "strike":
            # ~text~
            match = re.match(r"~([^~]+)~", content)
            if match:
                text_content = match.group(1)
                inlines.append(Strikethrough(children=[Text(content=text_content)]))

    return inlines
