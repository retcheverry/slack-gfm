"""Comprehensive parser tests."""


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


class TestGFMParser:
    """Test GFM parser."""

    def test_parse_headings(self):
        """Test heading parsing."""
        ast = parse_gfm("# Heading 1\n## Heading 2")
        assert len(ast.children) == 2
        assert isinstance(ast.children[0], Heading)
        assert ast.children[0].level == 1
        assert isinstance(ast.children[1], Heading)
        assert ast.children[1].level == 2

    def test_parse_code_block(self):
        """Test code block parsing."""
        ast = parse_gfm("```python\nprint('hello')\n```")
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], CodeBlock)
        assert ast.children[0].language == "python"
        assert "print('hello')" in ast.children[0].content

    def test_parse_list(self):
        """Test list parsing."""
        ast = parse_gfm("- Item 1\n- Item 2")
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], List)
        assert not ast.children[0].ordered
        assert len(ast.children[0].children) == 2

    def test_parse_ordered_list(self):
        """Test ordered list parsing."""
        ast = parse_gfm("1. First\n2. Second")
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], List)
        assert ast.children[0].ordered

    def test_parse_blockquote(self):
        """Test blockquote parsing."""
        ast = parse_gfm("> This is a quote")
        assert len(ast.children) == 1
        assert isinstance(ast.children[0], Quote)

    def test_parse_slack_user_url(self):
        """Test parsing slack:// user URL."""
        ast = parse_gfm("[@john](slack://user?id=U123&name=john)")
        para = ast.children[0]
        assert isinstance(para.children[0], UserMention)
        assert para.children[0].user_id == "U123"
        assert para.children[0].username == "john"

    def test_parse_slack_channel_url(self):
        """Test parsing slack:// channel URL."""
        ast = parse_gfm("[#general](slack://channel?id=C123&name=general)")
        para = ast.children[0]
        assert isinstance(para.children[0], ChannelMention)
        assert para.children[0].channel_id == "C123"
        assert para.children[0].channel_name == "general"

    def test_parse_slack_broadcast_url(self):
        """Test parsing slack:// broadcast URL."""
        ast = parse_gfm("[@here](slack://broadcast?type=here)")
        para = ast.children[0]
        assert isinstance(para.children[0], Broadcast)
        assert para.children[0].type == "here"

    def test_parse_slack_usergroup_url(self):
        """Test parsing slack:// usergroup URL."""
        ast = parse_gfm("[@engineers](slack://usergroup?id=S123&name=engineers)")
        para = ast.children[0]
        assert isinstance(para.children[0], UsergroupMention)


class TestMrkdwnParser:
    """Test mrkdwn parser."""

    def test_parse_bold(self):
        """Test bold parsing."""
        ast = parse_mrkdwn("*bold text*")
        para = ast.children[0]
        assert isinstance(para.children[0], Bold)

    def test_parse_italic(self):
        """Test italic parsing."""
        ast = parse_mrkdwn("_italic text_")
        para = ast.children[0]
        assert isinstance(para.children[0], Italic)

    def test_parse_strikethrough(self):
        """Test strikethrough parsing."""
        ast = parse_mrkdwn("~strike~")
        para = ast.children[0]
        assert isinstance(para.children[0], Strikethrough)

    def test_parse_code(self):
        """Test inline code parsing."""
        ast = parse_mrkdwn("`code`")
        para = ast.children[0]
        assert isinstance(para.children[0], Code)

    def test_parse_code_block(self):
        """Test code block parsing."""
        ast = parse_mrkdwn("```\ncode block\n```")
        assert isinstance(ast.children[0], CodeBlock)

    def test_parse_user_mention(self):
        """Test user mention parsing."""
        ast = parse_mrkdwn("<@U123|john>")
        para = ast.children[0]
        assert isinstance(para.children[0], UserMention)
        assert para.children[0].user_id == "U123"
        assert para.children[0].username == "john"

    def test_parse_user_mention_no_name(self):
        """Test user mention without name."""
        ast = parse_mrkdwn("<@U123>")
        para = ast.children[0]
        assert isinstance(para.children[0], UserMention)
        assert para.children[0].user_id == "U123"

    def test_parse_channel_mention(self):
        """Test channel mention parsing."""
        ast = parse_mrkdwn("<#C123|general>")
        para = ast.children[0]
        assert isinstance(para.children[0], ChannelMention)
        assert para.children[0].channel_id == "C123"

    def test_parse_link(self):
        """Test link parsing."""
        ast = parse_mrkdwn("<https://example.com|Example>")
        para = ast.children[0]
        assert isinstance(para.children[0], Link)
        assert para.children[0].url == "https://example.com"

    def test_parse_link_no_text(self):
        """Test link without text."""
        ast = parse_mrkdwn("<https://example.com>")
        para = ast.children[0]
        assert isinstance(para.children[0], Link)

    def test_parse_broadcast(self):
        """Test broadcast parsing."""
        ast = parse_mrkdwn("<!here>")
        para = ast.children[0]
        assert isinstance(para.children[0], Broadcast)
        assert para.children[0].type == "here"

    def test_parse_blockquote(self):
        """Test blockquote parsing."""
        ast = parse_mrkdwn("> quote text")
        assert isinstance(ast.children[0], Quote)

    def test_parse_list(self):
        """Test list parsing."""
        # Note: mrkdwn doesn't auto-detect bullet lists like markdown
        # This is parsed as plain text
        ast = parse_mrkdwn("• Item 1\n• Item 2")
        assert isinstance(ast.children[0], Paragraph)


class TestRichTextParser:
    """Test Rich Text parser."""

    def test_parse_simple_section(self):
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
        para = ast.children[0]
        assert isinstance(para.children[0], Text)
        assert para.children[0].content == "Hello"

    def test_parse_styled_text(self):
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
        para = ast.children[0]
        assert isinstance(para.children[0], Bold)
        assert isinstance(para.children[1], Italic)
        assert isinstance(para.children[2], Strikethrough)

    def test_parse_list(self):
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

    def test_parse_code_block(self):
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

    def test_parse_quote(self):
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

    def test_parse_user_mention(self):
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
        para = ast.children[0]
        assert isinstance(para.children[0], UserMention)

    def test_parse_channel_mention(self):
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
        para = ast.children[0]
        assert isinstance(para.children[0], ChannelMention)

    def test_parse_broadcast(self):
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
        para = ast.children[0]
        assert isinstance(para.children[0], Broadcast)

    def test_parse_link(self):
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
        para = ast.children[0]
        assert isinstance(para.children[0], Link)

    def test_parse_elements_array(self):
        """Test parsing elements array directly."""
        elements = [
            {
                "type": "rich_text_section",
                "elements": [{"type": "text", "text": "Direct"}],
            }
        ]
        ast = parse_rich_text(elements)
        assert len(ast.children) == 1
