"""Parser for Slack mrkdwn format.

Converts Slack mrkdwn string to AST using a state machine tokenizer.
"""

from dataclasses import dataclass
from enum import Enum, auto

from ..ast import (
    AnyBlock,
    AnyInline,
    BlockNode,
    Bold,
    Broadcast,
    ChannelMention,
    Code,
    CodeBlock,
    Document,
    InlineNode,
    Italic,
    Link,
    List,
    ListItem,
    Paragraph,
    Quote,
    Strikethrough,
    Text,
    UserMention,
)


class State(Enum):
    """Tokenizer states for context-aware parsing."""

    OUTSIDE_CODE_BLOCK = auto()
    IN_CODE_BLOCK = auto()


@dataclass
class Token:
    """Token produced by tokenizer."""

    type: str  # Token type: "text", "code_block_start", "bold_marker", etc.
    content: str  # Token content
    pos: int  # Position in input


class MrkdwnTokenizer:
    """State machine tokenizer for Slack mrkdwn format.

    The tokenizer uses a state machine to handle context-dependent parsing rules:
    - OUTSIDE_CODE_BLOCK: Parse formatting markers, links, mentions
    - IN_CODE_BLOCK: Treat everything as literal text except closing ```
    """

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)
        self.state = State.OUTSIDE_CODE_BLOCK
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """Tokenize input into list of tokens."""
        while self.pos < self.length:
            if self.state == State.OUTSIDE_CODE_BLOCK:
                self._tokenize_outside()
            elif self.state == State.IN_CODE_BLOCK:
                self._tokenize_inside()

        return self.tokens

    def _peek(self, n: int = 1) -> str:
        """Peek ahead n characters without advancing position."""
        return self.text[self.pos : self.pos + n]

    def _advance(self, n: int = 1) -> None:
        """Advance position by n characters."""
        self.pos += n

    def _tokenize_outside(self) -> None:
        """Tokenize when outside code blocks.

        Rules:
        - ``` starts code block → transition to IN_CODE_BLOCK
        - <url> → parse as link (strip angle brackets)
        - <@USER> → parse as user mention
        - <#CHANNEL> → parse as channel mention
        - <!broadcast> → parse as broadcast
        - *text* → parse as bold marker
        - _text_ → parse as italic marker
        - ~text~ → parse as strikethrough marker
        - `text` → parse as inline code
        - &gt; at line start → parse as quote marker
        - • at line start → parse as bullet list marker
        - 1., 2., etc. at line start → parse as ordered list marker
        - \n → parse as newline
        """
        at_line_start = self.pos == 0 or self.text[self.pos - 1] == "\n"

        # Check for code block start (```)
        if self._peek(3) == "```":
            self.tokens.append(Token("code_block_start", "```", self.pos))
            self._advance(3)
            self.state = State.IN_CODE_BLOCK
            return

        # Check for inline code (`text`)
        if self._peek() == "`":
            self._parse_inline_code()
            return

        # Check for angle bracket content (<...>)
        if self._peek() == "<":
            self._parse_angle_bracket()
            return

        # Check for bold marker (*)
        if self._peek() == "*":
            self.tokens.append(Token("bold_marker", "*", self.pos))
            self._advance()
            return

        # Check for italic marker (_)
        if self._peek() == "_":
            self.tokens.append(Token("italic_marker", "_", self.pos))
            self._advance()
            return

        # Check for strikethrough marker (~)
        if self._peek() == "~":
            self.tokens.append(Token("strike_marker", "~", self.pos))
            self._advance()
            return

        # Check for quote marker (&gt; at line start)
        if at_line_start and self._peek(4) == "&gt;":
            self.tokens.append(Token("quote_marker", "&gt;", self.pos))
            self._advance(4)
            # Skip optional space after &gt;
            if self._peek() == " ":
                self._advance()
            return

        # Check for bullet list marker (• at line start)
        if at_line_start and self._peek() == "•":
            self.tokens.append(Token("bullet_marker", "•", self.pos))
            self._advance()
            # Skip optional space after bullet
            if self._peek() == " ":
                self._advance()
            return

        # Check for ordered list marker (1., 2., etc. at line start)
        if at_line_start and self._peek().isdigit():
            num_start = self.pos
            # Collect digits
            while self._peek().isdigit():
                self._advance()
            # Check for period and space
            if self._peek() == ".":
                num_text = self.text[num_start : self.pos]
                self.tokens.append(Token("ordered_marker", num_text, num_start))
                self._advance()  # Skip period
                # Skip optional space after period
                if self._peek() == " ":
                    self._advance()
                return
            else:
                # Not a list marker, backtrack
                self.pos = num_start

        # Check for newline
        if self._peek() == "\n":
            self.tokens.append(Token("newline", "\n", self.pos))
            self._advance()
            return

        # Regular text - accumulate until next special character
        self._parse_text_outside()

    def _tokenize_inside(self) -> None:
        """Tokenize when inside code blocks.

        Rules:
        - ``` ends code block → transition to OUTSIDE_CODE_BLOCK
        - <url> → strip angle brackets, treat as literal text
        - Everything else → literal text (no formatting)
        """
        # Check for code block end (```)
        if self._peek(3) == "```":
            self.tokens.append(Token("code_block_end", "```", self.pos))
            self._advance(3)
            self.state = State.OUTSIDE_CODE_BLOCK
            return

        # Check for angle bracket URL and strip
        if self._peek() == "<":
            url = self._try_extract_url()
            if url:
                # Strip angle brackets from URLs in code blocks
                self.tokens.append(Token("text", url, self.pos))
                return

        # Everything else is literal text
        self._parse_text_inside()

    def _parse_inline_code(self) -> None:
        """Parse inline code: `text`."""
        start_pos = self.pos
        self._advance()  # Skip opening backtick

        # Find closing backtick
        end = self.text.find("`", self.pos)
        if end == -1:
            # No closing backtick - treat as literal text
            self.tokens.append(Token("text", "`", start_pos))
            return

        content = self.text[self.pos : end]
        self.tokens.append(Token("inline_code", content, start_pos))
        self.pos = end + 1  # Skip closing backtick

    def _parse_angle_bracket(self) -> None:
        """Parse content between < > based on context.

        Patterns:
        - <http://url> or <http://url|text> → link
        - <@USER_ID> or <@USER_ID|name> → user mention
        - <#CHANNEL_ID> or <#CHANNEL_ID|name> → channel mention
        - <!here> or <!channel> or <!everyone> → broadcast
        """
        start_pos = self.pos
        end = self.text.find(">", self.pos)
        if end == -1:
            # No closing bracket - treat as literal text
            self.tokens.append(Token("text", "<", start_pos))
            self._advance()
            return

        content = self.text[self.pos + 1 : end]

        # Check for URL (http:// or https://)
        if content.startswith("http://") or content.startswith("https://"):
            self.tokens.append(Token("link", content, start_pos))
            self.pos = end + 1
            return

        # Check for user mention (@)
        if content.startswith("@"):
            self.tokens.append(Token("user_mention", content[1:], start_pos))
            self.pos = end + 1
            return

        # Check for channel mention (#)
        if content.startswith("#"):
            self.tokens.append(Token("channel_mention", content[1:], start_pos))
            self.pos = end + 1
            return

        # Check for broadcast (!)
        if content.startswith("!"):
            self.tokens.append(Token("broadcast", content[1:], start_pos))
            self.pos = end + 1
            return

        # Not a special pattern - treat as literal text
        self.tokens.append(Token("text", self.text[start_pos : end + 1], start_pos))
        self.pos = end + 1

    def _try_extract_url(self) -> str | None:
        """Try to extract URL from <url> if present.

        Returns URL without brackets, or None if not a URL.
        """
        end = self.text.find(">", self.pos)
        if end == -1:
            return None

        content = self.text[self.pos + 1 : end]

        # Check if it looks like a URL
        if content.startswith("http://") or content.startswith("https://"):
            self.pos = end + 1
            return content  # Return URL without brackets

        return None

    def _parse_text_outside(self) -> None:
        """Parse regular text when outside code blocks.

        Accumulate characters until next special character.
        """
        start_pos = self.pos
        text_chars = []

        while self.pos < self.length:
            char = self._peek()

            # Stop at special characters
            if char in ("*", "_", "~", "`", "<", "\n"):
                break

            # Stop at ``` (code block start)
            if self._peek(3) == "```":
                break

            # Note: We don't check for > here anymore, since Slack mrkdwn uses &gt;
            # which is checked in the main tokenizer. Plain > is treated as regular text.

            text_chars.append(char)
            self._advance()

        if text_chars:
            self.tokens.append(Token("text", "".join(text_chars), start_pos))

    def _parse_text_inside(self) -> None:
        """Parse literal text when inside code blocks.

        Accumulate characters until ``` or <url>.
        """
        start_pos = self.pos
        text_chars = []

        while self.pos < self.length:
            # Stop at code block end
            if self._peek(3) == "```":
                break

            # Stop at potential URL
            if self._peek() == "<":
                # Check if this is a URL that should be stripped
                end = self.text.find(">", self.pos)
                if end != -1:
                    content = self.text[self.pos + 1 : end]
                    if content.startswith("http://") or content.startswith("https://"):
                        break

            text_chars.append(self._peek())
            self._advance()

        if text_chars:
            self.tokens.append(Token("text", "".join(text_chars), start_pos))


