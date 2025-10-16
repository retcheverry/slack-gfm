"""Exception classes for slack-gfm library.

This module defines the exception hierarchy for the slack-gfm library,
providing detailed error information with context for debugging.
"""

from typing import Any


class SlackGFMError(Exception):
    """Base exception for all slack-gfm errors.

    All exceptions raised by this library inherit from this base class,
    making it easy to catch all library-specific errors.

    Attributes:
        message: Human-readable error message
        context: Additional context information for debugging (optional)
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message
            context: Additional context information (position, element type, etc.)
        """
        self.message = message
        self.context = context or {}
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation with context if available."""
        if self.context:
            context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} (context: {context_str})"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"{self.__class__.__name__}({self.message!r}, context={self.context!r})"


class ParseError(SlackGFMError):
    """Error parsing input format.

    Raised when the parser encounters invalid or malformed input that cannot
    be parsed into an AST.

    Common scenarios:
    - Invalid JSON structure in Rich Text
    - Unknown element types
    - Malformed mrkdwn syntax
    - Unexpected token in input stream
    - Missing required fields

    Example:
        >>> try:
        ...     ast = parse_rich_text({"type": "unknown"})
        ... except ParseError as e:
        ...     print(e.message)
        ...     print(e.context)
        Unknown element type: unknown
        {'element': {'type': 'unknown'}, 'parent': 'Document'}
    """

    pass


class RenderError(SlackGFMError):
    """Error rendering output format.

    Raised when the renderer encounters an AST structure that cannot be
    rendered to the target format.

    Common scenarios:
    - Invalid AST node structure
    - Missing required node attributes
    - Type mismatches in node data
    - Unsupported node type for target format
    - Inconsistent AST state

    Example:
        >>> try:
        ...     gfm = render_gfm(invalid_ast)
        ... except RenderError as e:
        ...     print(e.message)
        ...     print(e.context)
        Missing required attribute 'url' on Link node
        {'node_type': 'Link', 'node': Link(...)}
    """

    pass


class ValidationError(SlackGFMError):
    """Invalid input data.

    Raised when input data fails validation checks before parsing or rendering.

    Common scenarios:
    - Required fields missing from input
    - Invalid field values (wrong type, out of range, etc.)
    - Constraint violations (e.g., invalid user ID format)
    - Schema validation failures

    Example:
        >>> try:
        ...     validate_rich_text({"elements": "not a list"})
        ... except ValidationError as e:
        ...     print(e.message)
        ...     print(e.context)
        Field 'elements' must be a list, got str
        {'field': 'elements', 'expected_type': 'list', 'actual_type': 'str'}
    """

    pass


class TransformError(SlackGFMError):
    """Error during AST transformation.

    Raised when a visitor or transformer encounters an error while traversing
    or modifying the AST.

    Common scenarios:
    - Invalid visitor implementation
    - Transformation produces invalid AST structure
    - Visitor method raises unexpected exception
    - AST node type not handled by visitor

    Example:
        >>> class MyVisitor(NodeVisitor):
        ...     def visit_Text(self, node):
        ...         raise ValueError("oops")
        >>> try:
        ...     result = MyVisitor().visit(ast)
        ... except TransformError as e:
        ...     print(e.message)
        ...     print(e.context)
        Visitor raised exception in visit_Text
        {'visitor': 'MyVisitor', 'node_type': 'Text', 'original_error': 'oops'}
    """

    pass


# Export all exception classes
__all__ = [
    "SlackGFMError",
    "ParseError",
    "RenderError",
    "ValidationError",
    "TransformError",
]
