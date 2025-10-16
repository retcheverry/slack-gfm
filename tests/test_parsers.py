"""Comprehensive parser tests."""

from typing import cast

from slack_gfm.ast import (
    Bold,
    Broadcast,
    ChannelMention,
    Code,
    CodeBlock,
    Heading,
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
from slack_gfm.parsers import parse_gfm, parse_mrkdwn, parse_rich_text
from slack_gfm.renderers import render_gfm


class TestGFMParser:
    """Test GFM parser."""

    def test_parse_headings(self) -> None:
        """Test heading parsing."""
        ast = parse_gfm("# Heading 1\n## Heading 2")
        assert len(ast.children) == 2
        assert isinstance(ast.children[0], Heading)
        assert ast.children[0].level == 1
        assert isinstance(ast.children[1], Heading)
        assert ast.children[1].level == 2

    def test_parse_code_block(self) -> None:
        """Test code block parsing."""
        ast = parse_gfm("```python\nprint('hello')\n```")
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], CodeBlock)
        assert ast.children[0].language == "python"
        assert "print('hello')" in ast.children[0].content

    def test_parse_list(self) -> None:
        """Test list parsing."""
        ast = parse_gfm("- Item 1\n- Item 2")
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], List)
        assert not ast.children[0].ordered
        assert len(ast.children[0].children) == 2

    def test_parse_ordered_list(self) -> None:
        """Test ordered list parsing."""
        ast = parse_gfm("1. First\n2. Second")
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], List)
        assert ast.children[0].ordered

    def test_parse_blockquote(self) -> None:
        """Test blockquote parsing."""
        ast = parse_gfm("> This is a quote")
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], Quote)

    def test_parse_slack_user_url(self) -> None:
        """Test parsing slack:// user URL."""
        ast = parse_gfm("[@john](slack://user?id=U123&name=john)")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], UserMention)
        assert para.children[0].user_id == "U123"
        assert para.children[0].username == "john"

    def test_parse_slack_channel_url(self) -> None:
        """Test parsing slack:// channel URL."""
        ast = parse_gfm("[#general](slack://channel?id=C123&name=general)")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], ChannelMention)
        assert para.children[0].channel_id == "C123"
        assert para.children[0].channel_name == "general"

    def test_parse_slack_broadcast_url(self) -> None:
        """Test parsing slack:// broadcast URL."""
        ast = parse_gfm("[@here](slack://broadcast?type=here)")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Broadcast)
        assert para.children[0].range == "here"

    def test_parse_slack_usergroup_url(self) -> None:
        """Test parsing slack:// usergroup URL."""
        ast = parse_gfm("[@engineers](slack://usergroup?id=S123&name=engineers)")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], UsergroupMention)


class TestMrkdwnParser:
    """Test mrkdwn parser."""

    def test_parse_bold(self) -> None:
        """Test bold parsing."""
        ast = parse_mrkdwn("*bold text*")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Bold)

    def test_parse_italic(self) -> None:
        """Test italic parsing."""
        ast = parse_mrkdwn("_italic text_")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Italic)

    def test_parse_strikethrough(self) -> None:
        """Test strikethrough parsing."""
        ast = parse_mrkdwn("~strike~")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Strikethrough)

    def test_parse_code(self) -> None:
        """Test inline code parsing."""
        ast = parse_mrkdwn("`code`")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Code)

    def test_parse_code_block(self) -> None:
        """Test code block parsing."""
        ast = parse_mrkdwn("```\ncode block\n```")
        assert isinstance(ast.children[0], CodeBlock)

    def test_parse_user_mention(self) -> None:
        """Test user mention parsing."""
        ast = parse_mrkdwn("<@U123|john>")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], UserMention)
        assert para.children[0].user_id == "U123"
        assert para.children[0].username == "john"

    def test_parse_user_mention_no_name(self) -> None:
        """Test user mention without name."""
        ast = parse_mrkdwn("<@U123>")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], UserMention)
        assert para.children[0].user_id == "U123"

    def test_parse_channel_mention(self) -> None:
        """Test channel mention parsing."""
        ast = parse_mrkdwn("<#C123|general>")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], ChannelMention)
        assert para.children[0].channel_id == "C123"

    def test_parse_link(self) -> None:
        """Test link parsing."""
        ast = parse_mrkdwn("<https://example.com|Example>")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Link)
        assert para.children[0].url == "https://example.com"

    def test_parse_link_no_text(self) -> None:
        """Test link without text."""
        ast = parse_mrkdwn("<https://example.com>")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Link)

    def test_parse_broadcast(self) -> None:
        """Test broadcast parsing."""
        ast = parse_mrkdwn("<!here>")
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Broadcast)
        assert para.children[0].range == "here"

    def test_parse_blockquote(self) -> None:
        """Test blockquote parsing.

        Note: Slack mrkdwn uses &gt; (HTML entity) for blockquotes, not plain >.
        """
        ast = parse_mrkdwn("&gt; quote text")
        assert isinstance(ast.children[0], Quote)

    def test_parse_list(self) -> None:
        """Test list parsing.

        Slack mrkdwn DOES recognize bullet lists using • character.
        """
        ast = parse_mrkdwn("• Item 1\n• Item 2")
        assert isinstance(ast.children[0], List)
        assert not ast.children[0].ordered
        assert len(ast.children[0].children) == 2


