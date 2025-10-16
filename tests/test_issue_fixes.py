"""Unit tests for specific issues found during testing.

These tests document and verify fixes for edge cases found in real-world usage.
Each test corresponds to an issue documented in .issues/ directory.
"""

from slack_gfm import gfm_to_rich_text, mrkdwn_to_gfm


class TestIssue02:
    """Issue 02: mrkdwn → GFM inline code block with no newlines.

    When a code block has no newlines after opening ``` and before closing ```,
    the GFM output should preserve this format without adding extra newlines.

    Input:  ```no newlines```
    Expected: ```no newlines```
    Actual: ```no newlines```\n```  (WRONG - extra newline + ```)
    """

    def test_inline_code_block_no_newlines(self) -> None:
        """Test code block on single line without newlines."""
        mrkdwn = "```no newlines```"
        result = mrkdwn_to_gfm(mrkdwn)

        # Should preserve single-line format
        assert result == "```no newlines```", f"Got: {repr(result)}"

        # Should NOT have extra newlines or closing ```
        assert result.count("```") == 2, "Should have exactly 2 ``` markers"
        assert "\n" not in result, "Should not contain newlines"


class TestIssue05:
    """Issue 05: mrkdwn → GFM code block with content on opening line.

    When a code block has content on the opening ``` line but has a newline
    before the closing ```, the GFM output adds an unwanted extra newline.

    Input:  ```no newline at start\n```
    Expected: ```no newline at start\n```
    Actual: ```no newline at start\n\n```  (WRONG - extra newline)
    """

    def test_code_block_content_on_opening_line(self) -> None:
        """Test code block with content on same line as opening ```."""
        mrkdwn = "```no newline at start\n```"
        result = mrkdwn_to_gfm(mrkdwn)

        expected = "```no newline at start\n```"
        assert result == expected, f"Expected: {repr(expected)}, Got: {repr(result)}"

        # Should have exactly one newline (before closing ```)
        assert result.count("\n") == 1, (
            f"Should have exactly 1 newline, got {result.count(chr(10))}"
        )


class TestIssue06:
    """Issue 06: mrkdwn → GFM multiline code block with no newline after opening.

    When a code block has content on the opening line and includes internal
    newlines, the GFM output should add a newline after the opening ```.

    Input:  ```no newline at start\nor at the end\nthe code block includes newlines though```
    Expected: ```\nno newline at start\nor at the end\nthe code block includes newlines though\n```
    Actual: ```no newline at start\nor at the end\nthe code block includes newlines though\n```
           (WRONG - missing newline after opening ```)
    """

    def test_multiline_code_block_no_newline_after_opening(self) -> None:
        """Test multiline code block with content starting on opening line."""
        mrkdwn = "```no newline at start\nor at the end\nthe code block includes newlines though```"
        result = mrkdwn_to_gfm(mrkdwn)

        # GFM format requires newline after opening ```
        expected = (
            "```\nno newline at start\nor at the end\nthe code block includes newlines though\n```"
        )
        assert result == expected, f"Expected: {repr(expected)}, Got: {repr(result)}"

        # Should start with ```\n not ```content
        assert result.startswith("```\n"), "Should have newline after opening ```"

        # Should end with \n```
        assert result.endswith("\n```"), "Should have newline before closing ```"


class TestIssue07:
    """Issue 07: mrkdwn → GFM angle brackets around URLs in code blocks.

    In mrkdwn, <url> outside code blocks is a clickable link.
    Inside code blocks, <url> should be treated as literal text, but the
    angle brackets should be removed to show just the URL.

    Input:  ```\n<https://example.com>\n```
    Expected: ```\nhttps://example.com\n```
    Actual: ```\n<https://example.com>\n```  (WRONG - brackets not removed)
    """

    def test_angle_brackets_removed_in_code_blocks(self) -> None:
        """Test that angle brackets around URLs are removed in code blocks."""
        mrkdwn = "```\n<https://example.com>\n```"
        result = mrkdwn_to_gfm(mrkdwn)

        # Angle brackets should be removed
        expected = "```\nhttps://example.com\n```"
        assert result == expected, f"Expected: {repr(expected)}, Got: {repr(result)}"

        # Should NOT contain angle brackets
        assert "<" not in result, "Should not contain < in code block"
        assert ">" not in result, "Should not contain > in code block"

    def test_angle_brackets_with_multiple_urls(self) -> None:
        """Test multiple URLs with angle brackets in same code block."""
        mrkdwn = "```\n<https://api.example.com>\n<https://docs.example.com>\n```"
        result = mrkdwn_to_gfm(mrkdwn)

        expected = "```\nhttps://api.example.com\nhttps://docs.example.com\n```"
        assert result == expected, f"Expected: {repr(expected)}, Got: {repr(result)}"

        assert "<" not in result
        assert ">" not in result

    def test_angle_brackets_not_around_urls(self) -> None:
        """Test angle brackets that aren't around URLs (should be kept)."""
        mrkdwn = "```\nif (x > 5 && y < 10) {}\n```"
        result = mrkdwn_to_gfm(mrkdwn)

        # These angle brackets are part of code, not URL markers
        expected = "```\nif (x > 5 && y < 10) {}\n```"
        assert result == expected, f"Expected: {repr(expected)}, Got: {repr(result)}"