# Parser: Build AST from tokens


def parse_mrkdwn(mrkdwn_text: str) -> Document:
    """Parse Slack mrkdwn format to AST.

    Uses a state machine tokenizer for context-aware parsing.

    Args:
        mrkdwn_text: Slack mrkdwn string

    Returns:
        Document AST node

    Example:
        >>> mrkdwn = "*Hello* _world_"
        >>> doc = parse_mrkdwn(mrkdwn)
    """
    tokenizer = MrkdwnTokenizer(mrkdwn_text)
    tokens = tokenizer.tokenize()
    return _parse_tokens_to_ast(tokens)


def _parse_tokens_to_ast(tokens: list[Token]) -> Document:
    """Build AST from tokens."""

    blocks: list[AnyBlock] = []
    i = 0

    while i < len(tokens):
        # Check for code block
        if tokens[i].type == "code_block_start":
            block, consumed = _parse_code_block_tokens(tokens, i)
            blocks.append(block)
            i += consumed
            continue

        # Check for quote
        if tokens[i].type == "quote_marker":
            quote_block, consumed = _parse_quote_tokens(tokens, i)
            blocks.append(quote_block)
            i += consumed
            continue

        # Check for bullet list
        if tokens[i].type == "bullet_marker":
            list_block, consumed = _parse_list_tokens(tokens, i, ordered=False)
            blocks.append(list_block)
            i += consumed
            continue

        # Check for ordered list
        if tokens[i].type == "ordered_marker":
            list_block, consumed = _parse_list_tokens(tokens, i, ordered=True)
            blocks.append(list_block)
            i += consumed
            continue

        # Check for paragraph (text or formatting)
        para_block, consumed = _parse_paragraph_tokens(tokens, i)
        if para_block:
            blocks.append(para_block)
        i += consumed

    return Document(children=blocks)


