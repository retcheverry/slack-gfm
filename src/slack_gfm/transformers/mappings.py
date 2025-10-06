"""Transformers for mapping Slack IDs to names.

Provides convenient mapping transformers for common use cases.
"""

from collections.abc import Callable
from typing import Any

from ..ast import (
    ChannelMention,
    UsergroupMention,
    UserMention,
)
from ..ast.visitor import NodeVisitor


class IDMapper(NodeVisitor):
    """Visitor that maps Slack IDs to display names.

    Args:
        user_map: Dictionary mapping user IDs to usernames
        channel_map: Dictionary mapping channel IDs to channel names
        usergroup_map: Dictionary mapping usergroup IDs to usergroup names

    Example:
        >>> from slack_gfm.ast import Document, Paragraph, UserMention
        >>> from slack_gfm.ast.visitor import transform_ast
        >>> from slack_gfm.transformers import IDMapper
        >>>
        >>> doc = Document(children=[
        ...     Paragraph(children=[UserMention(user_id="U123")])
        ... ])
        >>>
        >>> mapper = IDMapper(user_map={"U123": "john"})
        >>> transformed = transform_ast(doc, mapper)
        >>> transformed.children[0].children[0].username
        'john'
    """

    def __init__(
        self,
        user_map: dict[str, str] | None = None,
        channel_map: dict[str, str] | None = None,
        usergroup_map: dict[str, str] | None = None,
    ):
        self.user_map = user_map or {}
        self.channel_map = channel_map or {}
        self.usergroup_map = usergroup_map or {}

    def visit_usermention(self, node: UserMention) -> UserMention:
        """Map user ID to username."""
        if node.user_id in self.user_map:
            node.username = self.user_map[node.user_id]
        return node

    def visit_channelmention(self, node: ChannelMention) -> ChannelMention:
        """Map channel ID to channel name."""
        if node.channel_id in self.channel_map:
            node.channel_name = self.channel_map[node.channel_id]
        return node

    def visit_usergroupmention(self, node: UsergroupMention) -> UsergroupMention:
        """Map usergroup ID to usergroup name."""
        if node.usergroup_id in self.usergroup_map:
            node.usergroup_name = self.usergroup_map[node.usergroup_id]
        return node


class CallbackMapper(NodeVisitor):
    """Visitor that applies custom callback functions to specific node types.

    Args:
        user_callback: Function to transform UserMention nodes
        channel_callback: Function to transform ChannelMention nodes
        usergroup_callback: Function to transform UsergroupMention nodes

    Example:
        >>> from slack_gfm.ast import UserMention
        >>> from slack_gfm.transformers import CallbackMapper
        >>>
        >>> def lookup_user(node: UserMention) -> UserMention:
        ...     # Call API to look up username
        ...     node.username = api.get_user(node.user_id)["name"]
        ...     return node
        >>>
        >>> mapper = CallbackMapper(user_callback=lookup_user)
        >>> transformed = transform_ast(doc, mapper)
    """

    def __init__(
        self,
        user_callback: Callable[[UserMention], UserMention] | None = None,
        channel_callback: Callable[[ChannelMention], ChannelMention] | None = None,
        usergroup_callback: Callable[[UsergroupMention], UsergroupMention] | None = None,
    ):
        self.user_callback = user_callback
        self.channel_callback = channel_callback
        self.usergroup_callback = usergroup_callback

    def visit_usermention(self, node: UserMention) -> UserMention:
        """Apply user callback."""
        if self.user_callback:
            return self.user_callback(node)
        return node

    def visit_channelmention(self, node: ChannelMention) -> ChannelMention:
        """Apply channel callback."""
        if self.channel_callback:
            return self.channel_callback(node)
        return node

    def visit_usergroupmention(self, node: UsergroupMention) -> UsergroupMention:
        """Apply usergroup callback."""
        if self.usergroup_callback:
            return self.usergroup_callback(node)
        return node


def apply_id_mappings(
    ast_node: Any,
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> Any:
    """Apply ID mappings to an AST node (convenience function).

    Args:
        ast_node: AST node to transform
        user_map: Dictionary mapping user IDs to usernames
        channel_map: Dictionary mapping channel IDs to channel names
        usergroup_map: Dictionary mapping usergroup IDs to usergroup names

    Returns:
        Transformed AST node

    Example:
        >>> from slack_gfm.parsers import parse_rich_text
        >>> from slack_gfm.transformers import apply_id_mappings
        >>> from slack_gfm.renderers import render_gfm
        >>>
        >>> ast = parse_rich_text(rich_text_data)
        >>> ast = apply_id_mappings(
        ...     ast,
        ...     user_map={"U123": "john", "U456": "jane"},
        ...     channel_map={"C789": "general"}
        ... )
        >>> gfm = render_gfm(ast)
    """
    from ..ast.visitor import transform_ast

    mapper = IDMapper(
        user_map=user_map, channel_map=channel_map, usergroup_map=usergroup_map
    )
    return transform_ast(ast_node, mapper)