class TestRichTextParser:
    """Test Rich Text parser."""

    def test_parse_simple_section(self) -> None:
        """Test simple section parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "text", "text": "Hello"}],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        assert len(ast.children) == 1
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Text)
        assert para.children[0].content == "Hello"

    def test_parse_styled_text(self) -> None:
        """Test styled text parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {"type": "text", "text": "Bold", "style": {"bold": True}},
                        {"type": "text", "text": "Italic", "style": {"italic": True}},
                        {
                            "type": "text",
                            "text": "Strike",
                            "style": {"strike": True},
                        },
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Bold)
        assert isinstance(para.children[1], Italic)
        assert isinstance(para.children[2], Strikethrough)

    def test_parse_list(self) -> None:
        """Test list parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_list",
                    "style": "bullet",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": "Item 1"}],
                        }
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        assert isinstance(ast.children[0], List)
        assert not ast.children[0].ordered

    def test_parse_code_block(self) -> None:
        """Test code block parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [{"type": "text", "text": "code"}],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        assert isinstance(ast.children[0], CodeBlock)

    def test_parse_quote(self) -> None:
        """Test quote parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_quote",
                    "elements": [{"type": "text", "text": "quote"}],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        assert isinstance(ast.children[0], Quote)

    def test_parse_user_mention(self) -> None:
        """Test user mention parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "user", "user_id": "U123"}],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], UserMention)

    def test_parse_channel_mention(self) -> None:
        """Test channel mention parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "channel", "channel_id": "C123"}],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], ChannelMention)

    def test_parse_broadcast(self) -> None:
        """Test broadcast parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "broadcast", "range": "here"}],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Broadcast)

    def test_parse_link(self) -> None:
        """Test link parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {
                            "type": "link",
                            "url": "https://example.com",
                            "text": "Example",
                        }
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        para = cast(Paragraph, ast.children[0])
        assert isinstance(para.children[0], Link)

    def test_parse_elements_array(self) -> None:
        """Test parsing elements array directly."""
        elements = [
            {
                "type": "rich_text_section",
                "elements": [{"type": "text", "text": "Direct"}],
            }
        ]
        ast = parse_rich_text(elements)
        assert len(ast.children) == 1


class TestMrkdwnCodeBlockEdgeCases:
    """Test mrkdwn code block parsing edge cases that cause escaping bugs."""

    def test_code_block_with_closing_backticks_on_content_line(self) -> None:
        """Test code block where closing ``` is on same line as content."""
        mrkdwn = """```