class TestIssue08:
    """Issue 08: GFM → Rich Text preformatted blocks gain trailing newline.

    When converting GFM code blocks to Rich Text preformatted blocks,
    an extra newline is being added to the text content.

    Input GFM:  ```\nxyz\n```
    Expected RT: {"type": "text", "text": "xyz"}
    Actual RT:   {"type": "text", "text": "xyz\n"}  (WRONG - extra \n)
    """

    def test_gfm_to_rich_text_no_trailing_newline(self) -> None:
        """Test that code block content doesn't gain trailing newline."""
        gfm = "```\nxyz\n```"
        result = gfm_to_rich_text(gfm)

        # Navigate to the text element in rich text structure
        assert result["type"] == "rich_text"
        assert len(result["elements"]) == 1

        preformatted = result["elements"][0]
        assert preformatted["type"] == "rich_text_preformatted"
        assert len(preformatted["elements"]) == 1

        text_elem = preformatted["elements"][0]
        assert text_elem["type"] == "text"

        # The text should be "xyz" without trailing newline
        assert text_elem["text"] == "xyz", f"Expected 'xyz', got {repr(text_elem['text'])}"
        assert not text_elem["text"].endswith("\n"), "Text should not end with newline"

    def test_gfm_to_rich_text_multiline_no_extra_newline(self) -> None:
        """Test multiline code block doesn't add extra trailing newline."""
        gfm = "```\nline1\nline2\nline3\n```"
        result = gfm_to_rich_text(gfm)

        text_elem = result["elements"][0]["elements"][0]
        expected_text = "line1\nline2\nline3"

        assert text_elem["text"] == expected_text, (
            f"Expected {repr(expected_text)}, got {repr(text_elem['text'])}"
        )

        # Should have exactly 2 newlines (between lines), not 3
        assert text_elem["text"].count("\n") == 2, (
            f"Should have 2 newlines, got {text_elem['text'].count(chr(10))}"
        )

    def test_gfm_to_rich_text_empty_code_block(self) -> None:
        """Test empty code block edge case."""
        gfm = "```\n\n```"
        result = gfm_to_rich_text(gfm)

        text_elem = result["elements"][0]["elements"][0]

        # Empty code block should have empty string or single newline, not double
        assert text_elem["text"] in ["", "\n"], (
            f"Expected empty or single newline, got {repr(text_elem['text'])}"
        )


class TestCodeBlockRoundTrip:
    """Test that code blocks can round-trip through conversions without data loss."""

    def test_simple_code_block_roundtrip_mrkdwn_gfm_richtext(self) -> None:
        """Test mrkdwn → GFM → Rich Text → GFM preserves content.

        Note: Slack's Rich Text format strips trailing newlines from code blocks,
        so the round-trip normalizes to inline format when there are no meaningful newlines.
        """
        original_mrkdwn = "```\nhello world\n```"

        # mrkdwn → GFM
        gfm = mrkdwn_to_gfm(original_mrkdwn)

        # GFM → Rich Text
        rich_text = gfm_to_rich_text(gfm)

        # Rich Text → GFM (using library functions)
        from slack_gfm import rich_text_to_gfm

        gfm_roundtrip = rich_text_to_gfm(rich_text)

        # Round-trip normalizes format (Slack strips newlines), but content is preserved
        assert "hello world" in gfm_roundtrip
        # After normalization, should be inline format (no trailing newlines in Rich Text)
        assert gfm_roundtrip == "```hello world```"

    def test_code_block_with_special_chars_roundtrip(self) -> None:
        """Test code block with special characters preserves them exactly."""
        original_mrkdwn = "```\nversion: 3.0.202\nhost: 10.64.64.98\npattern: test.*regex\n```"

        gfm = mrkdwn_to_gfm(original_mrkdwn)
        rich_text = gfm_to_rich_text(gfm)

        # Extract text content
        text_content = rich_text["elements"][0]["elements"][0]["text"]

        # Special chars should NOT be escaped
        assert "3.0.202" in text_content
        assert "10.64.64.98" in text_content
        assert "test.*regex" in text_content

        # No escaping artifacts
        assert r"\." not in text_content
        assert r"\*" not in text_content