def _parse_code_block_tokens(tokens: list[Token], start: int) -> tuple[CodeBlock, int]:
    """Parse code block from tokens.

    Handles:
    - Inline code blocks: ```xyz```
    - Multiline with content on opening line: ```xyz\n```
    - Multiline with newline after opening: ```\nxyz\n```
    """
    assert tokens[start].type == "code_block_start"
    i = start + 1

    # Collect content tokens until code_block_end
    content_parts = []
    language = None
    found_end = False

    while i < len(tokens):
        if tokens[i].type == "code_block_end":
            found_end = True
            break

        if tokens[i].type == "text":
            content_parts.append(tokens[i].content)
        elif tokens[i].type == "newline":
            content_parts.append("\n")

        i += 1

    # Join content
    content = "".join(content_parts)

    # Check if first line is language identifier (no spaces, alphanumeric)
    lines = content.split("\n", 1)
    if len(lines) >= 2 and lines[0] and lines[0].isalnum():
        language = lines[0]
        content = lines[1] if len(lines) > 1 else ""

    # Preserve trailing newlines for mrkdwn round-trip consistency
    # (GFM parser strips them, but mrkdwn parser preserves structure)

    consumed = i - start + (1 if found_end else 0)
    return CodeBlock(content=content, language=language), consumed


