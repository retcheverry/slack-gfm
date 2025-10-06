"""AST node definitions for slack-gfm.

This module defines the Abstract Syntax Tree (AST) nodes used to represent
formatted text from Slack (Mrkdwn, Rich Text) and GitHub Flavored Markdown.
"""

from dataclasses import dataclass, field

# Base classes


@dataclass
class Node:
    """Base class for all AST nodes."""

    pass


@dataclass
class InlineNode(Node):
    """Base class for inline-level nodes (can appear within a paragraph)."""

    pass


@dataclass
class BlockNode(Node):
    """Base class for block-level nodes (standalone blocks like paragraphs, lists, quotes)."""

    pass


# Document structure


@dataclass
class Document(Node):
    """Root node containing all content blocks."""

    children: list[BlockNode] = field(default_factory=list)


# Inline nodes


@dataclass
class Text(InlineNode):
    """Plain text node."""

    content: str


@dataclass
class Bold(InlineNode):
    """Bold text."""

    children: list[InlineNode] = field(default_factory=list)


@dataclass
class Italic(InlineNode):
    """Italic text."""

    children: list[InlineNode] = field(default_factory=list)


@dataclass
class Strikethrough(InlineNode):
    """Strikethrough text."""

    children: list[InlineNode] = field(default_factory=list)


@dataclass
class Code(InlineNode):
    """Inline code."""

    content: str


@dataclass
class Link(InlineNode):
    """Hyperlink with optional text content."""

    url: str
    children: list[InlineNode] = field(default_factory=list)  # Link text


@dataclass
class UserMention(InlineNode):
    """Slack user mention.

    Attributes:
        user_id: Slack user ID (e.g., "U123ABC")
        username: Optional display name for the user
    """

    user_id: str
    username: str | None = None


@dataclass
class ChannelMention(InlineNode):
    """Slack channel mention.

    Attributes:
        channel_id: Slack channel ID (e.g., "C123ABC")
        channel_name: Optional display name for the channel
    """

    channel_id: str
    channel_name: str | None = None


@dataclass
class UsergroupMention(InlineNode):
    """Slack usergroup mention.

    Attributes:
        usergroup_id: Slack usergroup ID (e.g., "S123ABC")
        usergroup_name: Optional display name for the usergroup
    """

    usergroup_id: str
    usergroup_name: str | None = None


@dataclass
class Broadcast(InlineNode):
    """Slack broadcast notification.

    Attributes:
        type: Type of broadcast ("here", "channel", "everyone")
    """

    type: str  # "here", "channel", "everyone"


@dataclass
class Emoji(InlineNode):
    """Emoji.

    Attributes:
        name: Emoji name (e.g., "smile", "thumbsup")
        unicode: Optional unicode representation
    """

    name: str
    unicode: str | None = None


@dataclass
class DateTimestamp(InlineNode):
    """Slack date/time formatting.

    Attributes:
        timestamp: Unix timestamp
        format: Optional format string
        fallback: Fallback text if formatting fails
    """

    timestamp: int
    format: str | None = None
    fallback: str | None = None


# Block nodes


@dataclass
class Paragraph(BlockNode):
    """Paragraph containing inline content."""

    children: list[InlineNode] = field(default_factory=list)


@dataclass
class Heading(BlockNode):
    """Heading with level (1-6)."""

    level: int  # 1-6
    children: list[InlineNode] = field(default_factory=list)


@dataclass
class CodeBlock(BlockNode):
    """Code block with optional language."""

    content: str
    language: str | None = None


@dataclass
class Quote(BlockNode):
    """Block quote."""

    children: list[BlockNode] = field(default_factory=list)


@dataclass
class List(BlockNode):
    """List (ordered or unordered).

    Attributes:
        ordered: True for ordered list, False for unordered
        start: Starting number for ordered lists (default 1)
        children: List items
    """

    ordered: bool
    children: list["ListItem"] = field(default_factory=list)
    start: int = 1


@dataclass
class ListItem(Node):
    """List item.

    Can contain inline content or nested blocks.
    """

    children: list[InlineNode | BlockNode] = field(default_factory=list)


@dataclass
class HorizontalRule(BlockNode):
    """Horizontal rule / divider."""

    pass


@dataclass
class Table(BlockNode):
    """Table (GFM extension).

    Attributes:
        header: Header row
        rows: Data rows
        alignments: Column alignments ("left", "center", "right", None)
    """

    header: list[list[InlineNode]] = field(default_factory=list)
    rows: list[list[list[InlineNode]]] = field(default_factory=list)
    alignments: list[str | None] = field(default_factory=list)


# Type aliases for convenience

AnyNode = Node | InlineNode | BlockNode
AnyInline = (
    InlineNode
    | Text
    | Bold
    | Italic
    | Strikethrough
    | Code
    | Link
    | UserMention
    | ChannelMention
    | UsergroupMention
    | Broadcast
    | Emoji
    | DateTimestamp
)
AnyBlock = BlockNode | Paragraph | Heading | CodeBlock | Quote | List | HorizontalRule | Table
