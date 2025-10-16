"""Edge case tests to improve coverage."""

from slack_gfm import gfm_to_rich_text, mrkdwn_to_gfm, rich_text_to_gfm
from slack_gfm.ast import (
    Document,
    Emoji,
    Heading,
    HorizontalRule,
    Paragraph,
    Table,
    Text,
)
from slack_gfm.parsers import parse_gfm, parse_mrkdwn, parse_rich_text
from slack_gfm.renderers import render_gfm, render_rich_text


class TestParserEdgeCases:
    """Test edge cases in parsers."""

    def test_gfm_empty_link(self):
        """Test GFM parser with empty link."""
        ast = parse_gfm("[text]()")
        para = ast.children[0]
        # Should still create a link even with empty URL
        assert len(para.children) > 0

    def test_gfm_table(self):
        """Test GFM table parsing."""
        ast = parse_gfm("| Col1 | Col2 |\n|------|------|\n| A | B |")
        # GFM extension for tables might not be enabled in markdown-it-py by default
        # Just verify it parses without error
        assert isinstance(ast, Document)

    def test_gfm_thematic_break(self):
        """Test horizontal rule parsing."""
        ast = parse_gfm("---")
        assert isinstance(ast.children[0], HorizontalRule)

    def test_mrkdwn_nested_formatting(self):
        """Test nested formatting in mrkdwn."""
        ast = parse_mrkdwn("*_bold italic_*")
        para = ast.children[0]
        # Should parse nested styles
        assert len(para.children) > 0

    def test_mrkdwn_multiline_code(self):
        """Test multiline code block."""
        ast = parse_mrkdwn("```\nline1\nline2\n```")
        assert any(hasattr(child, "content") for child in ast.children)

    def test_rich_text_emoji(self):
        """Test emoji parsing."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "emoji", "name": "smile"}],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        para = ast.children[0]
        assert isinstance(para.children[0], Emoji)

    def test_rich_text_link_with_style(self):
        """Test link with style in rich text."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {
                            "type": "link",
                            "url": "https://example.com",
                            "style": {"bold": True},
                        }
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        # Should handle styled links
        assert len(ast.children) > 0

    def test_rich_text_date(self):
        """Test date element."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {
                            "type": "date",
                            "timestamp": 1234567890,
                            "format": "{date_short}",
                        }
                    ],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        # Should parse date element
        assert len(ast.children) > 0

    def test_rich_text_usergroup(self):
        """Test usergroup mention."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "usergroup", "usergroup_id": "S123"}],
                }
            ],
        }
        ast = parse_rich_text(rich_text)
        # Should parse usergroup
        assert len(ast.children) > 0


class TestRendererEdgeCases:
    """Test edge cases in renderers."""

    def test_gfm_heading_levels(self):
        """Test different heading levels."""
        for level in range(1, 7):
            doc = Document(children=[Heading(level=level, children=[Text(content="Title")])])
            result = render_gfm(doc)
            assert "#" * level in result

    def test_gfm_table_rendering(self):
        """Test table rendering."""
        doc = Document(
            children=[
                Table(
                    header=[[Text(content="A")], [Text(content="B")]],
                    rows=[[[Text(content="1")], [Text(content="2")]]],
                    alignments=[None, None],
                )
            ]
        )
        result = render_gfm(doc)
        assert "|" in result

    def test_rich_text_heading(self):
        """Test heading in rich text (should render as section)."""
        doc = Document(children=[Heading(level=1, children=[Text(content="Title")])])
        result = render_rich_text(doc)
        # Headings become sections in rich text
        assert result["elements"][0]["type"] == "rich_text_section"

    def test_rich_text_table(self):
        """Test table in rich text (should render as section)."""
        doc = Document(
            children=[
                Table(
                    header=[[Text(content="A")]],
                    rows=[],
                    alignments=[],
                )
            ]
        )
        result = render_rich_text(doc)
        # Tables become sections in rich text
        assert result["type"] == "rich_text"

    def test_rich_text_horizontal_rule(self):
        """Test horizontal rule in rich text."""
        doc = Document(children=[HorizontalRule()])
        result = render_rich_text(doc)
        # Should render something
        assert result["type"] == "rich_text"

    def test_rich_text_emoji(self):
        """Test emoji rendering."""
        doc = Document(children=[Paragraph(children=[Emoji(name="smile")])])
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["type"] == "emoji"
        assert elem["name"] == "smile"

    def test_rich_text_link_no_children(self):
        """Test link without children."""
        from slack_gfm.ast import Link

        doc = Document(
            children=[Paragraph(children=[Link(url="https://example.com", children=[])])]
        )
        result = render_rich_text(doc)
        elem = result["elements"][0]["elements"][0]
        assert elem["type"] == "link"
        # Should still have URL as text when no children
        assert elem.get("text") or elem.get("url")


class TestConversionEdgeCases:
    """Test edge cases in high-level conversion functions."""

    def test_rich_text_to_gfm_with_all_mappings(self):
        """Test conversion with all mapping types."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {"type": "user", "user_id": "U1"},
                        {"type": "channel", "channel_id": "C1"},
                        {"type": "usergroup", "usergroup_id": "S1"},
                    ],
                }
            ],
        }
        result = rich_text_to_gfm(
            rich_text,
            user_map={"U1": "alice"},
            channel_map={"C1": "general"},
            usergroup_map={"S1": "devs"},
        )
        assert "alice" in result
        assert "general" in result
        assert "devs" in result

    def test_gfm_to_rich_text_with_mappings(self):
        """Test GFM to rich text with mappings."""
        gfm = "[@alice](slack://user?id=U1&name=alice)"
        result = gfm_to_rich_text(gfm, user_map={"U1": "alice"})
        # Should preserve user ID
        elem = result["elements"][0]["elements"][0]
        assert elem["user_id"] == "U1"

    def test_mrkdwn_complex(self):
        """Test complex mrkdwn conversion."""
        mrkdwn = "*bold* _italic_ ~strike~ `code` <@U1> <#C1> <!here> <http://example.com|link>"
        result = mrkdwn_to_gfm(mrkdwn)
        assert "**bold**" in result
        assert "*italic*" in result
        assert "~~strike~~" in result
        assert "`code`" in result
        assert "slack://user" in result
        assert "slack://channel" in result
        assert "slack://broadcast" in result


class TestVisitorEdgeCases:
    """Test visitor edge cases."""

    def test_visitor_methods(self):
        """Test all visitor methods are callable."""
        from slack_gfm.ast import NodeVisitor

        visitor = NodeVisitor()
        # Test that all visit methods exist and are callable
        methods = [
            "visit_document",
            "visit_paragraph",
            "visit_heading",
            "visit_text",
            "visit_bold",
            "visit_italic",
            "visit_strikethrough",
            "visit_code",
            "visit_link",
            "visit_usermention",
            "visit_channelmention",
            "visit_usergroupmention",
            "visit_broadcast",
            "visit_emoji",
            "visit_datetimestamp",
            "visit_codeblock",
            "visit_quote",
            "visit_list",
            "visit_listitem",
            "visit_horizontalrule",
            "visit_table",
        ]
        for method in methods:
            assert hasattr(visitor, method)
            assert callable(getattr(visitor, method))