def _parse_quote_tokens(tokens: list[Token], start: int) -> tuple[Quote, int]:
    """Parse quote from tokens."""
    assert tokens[start].type == "quote_marker"
    i = start + 1

    # Collect tokens until double newline or different block type
    inline_tokens = []
    while i < len(tokens):
        if tokens[i].type == "quote_marker":
            # Another quote line - skip the marker
            i += 1
            continue

        if tokens[i].type == "newline":
            # Check for double newline (end of quote)
            if i + 1 < len(tokens) and tokens[i + 1].type == "newline":
                i += 2
                break
            # Check if next line has quote marker - if not, end quote
            if i + 1 < len(tokens) and tokens[i + 1].type != "quote_marker":
                i += 1
                break
            # Single newline within quote - preserve it as literal newline
            # The GFM visitor will add > prefix to each line
            inline_tokens.append(Token("text", "\n", tokens[i].pos))
            i += 1
            continue

        if tokens[i].type == "code_block_start":
            # Different block type - end quote
            break

        inline_tokens.append(tokens[i])
        i += 1

    # Parse inline content
    inlines = _parse_inline_tokens(inline_tokens)
    para = Paragraph(children=inlines)
    consumed = i - start
    return Quote(children=[para]), consumed


def _parse_list_tokens(tokens: list[Token], start: int, ordered: bool) -> tuple[List, int]:
    """Parse list from tokens.

    Lists are identified by:
    - Bullet lists: lines starting with •
    - Ordered lists: lines starting with 1., 2., etc.

    Each list item continues until a newline, then the next marker starts a new item.
    """
    marker_type = "ordered_marker" if ordered else "bullet_marker"
    i = start
    list_items: list[ListItem] = []
    start_num = 1

    # Extract starting number for ordered lists
    if ordered and tokens[i].type == "ordered_marker":
        start_num = int(tokens[i].content)

    while i < len(tokens):
        # Check if this is a list marker
        if tokens[i].type != marker_type:
            break

        # Skip the marker
        i += 1

        # Collect tokens for this list item until newline
        item_tokens = []
        while i < len(tokens):
            if tokens[i].type == "newline":
                i += 1
                break
            item_tokens.append(tokens[i])
            i += 1

        # Parse item content
        if item_tokens:
            from typing import cast

            inlines = _parse_inline_tokens(item_tokens)
            # Cast to the expected type - AnyInline items are also InlineNode
            list_items.append(ListItem(children=cast(list[InlineNode | BlockNode], inlines)))

    consumed = i - start
    return List(children=list_items, ordered=ordered, start=start_num), consumed


