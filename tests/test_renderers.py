"""Comprehensive renderer tests."""

from slack_gfm.ast import (
    Bold,
    Broadcast,
    ChannelMention,
    Code,
    CodeBlock,
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
from slack_gfm.renderers import render_gfm, render_rich_text


class TestGFMRenderer:
    """Test GFM renderer."""

    def test_render_paragraph(self):
        """Test paragraph rendering."""
        doc = Document(children=[Paragraph(children=[Text(content="Hello")])])
        result = render_gfm(doc)
        assert result == "Hello"

    def test_render_bold(self):
        """Test bold rendering."""
        doc = Document(children=[Paragraph(children=[Bold(children=[Text(content="bold")])])])
        result = render_gfm(doc)
        assert "**bold**" in result

    def test_render_italic(self):
        """Test italic rendering."""
        doc = Document(children=[Paragraph(children=[Italic(children=[Text(content="italic")])])])
        result = render_gfm(doc)
        assert "*italic*" in result

    def test_render_strikethrough(self):
        """Test strikethrough rendering."""
        doc = Document(
            children=[Paragraph(children=[Strikethrough(children=[Text(content="strike")])])]
        )
        result = render_gfm(doc)
        assert "~~strike~~" in result

    def test_render_code(self):
        """Test inline code rendering."""
        doc = Document(children=[Paragraph(children=[Code(content="code")])])
        result = render_gfm(doc)
        assert "`code`" in result

    def test_render_heading(self):
        """Test heading rendering."""
        doc = Document(children=[Heading(level=1, children=[Text(content="Title")])])
        result = render_gfm(doc)
        assert result == "# Title"

    def test_render_code_block(self):
        """Test code block rendering."""
        doc = Document(children=[CodeBlock(content="print('hello')", language="python")])
        result = render_gfm(doc)
        assert "```python" in result
        assert "print('hello')" in result

    def test_render_code_block_no_language(self):
        """Test code block without language.

        Code blocks with no newlines render as inline format for round-trip consistency.
        """
        doc = Document(children=[CodeBlock(content="code")])
        result = render_gfm(doc)
        assert "```code```" in result

    def test_render_list(self):
        """Test list rendering."""
        doc = Document(
            children=[
                List(
                    ordered=False,
                    children=[
                        ListItem(children=[Text(content="Item 1")]),
                        ListItem(children=[Text(content="Item 2")]),
                    ],
                )
            ]
        )
        result = render_gfm(doc)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_render_ordered_list(self):
        """Test ordered list rendering."""
        doc = Document(
            children=[
                List(
                    ordered=True,
                    children=[
                        ListItem(children=[Text(content="First")]),
                        ListItem(children=[Text(content="Second")]),
                    ],
                )
            ]
        )
        result = render_gfm(doc)
        assert "1. First" in result
        assert "2. Second" in result

    def test_render_quote(self):
        """Test quote rendering."""
        doc = Document(
            children=[Quote(children=[Paragraph(children=[Text(content="quoted text")])])]
        )
        result = render_gfm(doc)
        assert "> quoted text" in result

    def test_render_link(self):
        """Test link rendering."""
        doc = Document(
            children=[
                Paragraph(
                    children=[Link(url="https://example.com", children=[Text(content="Link")])]
                )
            ]
        )
        result = render_gfm(doc)
        assert "[Link](https://example.com)" in result

    def test_render_user_mention(self):
        """Test user mention rendering."""
        doc = Document(
            children=[Paragraph(children=[UserMention(user_id="U123", username="john")])]
        )
        result = render_gfm(doc)
        assert "[@john](slack://user?id=U123&name=john)" in result

    def test_render_user_mention_no_name(self):
        """Test user mention without username."""
        doc = Document(children=[Paragraph(children=[UserMention(user_id="U123")])])
        result = render_gfm(doc)
        # When no username is provided, just the ID is shown without @
        assert "[U123](slack://user?id=U123)" in result

    def test_render_channel_mention(self):
        """Test channel mention rendering."""
        doc = Document(
            children=[
                Paragraph(children=[ChannelMention(channel_id="C123", channel_name="general")])
            ]
        )
        result = render_gfm(doc)
        assert "[#general](slack://channel?id=C123&name=general)" in result

    def test_render_usergroup_mention(self):
        """Test usergroup mention rendering."""
        doc = Document(
            children=[
                Paragraph(
                    children=[UsergroupMention(usergroup_id="S123", usergroup_name="engineers")]
                )
            ]
        )
        result = render_gfm(doc)
        assert "[@engineers](slack://usergroup?id=S123&name=engineers)" in result

    def test_render_broadcast(self):
        """Test broadcast rendering."""
        doc = Document(children=[Paragraph(children=[Broadcast(range="here")])])
        result = render_gfm(doc)
        assert "[@here](slack://broadcast?type=here)" in result

    def test_render_horizontal_rule(self):
        """Test horizontal rule rendering."""
        doc = Document(children=[HorizontalRule()])
        result = render_gfm(doc)
        assert "---" in result


class TestRichTextRenderer:
    """Test Rich Text renderer."""

    def test_render_paragraph(self):
        """Test paragraph rendering."""
        doc = Document(children=[Paragraph(children=[Text(content="Hello")])])
        result = render_rich_text(doc)
        assert result["type"] == "rich_text"
        section = result["elements"][0]
        assert section["type"] == "rich_text_section"
        assert section["elements"][0]["text"] == "Hello"

    def test_render_bold(self):
        """Test bold rendering."""
        doc = Document(children=[Paragraph(children=[Bold(children=[Text(content="bold")])])])
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["style"]["bold"] is True

    def test_render_italic(self):
        """Test italic rendering."""
        doc = Document(children=[Paragraph(children=[Italic(children=[Text(content="italic")])])])
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["style"]["italic"] is True

    def test_render_strikethrough(self):
        """Test strikethrough rendering."""
        doc = Document(
            children=[Paragraph(children=[Strikethrough(children=[Text(content="strike")])])]
        )
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["style"]["strike"] is True

    def test_render_code(self):
        """Test inline code rendering."""
        doc = Document(children=[Paragraph(children=[Code(content="code")])])
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["type"] == "text"
        assert elem["style"]["code"] is True

    def test_render_code_block(self):
        """Test code block rendering."""
        doc = Document(children=[CodeBlock(content="print('hello')")])
        result = render_rich_text(doc)
        block = result["elements"][0]
        assert block["type"] == "rich_text_preformatted"
        assert block["elements"][0]["text"] == "print('hello')"

    def test_render_list(self):
        """Test list rendering."""
        doc = Document(
            children=[
                List(
                    ordered=False,
                    children=[ListItem(children=[Text(content="Item")])],
                )
            ]
        )
        result = render_rich_text(doc)
        list_elem = result["elements"][0]
        assert list_elem["type"] == "rich_text_list"
        assert list_elem["style"] == "bullet"

    def test_render_ordered_list(self):
        """Test ordered list rendering."""
        doc = Document(
            children=[
                List(
                    ordered=True,
                    children=[ListItem(children=[Text(content="First")])],
                )
            ]
        )
        result = render_rich_text(doc)
        list_elem = result["elements"][0]
        assert list_elem["style"] == "ordered"

    def test_render_quote(self):
        """Test quote rendering."""
        doc = Document(children=[Quote(children=[Paragraph(children=[Text(content="quoted")])])])
        result = render_rich_text(doc)
        quote = result["elements"][0]
        assert quote["type"] == "rich_text_quote"

    def test_render_user_mention(self):
        """Test user mention rendering."""
        doc = Document(children=[Paragraph(children=[UserMention(user_id="U123")])])
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["type"] == "user"
        assert elem["user_id"] == "U123"

    def test_render_channel_mention(self):
        """Test channel mention rendering."""
        doc = Document(children=[Paragraph(children=[ChannelMention(channel_id="C123")])])
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["type"] == "channel"
        assert elem["channel_id"] == "C123"

    def test_render_broadcast(self):
        """Test broadcast rendering."""
        doc = Document(children=[Paragraph(children=[Broadcast(range="here")])])
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["type"] == "broadcast"
        assert elem["range"] == "here"

    def test_render_link(self):
        """Test link rendering."""
        doc = Document(
            children=[
                Paragraph(
                    children=[Link(url="https://example.com", children=[Text(content="Link")])]
                )
            ]
        )
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["type"] == "link"
        assert elem["url"] == "https://example.com"
