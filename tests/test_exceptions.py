"""Tests for exception classes."""

import pytest

from slack_gfm import (
    ParseError,
    RenderError,
    SlackGFMError,
    TransformError,
    ValidationError,
)


class TestSlackGFMError:
    """Test the base exception class."""

    def test_basic_exception(self):
        """Test exception with just a message."""
        exc = SlackGFMError("Something went wrong")

        assert exc.message == "Something went wrong"
        assert exc.context == {}
        assert str(exc) == "Something went wrong"

    def test_exception_with_context(self):
        """Test exception with context information."""
        context = {"element_type": "unknown", "position": 42}
        exc = SlackGFMError("Parse failed", context=context)

        assert exc.message == "Parse failed"
        assert exc.context == context
        assert "element_type='unknown'" in str(exc)
        assert "position=42" in str(exc)

    def test_exception_repr(self):
        """Test exception representation."""
        exc = SlackGFMError("Error", context={"foo": "bar"})
        repr_str = repr(exc)

        assert "SlackGFMError" in repr_str
        assert "'Error'" in repr_str
        assert "'foo': 'bar'" in repr_str

    def test_exception_is_catchable(self):
        """Test that exception can be caught."""
        with pytest.raises(SlackGFMError) as exc_info:
            raise SlackGFMError("test error")

        assert exc_info.value.message == "test error"


class TestParseError:
    """Test ParseError exception."""

    def test_parse_error_inherits_from_base(self):
        """Test that ParseError inherits from SlackGFMError."""
        exc = ParseError("Parse failed")

        assert isinstance(exc, SlackGFMError)
        assert isinstance(exc, ParseError)
        assert exc.message == "Parse failed"

    def test_parse_error_with_element_context(self):
        """Test ParseError with element context."""
        context = {
            "element": {"type": "rich_text_unknown"},
            "parent": "rich_text_section",
            "position": 10,
        }
        exc = ParseError("Unknown element type", context=context)

        assert exc.message == "Unknown element type"
        assert exc.context["element"]["type"] == "rich_text_unknown"
        assert "rich_text_unknown" in str(exc)

    def test_catch_specific_parse_error(self):
        """Test catching specific ParseError."""
        with pytest.raises(ParseError):
            raise ParseError("Invalid syntax")

    def test_catch_as_base_exception(self):
        """Test catching ParseError as base SlackGFMError."""
        with pytest.raises(SlackGFMError):
            raise ParseError("Invalid syntax")


class TestRenderError:
    """Test RenderError exception."""

    def test_render_error_inherits_from_base(self):
        """Test that RenderError inherits from SlackGFMError."""
        exc = RenderError("Render failed")

        assert isinstance(exc, SlackGFMError)
        assert isinstance(exc, RenderError)

    def test_render_error_with_node_context(self):
        """Test RenderError with AST node context."""
        context = {
            "node_type": "Link",
            "missing_field": "url",
            "node": "Link(url=None, text='example')",
        }
        exc = RenderError("Missing required attribute", context=context)

        assert "Link" in str(exc)
        assert "url" in str(exc)

    def test_catch_specific_render_error(self):
        """Test catching specific RenderError."""
        with pytest.raises(RenderError):
            raise RenderError("Cannot render")


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_inherits_from_base(self):
        """Test that ValidationError inherits from SlackGFMError."""
        exc = ValidationError("Validation failed")

        assert isinstance(exc, SlackGFMError)
        assert isinstance(exc, ValidationError)

    def test_validation_error_with_field_context(self):
        """Test ValidationError with field validation context."""
        context = {
            "field": "elements",
            "expected_type": "list",
            "actual_type": "str",
            "value": "not a list",
        }
        exc = ValidationError("Type mismatch", context=context)

        assert "elements" in str(exc)
        assert "list" in str(exc)

    def test_catch_specific_validation_error(self):
        """Test catching specific ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid data")


class TestTransformError:
    """Test TransformError exception."""

    def test_transform_error_inherits_from_base(self):
        """Test that TransformError inherits from SlackGFMError."""
        exc = TransformError("Transform failed")

        assert isinstance(exc, SlackGFMError)
        assert isinstance(exc, TransformError)

    def test_transform_error_with_visitor_context(self):
        """Test TransformError with visitor context."""
        context = {
            "visitor": "MyCustomVisitor",
            "node_type": "Text",
            "method": "visit_Text",
            "original_error": "ValueError: oops",
        }
        exc = TransformError("Visitor raised exception", context=context)

        assert "MyCustomVisitor" in str(exc)
        assert "Text" in str(exc)
        assert "oops" in str(exc)

    def test_catch_specific_transform_error(self):
        """Test catching specific TransformError."""
        with pytest.raises(TransformError):
            raise TransformError("Transformation failed")


class TestExceptionHierarchy:
    """Test exception hierarchy and catching."""

    def test_catch_all_library_exceptions(self):
        """Test catching all library exceptions with base class."""
        exceptions = [
            ParseError("parse"),
            RenderError("render"),
            ValidationError("validate"),
            TransformError("transform"),
        ]

        for exc in exceptions:
            with pytest.raises(SlackGFMError):
                raise exc

    def test_exception_types_are_distinct(self):
        """Test that exception types are distinguishable."""
        parse_exc = ParseError("parse")
        render_exc = RenderError("render")

        assert type(parse_exc) is not type(render_exc)
        assert isinstance(parse_exc, ParseError)
        assert not isinstance(parse_exc, RenderError)

    def test_selective_exception_catching(self):
        """Test catching specific exception types."""

        def might_fail(error_type: str) -> None:
            if error_type == "parse":
                raise ParseError("parse failed")
            elif error_type == "render":
                raise RenderError("render failed")

        # Catch specific type
        with pytest.raises(ParseError):
            might_fail("parse")

        with pytest.raises(RenderError):
            might_fail("render")


class TestExceptionUsagePatterns:
    """Test realistic exception usage patterns."""

    def test_exception_with_empty_context(self):
        """Test that empty context dict works correctly."""
        exc = SlackGFMError("error", context={})

        assert exc.context == {}
        assert str(exc) == "error"

    def test_exception_with_none_context(self):
        """Test that None context becomes empty dict."""
        exc = SlackGFMError("error", context=None)

        assert exc.context == {}

    def test_exception_with_complex_context(self):
        """Test exception with complex nested context."""
        context = {
            "input": {"type": "rich_text", "elements": [...]},
            "error_location": {"line": 5, "column": 12},
            "suggestions": ["check type field", "verify elements array"],
        }
        exc = ParseError("Invalid structure", context=context)

        assert len(exc.context) == 3
        assert "input" in exc.context
        assert exc.context["error_location"]["line"] == 5

    def test_re_raising_with_additional_context(self):
        """Test re-raising exception with additional context."""
        try:
            raise ParseError("Inner error", context={"level": "inner"})
        except ParseError as e:
            # Re-raise with additional context
            new_context = {**e.context, "level": "outer", "wrapped": True}
            with pytest.raises(ParseError) as exc_info:
                raise ParseError(f"Outer: {e.message}", context=new_context) from None

            assert exc_info.value.context["level"] == "outer"
            assert exc_info.value.context["wrapped"] is True