def _parse_paragraph_tokens(tokens: list[Token], start: int) -> tuple[Paragraph | None, int]:
    """Parse paragraph from tokens."""
    # Collect tokens until double newline or block marker
    inline_tokens = []
    i = start

    while i < len(tokens):
        if tokens[i].type in (
            "code_block_start",
            "quote_marker",
            "bullet_marker",
            "ordered_marker",
        ):
            # Different block type
            break

        if tokens[i].type == "newline":
            # Check for double newline (end of paragraph)
            if i + 1 < len(tokens) and tokens[i + 1].type == "newline":
                i += 2
                break
            # Check if this is the last token (trailing newline)
            if i + 1 >= len(tokens):
                i += 1
                break
            # Check if next token is a block boundary (list, quote, code block)
            if i + 1 < len(tokens) and tokens[i + 1].type in (
                "bullet_marker",
                "ordered_marker",
                "quote_marker",
                "code_block_start",
            ):
                i += 1
                break
            # Single newline - convert to space
            inline_tokens.append(Token("text", " ", tokens[i].pos))
            i += 1
            continue

        inline_tokens.append(tokens[i])
        i += 1

    if not inline_tokens:
        return None, i - start

    inlines = _parse_inline_tokens(inline_tokens)
    consumed = i - start
    return Paragraph(children=inlines), consumed


def _parse_inline_tokens(tokens: list[Token]) -> list[AnyInline]:
    """Parse inline tokens into AST nodes."""
    inlines: list[AnyInline] = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if token.type == "text":
            if token.content:  # Skip empty text
                inlines.append(Text(content=token.content))
            i += 1

        elif token.type == "inline_code":
            inlines.append(Code(content=token.content))
            i += 1

        elif token.type == "link":
            # Parse link: url or url|text
            if "|" in token.content:
                url, link_text = token.content.split("|", 1)
                inlines.append(Link(url=url, children=[Text(content=link_text)]))
            else:
                inlines.append(Link(url=token.content, children=[]))
            i += 1

        elif token.type == "user_mention":
            # Parse user mention: USER_ID or USER_ID|name
            if "|" in token.content:
                user_id, username = token.content.split("|", 1)
                inlines.append(UserMention(user_id=user_id, username=username))
            else:
                inlines.append(UserMention(user_id=token.content))
            i += 1

        elif token.type == "channel_mention":
            # Parse channel mention: CHANNEL_ID or CHANNEL_ID|name
            if "|" in token.content:
                channel_id, channel_name = token.content.split("|", 1)
                inlines.append(ChannelMention(channel_id=channel_id, channel_name=channel_name))
            else:
                inlines.append(ChannelMention(channel_id=token.content))
            i += 1

        elif token.type == "broadcast":
            # Parse broadcast: here, channel, or everyone
            inlines.append(Broadcast(range=token.content))
            i += 1

        elif token.type == "bold_marker":
            # Find matching closing marker
            closing = _find_closing_marker(tokens, i + 1, "bold_marker")
            if closing != -1:
                # Parse content between markers
                inner_tokens = tokens[i + 1 : closing]
                inner_inlines = _parse_inline_tokens(inner_tokens)
                inlines.append(Bold(children=inner_inlines))
                i = closing + 1
            else:
                # No closing marker - treat as literal text
                inlines.append(Text(content="*"))
                i += 1

        elif token.type == "italic_marker":
            # Find matching closing marker
            closing = _find_closing_marker(tokens, i + 1, "italic_marker")
            if closing != -1:
                inner_tokens = tokens[i + 1 : closing]
                inner_inlines = _parse_inline_tokens(inner_tokens)
                inlines.append(Italic(children=inner_inlines))
                i = closing + 1
            else:
                inlines.append(Text(content="_"))
                i += 1

        elif token.type == "strike_marker":
            # Find matching closing marker
            closing = _find_closing_marker(tokens, i + 1, "strike_marker")
            if closing != -1:
                inner_tokens = tokens[i + 1 : closing]
                inner_inlines = _parse_inline_tokens(inner_tokens)
                inlines.append(Strikethrough(children=inner_inlines))
                i = closing + 1
            else:
                inlines.append(Text(content="~"))
                i += 1

        else:
            # Unknown token type - skip
            i += 1

    return inlines


def _find_closing_marker(tokens: list[Token], start: int, marker_type: str) -> int:
    """Find the index of the closing marker.

    Returns -1 if not found.
    """
    for i in range(start, len(tokens)):
        if tokens[i].type == marker_type:
            return i
    return -1