line 1
line 2```"""
        ast = parse_mrkdwn(mrkdwn)

        # Should parse as a single CodeBlock, not mixed blocks
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], CodeBlock)
        assert "line 1" in ast.children[0].content
        assert "line 2" in ast.children[0].content

    def test_code_block_with_very_long_line_ending_with_backticks(self) -> None:
        """Test code block with very long line ending with ```."""
        # Simulate the real-world case: long JSON line ending with ```
        long_content = "x" * 1000 + " ending"
        mrkdwn = f"```\n{long_content}```"

        ast = parse_mrkdwn(mrkdwn)

        # Should be a single CodeBlock
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], CodeBlock)
        assert long_content in ast.children[0].content

    def test_code_block_with_special_chars_not_escaped(self) -> None:
        """Test that special chars in code blocks are NOT escaped."""
        mrkdwn = """```
version: 3.0.202
host: 10.64.64.98
path: /api/v1
pattern: test.*regex
math: (a+b)*c
```"""
        ast = parse_mrkdwn(mrkdwn)
        gfm = render_gfm(ast)

        # Content should NOT be escaped
        assert "3.0.202" in gfm
        assert r"3\.0\.202" not in gfm
        assert "10.64.64.98" in gfm
        assert r"test\.\*regex" not in gfm
        assert r"\(a\+b\)" not in gfm

    def test_code_block_with_backslash_n_not_doubled(self) -> None:
        """Test that literal backslash-n sequences are not doubled."""
        mrkdwn = r"""```
"debug": "Line 1\nLine 2\nLine 3"
```"""
        ast = parse_mrkdwn(mrkdwn)
        gfm = render_gfm(ast)

        # Backslashes should NOT be doubled (2 \n in input = 2 \n in output)
        backslash_count = gfm.count("\\")
        assert backslash_count == 2, f"Expected 2 backslashes, got {backslash_count}"
        # Count \n sequences - should be 2, not 4 (which would mean doubling)
        assert gfm.count(r"\n") == 2

    def test_code_block_json_with_escapes_ending_with_backticks(self) -> None:
        """Test realistic JSON code block ending with ``` on content line."""
        mrkdwn = r"""```{
  "message": "Exception occurred",
  "debug": "Service Name: test\nVersion: 3.0.202\nHost: 10.64.64.98"
}```"""
        ast = parse_mrkdwn(mrkdwn)

        # Should be a single CodeBlock
        assert len(ast.children) == 1, f"Expected 1 block, got {len(ast.children)}"
        assert isinstance(ast.children[0], CodeBlock), (
            f"Expected CodeBlock, got {type(ast.children[0])}"
        )

        # Render and check no escaping
        gfm = render_gfm(ast)
        assert "3.0.202" in gfm
        assert r"3\.0\.202" not in gfm
        assert r"10\.64\.64\.98" not in gfm

        # Backslash-n should not be doubled (2 \n in input = 2 \n in output)
        assert gfm.count(r"\n") == 2

    def test_multiple_code_blocks_with_mixed_formats(self) -> None:
        """Test multiple code blocks with various closing styles."""
        mrkdwn = """First paragraph

```
code block 1
```

```{
json block
}```

Last paragraph"""

        ast = parse_mrkdwn(mrkdwn)
        gfm = render_gfm(ast)

        # Should have parsed correctly: 2 paragraphs and 2 code blocks
        code_blocks = [c for c in ast.children if isinstance(c, CodeBlock)]
        paragraphs = [c for c in ast.children if isinstance(c, Paragraph)]

        assert len(code_blocks) == 2, f"Expected 2 code blocks, got {len(code_blocks)}"
        assert len(paragraphs) == 2, f"Expected 2 paragraphs, got {len(paragraphs)}"

        # No escaping in output
        assert r"\{" not in gfm
        assert r"\}" not in gfm


class TestRichTextPreformattedInlineElements:
    """Test all inline element types inside rich_text_preformatted blocks.

    According to Slack documentation, the following inline elements can appear
    in rich_text_preformatted blocks: text, link, emoji, user, usergroup,
    channel, date, broadcast, and color.
    """

    def test_preformatted_with_link(self) -> None:
        """Test link element in preformatted block."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "curl -X GET "},
                        {"type": "link", "url": "https://example.com/api"},
                        {"type": "text", "text": " -H 'Accept: application/json'"},
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        code_block = ast.children[0]
        assert isinstance(code_block, CodeBlock)
        # The content should include the URL as plain text
        assert "https://example.com/api" in code_block.content
        assert "curl -X GET" in code_block.content
        assert "Accept: application/json" in code_block.content

    def test_preformatted_with_user_mention(self) -> None:
        """Test user mention in preformatted block."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "Author: "},
                        {"type": "user", "user_id": "U123ABC"},
                        {"type": "text", "text": "\nDate: 2024-01-01"},
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        code_block = ast.children[0]
        assert isinstance(code_block, CodeBlock)
        # User mention should be rendered as plain text (e.g., <@U123ABC>)
        assert "U123ABC" in code_block.content or "@U123ABC" in code_block.content
        assert "Author:" in code_block.content

    def test_preformatted_with_channel_mention(self) -> None:
        """Test channel mention in preformatted block."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "Post to "},
                        {"type": "channel", "channel_id": "C123XYZ"},
                        {"type": "text", "text": " channel"},
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        code_block = ast.children[0]
        assert isinstance(code_block, CodeBlock)
        # Channel mention should be rendered as plain text
        assert "C123XYZ" in code_block.content or "#C123XYZ" in code_block.content
        assert "Post to" in code_block.content

    def test_preformatted_with_usergroup_mention(self) -> None:
        """Test usergroup mention in preformatted block."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "CC: "},
                        {"type": "usergroup", "usergroup_id": "S123DEF"},
                        {"type": "text", "text": " team"},
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        code_block = ast.children[0]
        assert isinstance(code_block, CodeBlock)
        # Usergroup mention should be rendered as plain text
        assert "S123DEF" in code_block.content or "@S123DEF" in code_block.content
        assert "CC:" in code_block.content

    def test_preformatted_with_emoji(self) -> None:
        """Test emoji in preformatted block."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "Status: "},
                        {"type": "emoji", "name": "white_check_mark", "unicode": "✅"},
                        {"type": "text", "text": " Success"},
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        code_block = ast.children[0]
        assert isinstance(code_block, CodeBlock)
        # Emoji should be rendered as unicode or :emoji_name:
        assert "✅" in code_block.content or "white_check_mark" in code_block.content
        assert "Status:" in code_block.content

    def test_preformatted_with_broadcast(self) -> None:
        """Test broadcast in preformatted block."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "Notify: "},
                        {"type": "broadcast", "range": "here"},
                        {"type": "text", "text": " immediately"},
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        code_block = ast.children[0]
        assert isinstance(code_block, CodeBlock)
        # Broadcast should be rendered as plain text
        assert "here" in code_block.content or "@here" in code_block.content
        assert "Notify:" in code_block.content

    def test_preformatted_with_date(self) -> None:
        """Test date timestamp in preformatted block."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "Deployed at: "},
                        {
                            "type": "date",
                            "timestamp": 1704067200,
                            "format": "{date_short_pretty}",
                            "fallback": "Jan 1, 2024",
                        },
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        code_block = ast.children[0]
        assert isinstance(code_block, CodeBlock)
        # Date should be rendered as plain text (timestamp or fallback)
        assert "1704067200" in code_block.content or "Jan 1, 2024" in code_block.content
        assert "Deployed at:" in code_block.content

    def test_preformatted_with_multiple_links(self) -> None:
        """Test multiple links in preformatted block."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "API: "},
                        {"type": "link", "url": "https://api.example.com"},
                        {"type": "text", "text": "\nDocs: "},
                        {"type": "link", "url": "https://docs.example.com"},
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        code_block = ast.children[0]
        assert isinstance(code_block, CodeBlock)
        assert "https://api.example.com" in code_block.content
        assert "https://docs.example.com" in code_block.content

    def test_preformatted_roundtrip_with_link(self) -> None:
        """Test that preformatted blocks with links can round-trip through GFM."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [
                        {"type": "text", "text": "URL: "},
                        {"type": "link", "url": "https://example.com"},
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        gfm = render_gfm(ast)

        # The GFM should contain the URL as plain text in a code block
        assert "```" in gfm
        assert "https://example.com" in gfm
        assert "URL:" in gfm
