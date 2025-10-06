"""AST (Abstract Syntax Tree) module for slack-gfm.

This module provides the AST node definitions and visitor pattern
for transforming between Slack and GitHub Flavored Markdown formats.
"""

from .nodes import (
    AnyBlock,
    AnyInline,
    AnyNode,
    BlockNode,
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
    InlineNode,
    Italic,
    Link,
    List,
    ListItem,
    Node,
    Paragraph,
    Quote,
    Strikethrough,
    Table,
    Text,
    UsergroupMention,
    UserMention,
)
from .visitor import NodeVisitor, transform_ast

__all__ = [
    # Base classes
    "Node",
    "InlineNode",
    "BlockNode",
    # Document
    "Document",
    # Inline nodes
    "Text",
    "Bold",
    "Italic",
    "Strikethrough",
    "Code",
    "Link",
    "UserMention",
    "ChannelMention",
    "UsergroupMention",
    "Broadcast",
    "Emoji",
    "DateTimestamp",
    # Block nodes
    "Paragraph",
    "Heading",
    "CodeBlock",
    "Quote",
    "List",
    "ListItem",
    "HorizontalRule",
    "Table",
    # Type aliases
    "AnyNode",
    "AnyInline",
    "AnyBlock",
    # Visitor pattern
    "NodeVisitor",
    "transform_ast",
]
