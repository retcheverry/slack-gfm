"""slack-gfm: Convert between Slack message formats and GitHub Flavored Markdown.

This library provides conversion between:
- Slack Rich Text ↔ GitHub Flavored Markdown (GFM)
- Slack mrkdwn → GitHub Flavored Markdown (GFM)

It uses a common Abstract Syntax Tree (AST) format to enable transformations
and ID mappings.
"""

from typing import Any

from .ast.visitor import NodeVisitor, transform_ast
from .exceptions import ParseError, RenderError, SlackGFMError, TransformError, ValidationError
from .parsers import parse_gfm, parse_mrkdwn, parse_rich_text
from .renderers import render_gfm, render_rich_text
from .transformers import CallbackMapper, IDMapper, apply_id_mappings

__version__ = "0.2.0"

__all__ = [
    # Version
    "__version__",
    # Convenience functions
    "rich_text_to_gfm",
    "gfm_to_rich_text",
    "mrkdwn_to_gfm",
    # Parsers
    "parse_rich_text",
    "parse_gfm",
    "parse_mrkdwn",
    # Renderers
    "render_gfm",
    "render_rich_text",
    # Transformers
    "transform_ast",
    "apply_id_mappings",
    "IDMapper",
    "CallbackMapper",
    "NodeVisitor",
    # Exceptions
    "SlackGFMError",
    "ParseError",
    "RenderError",
    "ValidationError",
    "TransformError",
]


def rich_text_to_gfm(
    rich_text_data: dict[str, Any] | list[dict[str, Any]],
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> str:
    """Convert Slack Rich Text to GitHub Flavored Markdown.

    This is the main convenience function for the most common use case.
    Slack-specific features (user mentions, channel mentions, broadcasts) are
    converted to GFM links with custom slack:// URLs to preserve all information.

    Args:
        rich_text_data: Slack Rich Text JSON (either full block or elements array)
        user_map: Optional dictionary mapping user IDs to usernames (e.g., {"U123": "john"})
        channel_map: Optional dictionary mapping channel IDs to names (e.g., {"C456": "general"})
        usergroup_map: Optional dictionary mapping usergroup IDs to names

    Returns:
        GitHub Flavored Markdown string

    Example:
        >>> rich_text = {
        ...     "type": "rich_text",
        ...     "elements": [{
        ...         "type": "rich_text_section",
        ...         "elements": [
        ...             {"type": "text", "text": "Hello "},
        ...             {"type": "user", "user_id": "U123"}
        ...         ]
        ...     }]
        ... }
        >>> gfm = rich_text_to_gfm(rich_text, user_map={"U123": "john"})
        >>> print(gfm)
        Hello [@john](slack://user?id=U123&name=john)
    """
    # Parse Rich Text to AST
    ast = parse_rich_text(rich_text_data)

    # Apply ID mappings if provided
    if user_map or channel_map or usergroup_map:
        ast = apply_id_mappings(
            ast, user_map=user_map, channel_map=channel_map, usergroup_map=usergroup_map
        )

    # Render to GFM
    return render_gfm(ast)


def gfm_to_rich_text(
    gfm_text: str,
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Convert GitHub Flavored Markdown to Slack Rich Text.

    Recognizes custom slack:// URLs and converts them back to Slack-specific elements.

    Args:
        gfm_text: GitHub Flavored Markdown string
        user_map: Optional dictionary mapping user IDs to usernames
        channel_map: Optional dictionary mapping channel IDs to names
        usergroup_map: Optional dictionary mapping usergroup IDs to names

    Returns:
        Slack Rich Text JSON block

    Example:
        >>> gfm = "Hello [@john](slack://user?id=U123&name=john)"
        >>> rich_text = gfm_to_rich_text(gfm)
        >>> rich_text["elements"][0]["elements"][1]
        {'type': 'user', 'user_id': 'U123'}
    """
    # Parse GFM to AST
    ast = parse_gfm(gfm_text)

    # Apply ID mappings if provided
    if user_map or channel_map or usergroup_map:
        ast = apply_id_mappings(
            ast, user_map=user_map, channel_map=channel_map, usergroup_map=usergroup_map
        )

    # Render to Rich Text
    return render_rich_text(ast)


def mrkdwn_to_gfm(
    mrkdwn_text: str,
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> str:
    """Convert Slack mrkdwn to GitHub Flavored Markdown.

    Useful for migrating legacy mrkdwn-formatted messages.

    Args:
        mrkdwn_text: Slack mrkdwn string
        user_map: Optional dictionary mapping user IDs to usernames
        channel_map: Optional dictionary mapping channel IDs to names
        usergroup_map: Optional dictionary mapping usergroup IDs to names

    Returns:
        GitHub Flavored Markdown string

    Example:
        >>> mrkdwn = "*Hello* <@U123|john>"
        >>> gfm = mrkdwn_to_gfm(mrkdwn)
        >>> print(gfm)
        **Hello** [@john](slack://user?id=U123&name=john)
    """
    # Parse mrkdwn to AST
    ast = parse_mrkdwn(mrkdwn_text)

    # Apply ID mappings if provided
    if user_map or channel_map or usergroup_map:
        ast = apply_id_mappings(
            ast, user_map=user_map, channel_map=channel_map, usergroup_map=usergroup_map
        )

    # Render to GFM
    return render_gfm(ast)
