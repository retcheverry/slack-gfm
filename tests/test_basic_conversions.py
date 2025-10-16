"""Basic conversion tests for slack-gfm."""

from slack_gfm import gfm_to_rich_text, mrkdwn_to_gfm, rich_text_to_gfm


class TestRichTextToGFM:
    """Test Rich Text to GFM conversion."""

    def test_simple_text(self) -> None:
        """Test simple text conversion."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }

        result = rich_text_to_gfm(rich_text)
        assert result == "Hello world"

    def test_bold_text(self) -> None:
        """Test bold text conversion."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "text", "text": "Hello", "style": {"bold": True}}],
                }
            ],
        }

        result = rich_text_to_gfm(rich_text)
        assert result == "**Hello**"

    def test_user_mention(self) -> None:
        """Test user mention conversion."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "user", "user_id": "U123ABC"}],
                }
            ],
        }

        result = rich_text_to_gfm(rich_text)
        assert "slack://user" in result
        assert "id=U123ABC" in result

    def test_user_mention_with_mapping(self) -> None:
        """Test user mention with ID mapping."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "user", "user_id": "U123ABC"}],
                }
            ],
        }

        result = rich_text_to_gfm(rich_text, user_map={"U123ABC": "john"})
        assert "@john" in result
        assert "name=john" in result

    def test_code_block(self) -> None:
        """Test code block conversion."""
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_preformatted",
                    "elements": [{"type": "text", "text": "print('hello')"}],
                }
            ],
        }

        result = rich_text_to_gfm(rich_text)
        assert "```" in result
        assert "print('hello')" in result


class TestGFMToRichText:
    """Test GFM to Rich Text conversion."""

    def test_simple_text(self) -> None:
        """Test simple text conversion."""
        gfm = "Hello world"
        result = gfm_to_rich_text(gfm)

        assert result["type"] == "rich_text"
        assert len(result["elements"]) > 0
        # Check for text content
        first_elem = result["elements"][0]
        assert first_elem["type"] == "rich_text_section"

    def test_bold_text(self) -> None:
        """Test bold text conversion."""
        gfm = "**Hello**"
        result = gfm_to_rich_text(gfm)

        elements = result["elements"][0]["elements"]
        # Should contain a text element with bold style
        assert any(
            elem.get("style", {}).get("bold") for elem in elements if elem.get("type") == "text"
        )

    def test_slack_url_user_mention(self) -> None:
        """Test slack:// URL conversion back to user mention."""
        gfm = "[@john](slack://user?id=U123ABC&name=john)"
        result = gfm_to_rich_text(gfm)

        elements = result["elements"][0]["elements"]
        user_elem = next(elem for elem in elements if elem.get("type") == "user")
        assert user_elem["user_id"] == "U123ABC"


class TestMrkdwnToGFM:
    """Test mrkdwn to GFM conversion."""

    def test_simple_text(self) -> None:
        """Test simple text conversion."""
        mrkdwn = "Hello world"
        result = mrkdwn_to_gfm(mrkdwn)
        assert "Hello world" in result

    def test_bold_syntax(self) -> None:
        """Test mrkdwn bold (*) to GFM bold (**)."""
        mrkdwn = "*Hello*"
        result = mrkdwn_to_gfm(mrkdwn)
        assert "**Hello**" in result

    def test_italic_syntax(self) -> None:
        """Test mrkdwn italic (_) to GFM italic (*)."""
        mrkdwn = "_Hello_"
        result = mrkdwn_to_gfm(mrkdwn)
        assert "*Hello*" in result

    def test_user_mention(self) -> None:
        """Test mrkdwn user mention conversion."""
        mrkdwn = "<@U123ABC|john>"
        result = mrkdwn_to_gfm(mrkdwn)
        assert "slack://user" in result
        assert "id=U123ABC" in result
        assert "@john" in result

    def test_link(self) -> None:
        """Test mrkdwn link conversion."""
        mrkdwn = "<https://example.com|Example>"
        result = mrkdwn_to_gfm(mrkdwn)
        assert "[Example](https://example.com)" in result


class TestRoundTrip:
    """Test round-trip conversions."""

    def test_rich_text_to_gfm_to_rich_text(self) -> None:
        """Test Rich Text → GFM → Rich Text preserves data."""
        original = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {"type": "text", "text": "Hello "},
                        {"type": "user", "user_id": "U123"},
                    ],
                }
            ],
        }

        # Convert to GFM and back
        gfm = rich_text_to_gfm(original)
        result = gfm_to_rich_text(gfm)

        # Check structure is preserved
        assert result["type"] == "rich_text"
        elements = result["elements"][0]["elements"]

        # Should have user element with correct ID
        user_elem = next(elem for elem in elements if elem.get("type") == "user")
        assert user_elem["user_id"] == "U123"
