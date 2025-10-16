# slack-gfm Library Design Document

**Version**: 0.2.0 (TDD Rewrite)
**Status**: Design Phase
**Date**: 2025-10-12

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [AST (Abstract Syntax Tree)](#ast-abstract-syntax-tree)
4. [Parsers](#parsers)
5. [Renderers](#renderers)
6. [Transformers](#transformers)
7. [Exception Handling](#exception-handling)
8. [New Features](#new-features)
9. [API Design](#api-design)
10. [Implementation Order](#implementation-order)

---

## Overview

### Goals

Convert between three text formats with perfect fidelity:
- **Slack Rich Text** (JSON structure) ↔ **GitHub Flavored Markdown** (GFM)
- **Slack Mrkdwn** (legacy text format) → **GFM**

### Key Requirements

1. **Lossless round-trip**: Rich Text → GFM → Rich Text preserves all data
2. **Accurate AST**: Enable future format conversions (Jira, etc.)
3. **Context-aware parsing**: Different rules inside/outside code blocks
4. **Robust error handling**: Optional exceptions for production use
5. **Extensibility**: Easy to add new formats and transformations

---

## Architecture

### High-Level Flow

```
┌─────────────────┐
│  Input Format   │
│  (Rich Text,    │
│   mrkdwn, GFM)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Parser      │
│  (Format-aware) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Common AST    │◄───────┐
│  (dataclasses)  │        │
└────────┬────────┘        │
         │                 │
         ▼                 │
┌─────────────────┐        │
│  Transformers   │        │
│  (ID mapping,   │────────┘
│   visitors)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Renderer     │
│ (Visitor-based) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Output Format   │
│  (GFM, Rich     │
│   Text)         │
└─────────────────┘
```

### Key Design Patterns

1. **Visitor Pattern**: For AST traversal (renderers, transformers, printer)
2. **State Machine**: For context-aware mrkdwn parsing
3. **Dataclasses**: For immutable AST nodes
4. **Functional Core, Imperative Shell**: Pure functions for transformations

---

## AST (Abstract Syntax Tree)

### Node Hierarchy

The AST uses Python dataclasses with full type hints:

```python
@dataclass(frozen=True)
class Node:
    """Base class for all AST nodes."""
    pass

# Block-level nodes (can contain other blocks or inlines)
@dataclass(frozen=True)
class BlockNode(Node):
    children: list[AnyNode] = field(default_factory=list)

@dataclass(frozen=True)
class Document(BlockNode):
    """Root node containing all content."""
    pass

@dataclass(frozen=True)
class Paragraph(BlockNode):
    """Paragraph containing inline elements."""
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Heading(BlockNode):
    level: int  # 1-6
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class CodeBlock(BlockNode):
    content: str  # Raw text content
    language: str | None = None

@dataclass(frozen=True)
class Quote(BlockNode):
    """Blockquote containing blocks."""
    children: list[BlockNode] = field(default_factory=list)

@dataclass(frozen=True)
class List(BlockNode):
    ordered: bool
    children: list[ListItem] = field(default_factory=list)

@dataclass(frozen=True)
class ListItem(BlockNode):
    """List item can contain inline or block elements."""
    children: list[InlineNode | BlockNode] = field(default_factory=list)

# Inline nodes (text and formatting)
@dataclass(frozen=True)
class InlineNode(Node):
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Text(InlineNode):
    text: str
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Bold(InlineNode):
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Italic(InlineNode):
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Strikethrough(InlineNode):
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Code(InlineNode):
    """Inline code span."""
    content: str
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Link(InlineNode):
    url: str
    text: str | None = None
    children: list[InlineNode] = field(default_factory=list)

# Slack-specific nodes
@dataclass(frozen=True)
class UserMention(InlineNode):
    user_id: str
    username: str | None = None
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class ChannelMention(InlineNode):
    channel_id: str
    channel_name: str | None = None
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class UsergroupMention(InlineNode):
    usergroup_id: str
    usergroup_name: str | None = None
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Broadcast(InlineNode):
    range: str  # "here", "channel", "everyone"
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class Emoji(InlineNode):
    name: str
    unicode: str | None = None
    children: list[InlineNode] = field(default_factory=list)

@dataclass(frozen=True)
class DateTimestamp(InlineNode):
    timestamp: int
    format: str | None = None
    fallback: str | None = None
    children: list[InlineNode] = field(default_factory=list)
```

### Design Rationale

- **Frozen dataclasses**: Immutable by default, safer for concurrent use
- **Type hints**: Full Python 3.12+ type annotations for IDE support
- **Optional fields**: Use `None` defaults for optional data
- **Children lists**: Consistent structure for tree traversal

---

## Parsers

### 1. Rich Text Parser

**Status**: Mostly keep existing logic (it's straightforward)

**Approach**: Recursive descent through JSON structure

```python
def parse_rich_text(data: dict | list) -> Document:
    """Parse Slack Rich Text JSON to AST.

    Args:
        data: Either a rich_text block dict or elements array

    Returns:
        Document node with parsed content

    Raises:
        ParseError: If JSON structure is invalid
    """
    if isinstance(data, list):
        # Direct elements array
        blocks = [_parse_element(elem) for elem in data]
    elif data.get("type") == "rich_text":
        # Full rich_text block
        blocks = [_parse_element(elem) for elem in data.get("elements", [])]
    else:
        raise ParseError(f"Expected rich_text block or elements array, got: {data.get('type')}")

    return Document(children=blocks)


def _parse_element(elem: dict) -> BlockNode:
    """Parse a single rich text element."""
    elem_type = elem.get("type")

    if elem_type == "rich_text_section":
        return _parse_section(elem)
    elif elem_type == "rich_text_preformatted":
        return _parse_preformatted(elem)
    elif elem_type == "rich_text_quote":
        return _parse_quote(elem)
    elif elem_type == "rich_text_list":
        return _parse_list(elem)
    else:
        raise ParseError(f"Unknown element type: {elem_type}")


def _parse_inline_element(elem: dict) -> InlineNode:
    """Parse inline element (text, link, mention, etc.)."""
    elem_type = elem.get("type")

    if elem_type == "text":
        text = elem.get("text", "")
        style = elem.get("style", {})

        # Build nested structure for styles
        node: InlineNode = Text(text=text)

        if style.get("code"):
            node = Code(content=text)
        if style.get("bold"):
            node = Bold(children=[node])
        if style.get("italic"):
            node = Italic(children=[node])
        if style.get("strike"):
            node = Strikethrough(children=[node])

        return node

    elif elem_type == "link":
        url = elem.get("url", "")
        text = elem.get("text")
        return Link(url=url, text=text)

    elif elem_type == "user":
        user_id = elem.get("user_id", "")
        return UserMention(user_id=user_id)

    # ... handle other types
```

**Key improvements from v0.1.0**:
- Proper error handling with ParseError
- Better handling of inline elements in preformatted blocks
- Convert links/mentions to plain text in code blocks

---

### 2. Mrkdwn Parser (STATE MACHINE)

**Status**: Complete rewrite with state machine

**Problem with v0.1.0**: Split-then-parse approach couldn't handle context-dependent rules

**New Approach**: Single-pass state machine tokenizer

#### State Machine Design

```python
from enum import Enum, auto
from dataclasses import dataclass

class State(Enum):
    """Parser states."""
    OUTSIDE_CODE_BLOCK = auto()
    IN_CODE_BLOCK = auto()


@dataclass
class Token:
    """Token produced by tokenizer."""
    type: str  # "text", "bold_marker", "code_block_start", etc.
    content: str
    pos: int  # Position in input


class MrkdwnTokenizer:
    """State machine tokenizer for mrkdwn format."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)
        self.state = State.OUTSIDE_CODE_BLOCK
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """Tokenize input into list of tokens."""
        while self.pos < self.length:
            if self.state == State.OUTSIDE_CODE_BLOCK:
                self._tokenize_outside()
            elif self.state == State.IN_CODE_BLOCK:
                self._tokenize_inside()

        return self.tokens

    def _tokenize_outside(self) -> None:
        """Tokenize when outside code blocks.

        Rules:
        - ``` starts code block → transition to IN_CODE_BLOCK
        - <url> → parse as link, strip angle brackets
        - <@USER> → parse as user mention
        - <#CHANNEL> → parse as channel mention
        - <!broadcast> → parse as broadcast
        - *text* → parse as bold
        - _text_ → parse as italic
        - ~text~ → parse as strikethrough
        - `text` → parse as inline code
        """
        # Check for code block start
        if self.text[self.pos:self.pos+3] == "```":
            self.tokens.append(Token("code_block_start", "```", self.pos))
            self.pos += 3
            self.state = State.IN_CODE_BLOCK
            return

        # Check for link <url|text> or <url>
        if self.text[self.pos] == "<":
            self._parse_angle_bracket_content()
            return

        # Check for bold *text*
        if self.text[self.pos] == "*" and not self._is_escaped():
            self._parse_bold()
            return

        # ... handle other markers

        # Regular text
        self._parse_text()

    def _tokenize_inside(self) -> None:
        """Tokenize when inside code blocks.

        Rules:
        - ``` ends code block → transition to OUTSIDE_CODE_BLOCK
        - <url> → strip angle brackets, treat as literal text
        - Everything else → literal text (no formatting)
        """
        # Check for code block end
        if self.text[self.pos:self.pos+3] == "```":
            self.tokens.append(Token("code_block_end", "```", self.pos))
            self.pos += 3
            self.state = State.OUTSIDE_CODE_BLOCK
            return

        # Check for <url> and strip brackets
        if self.text[self.pos] == "<":
            url = self._extract_url()
            if url:
                # Strip angle brackets, keep URL as text
                self.tokens.append(Token("text", url, self.pos))
                return

        # Everything else is literal text
        self._parse_literal_text()

    def _parse_angle_bracket_content(self) -> None:
        """Parse content between < > based on context."""
        # <http://example.com> or <http://example.com|text>
        # <@USER_ID> or <@USER_ID|name>
        # <#CHANNEL_ID> or <#CHANNEL_ID|name>
        # <!here> or <!channel> or <!everyone>
        pass

    def _extract_url(self) -> str | None:
        """Extract URL from <url> if present."""
        if not self.text[self.pos] == "<":
            return None

        # Find closing >
        end = self.text.find(">", self.pos)
        if end == -1:
            return None

        content = self.text[self.pos+1:end]

        # Check if it looks like a URL
        if content.startswith("http://") or content.startswith("https://"):
            self.pos = end + 1
            return content  # URL without brackets

        return None
```

#### Why State Machine?

**Advantages**:
1. **Context-aware**: Different rules inside/outside code blocks
2. **Single-pass**: More efficient than multiple passes
3. **Predictable**: State transitions are explicit and testable
4. **Maintainable**: Easy to add new states or rules
5. **Robust**: Handles edge cases (nested markers, escaping, etc.)

**Example**:

```
Input: "text *bold* ```code <url>``` *bold*"

Tokens (with states):
┌─────────────┬────────────────────┬───────────────────┐
│ State       │ Input              │ Token             │
├─────────────┼────────────────────┼───────────────────┤
│ OUTSIDE     │ "text "            │ text("text ")     │
│ OUTSIDE     │ "*"                │ bold_start("*")   │
│ OUTSIDE     │ "bold"             │ text("bold")      │
│ OUTSIDE     │ "*"                │ bold_end("*")     │
│ OUTSIDE     │ " "                │ text(" ")         │
│ OUTSIDE     │ "```"              │ code_block_start  │
│ IN_CODE     │ "code "            │ text("code ")     │
│ IN_CODE     │ "<url>"            │ text("url")       │ ← brackets stripped!
│ IN_CODE     │ "```"              │ code_block_end    │
│ OUTSIDE     │ " "                │ text(" ")         │
│ OUTSIDE     │ "*"                │ bold_start("*")   │
│ OUTSIDE     │ "bold"             │ text("bold")      │
│ OUTSIDE     │ "*"                │ bold_end("*")     │
└─────────────┴────────────────────┴───────────────────┘
```

#### Building AST from Tokens

```python
def parse_mrkdwn(text: str) -> Document:
    """Parse mrkdwn string to AST."""
    tokenizer = MrkdwnTokenizer(text)
    tokens = tokenizer.tokenize()

    parser = MrkdwnParser(tokens)
    return parser.parse()


class MrkdwnParser:
    """Build AST from token stream."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Document:
        """Parse tokens into Document."""
        blocks: list[BlockNode] = []

        while self.pos < len(self.tokens):
            block = self._parse_block()
            if block:
                blocks.append(block)

        return Document(children=blocks)

    def _parse_block(self) -> BlockNode | None:
        """Parse a block-level element."""
        token = self.current_token()

        if token.type == "code_block_start":
            return self._parse_code_block()
        elif token.type == "newline":
            # Multiple newlines = paragraph break
            return self._parse_paragraph()
        # ... handle other block types

    def _parse_code_block(self) -> CodeBlock:
        """Parse code block from tokens."""
        self.advance()  # Skip ```

        content_tokens = []
        while self.current_token().type != "code_block_end":
            content_tokens.append(self.current_token())
            self.advance()

        self.advance()  # Skip closing ```

        # Combine text tokens
        content = "".join(t.content for t in content_tokens)

        return CodeBlock(content=content)
```

---

### 3. GFM Parser

**Status**: Keep existing (uses markdown-it-py)

**Approach**: Wrap markdown-it-py and convert to our AST

```python
from markdown_it import MarkdownIt

def parse_gfm(text: str) -> Document:
    """Parse GitHub Flavored Markdown to AST.

    Uses markdown-it-py for parsing, then converts tokens to our AST.
    """
    md = MarkdownIt("gfm-like")
    tokens = md.parse(text)

    converter = GFMTokenConverter(tokens)
    return converter.convert()
```

**Key improvements**:
- Better handling of slack:// URLs
- Support both `slack://user?id=X` and `slack://user?team=Y&id=X`
- Parse link URLs to detect Slack-specific elements

---

## Renderers

### Visitor-Based Architecture

**Old approach (v0.1.0)**: Manual recursion in renderer functions
**New approach (v0.2.0)**: Renderers extend `NodeVisitor` base class

```python
from abc import ABC, abstractmethod
from typing import Any

class NodeVisitor(ABC):
    """Base class for AST visitors.

    Implements the visitor pattern for tree traversal.
    """

    def visit(self, node: Node) -> Any:
        """Visit a node and dispatch to appropriate method."""
        method_name = f"visit_{node.__class__.__name__}"
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node: Node) -> Any:
        """Default visit method for nodes without specific visitor."""
        if hasattr(node, "children"):
            return [self.visit(child) for child in node.children]
        return None

    # Specific visitor methods (to be implemented by subclasses)
    def visit_Document(self, node: Document) -> Any:
        return self.generic_visit(node)

    def visit_Paragraph(self, node: Paragraph) -> Any:
        return self.generic_visit(node)

    # ... one method per node type


class GFMRenderer(NodeVisitor):
    """Render AST to GitHub Flavored Markdown."""

    def __init__(self, team_id: str | None = None):
        self.team_id = team_id
        self.output: list[str] = []

    def render(self, node: Document) -> str:
        """Render document to GFM string."""
        self.output = []
        self.visit(node)
        return "".join(self.output)

    def visit_Document(self, node: Document) -> None:
        """Render document children."""
        for i, child in enumerate(node.children):
            if i > 0:
                self.output.append("\n\n")  # Block separator
            self.visit(child)

    def visit_Paragraph(self, node: Paragraph) -> None:
        """Render paragraph inline elements."""
        for child in node.children:
            self.visit(child)

    def visit_Text(self, node: Text) -> None:
        """Render plain text."""
        self.output.append(node.text)

    def visit_Bold(self, node: Bold) -> None:
        """Render bold: **text**"""
        self.output.append("**")
        for child in node.children:
            self.visit(child)
        self.output.append("**")

    def visit_Italic(self, node: Italic) -> None:
        """Render italic: *text*"""
        self.output.append("*")
        for child in node.children:
            self.visit(child)
        self.output.append("*")

    def visit_CodeBlock(self, node: CodeBlock) -> None:
        """Render code block with language hint."""
        self.output.append("```")
        if node.language:
            self.output.append(node.language)
        self.output.append("\n")
        self.output.append(node.content)
        if not node.content.endswith("\n"):
            self.output.append("\n")
        self.output.append("```")

    def visit_Link(self, node: Link) -> None:
        """Render link: [text](url)"""
        text = node.text or node.url
        self.output.append(f"[{text}]({node.url})")

    def visit_UserMention(self, node: UserMention) -> None:
        """Render user mention as slack:// URL.

        Format: [@username](slack://user?team=X&id=Y)
        or:     [@username](slack://user?id=Y) if no team_id
        """
        username = node.username or node.user_id

        if self.team_id:
            url = f"slack://user?team={self.team_id}&id={node.user_id}"
        else:
            url = f"slack://user?id={node.user_id}"

        if node.username:
            self.output.append(f"[@{username}]({url})")
        else:
            self.output.append(f"[{node.user_id}]({url})")

    def visit_ChannelMention(self, node: ChannelMention) -> None:
        """Render channel mention as slack:// URL."""
        channel_name = node.channel_name or node.channel_id

        if self.team_id:
            url = f"slack://channel?team={self.team_id}&id={node.channel_id}"
        else:
            url = f"slack://channel?id={node.channel_id}"

        if node.channel_name:
            self.output.append(f"[#{channel_name}]({url})")
        else:
            self.output.append(f"[{node.channel_id}]({url})")

    # ... other visit methods


class RichTextRenderer(NodeVisitor):
    """Render AST to Slack Rich Text JSON."""

    def render(self, node: Document) -> dict:
        """Render document to rich_text block."""
        elements = [self.visit(child) for child in node.children]

        return {
            "type": "rich_text",
            "elements": elements
        }

    def visit_Paragraph(self, node: Paragraph) -> dict:
        """Render paragraph as rich_text_section."""
        elements = [self.visit(child) for child in node.children]

        return {
            "type": "rich_text_section",
            "elements": elements
        }

    def visit_CodeBlock(self, node: CodeBlock) -> dict:
        """Render code block as rich_text_preformatted."""
        # Critical: Don't add trailing newline
        content = node.content.rstrip("\n")

        return {
            "type": "rich_text_preformatted",
            "elements": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        }

    def visit_Text(self, node: Text) -> dict:
        """Render text element."""
        return {
            "type": "text",
            "text": node.text
        }

    def visit_Bold(self, node: Bold) -> dict:
        """Render bold text with style."""
        # Combine children text and add style
        child_data = self.visit(node.children[0]) if node.children else {"text": ""}

        if "style" not in child_data:
            child_data["style"] = {}
        child_data["style"]["bold"] = True

        return child_data

    # ... other visit methods
```

### Advantages of Visitor Pattern

1. **Separation of concerns**: Rendering logic separate from AST structure
2. **Extensibility**: Easy to add new renderers (Jira, HTML, etc.)
3. **Composability**: Can combine multiple visitors (render + validate)
4. **Testability**: Each visit method tested independently
5. **Consistency**: All renderers follow same pattern

---

## Transformers

### ID Mapping with Visitors

```python
class IDMapperVisitor(NodeVisitor):
    """Apply ID-to-name mappings for mentions."""

    def __init__(
        self,
        user_map: dict[str, str] | None = None,
        channel_map: dict[str, str] | None = None,
        usergroup_map: dict[str, str] | None = None,
    ):
        self.user_map = user_map or {}
        self.channel_map = channel_map or {}
        self.usergroup_map = usergroup_map or {}

    def visit_UserMention(self, node: UserMention) -> UserMention:
        """Add username from map if available."""
        username = self.user_map.get(node.user_id)
        if username:
            return UserMention(
                user_id=node.user_id,
                username=username,
                children=node.children
            )
        return node

    def visit_ChannelMention(self, node: ChannelMention) -> ChannelMention:
        """Add channel name from map if available."""
        channel_name = self.channel_map.get(node.channel_id)
        if channel_name:
            return ChannelMention(
                channel_id=node.channel_id,
                channel_name=channel_name,
                children=node.children
            )
        return node

    # ... handle other mention types


def apply_id_mappings(
    ast: Document,
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> Document:
    """Apply ID mappings to AST."""
    mapper = IDMapperVisitor(user_map, channel_map, usergroup_map)
    return mapper.visit(ast)
```

### Custom Transformers

Users can write custom visitors:

```python
class MyCustomVisitor(NodeVisitor):
    """Example: Replace all links with plain text."""

    def visit_Link(self, node: Link) -> Text:
        """Replace link with its text."""
        return Text(text=node.text or node.url)


# Usage
ast = parse_rich_text(rich_text)
ast = MyCustomVisitor().visit(ast)
gfm = render_gfm(ast)
```

---

## Exception Handling

### Exception Hierarchy

```python
class SlackGFMError(Exception):
    """Base exception for slack-gfm library."""

    def __init__(self, message: str, context: dict | None = None):
        self.message = message
        self.context = context or {}
        super().__init__(message)


class ParseError(SlackGFMError):
    """Error parsing input format.

    Raised when:
    - Invalid JSON structure
    - Unknown element types
    - Malformed syntax
    """
    pass


class RenderError(SlackGFMError):
    """Error rendering output format.

    Raised when:
    - Invalid AST structure
    - Missing required fields
    - Type mismatches
    """
    pass


class ValidationError(SlackGFMError):
    """Invalid input data.

    Raised when:
    - Required fields missing
    - Invalid field values
    - Constraint violations
    """
    pass


class TransformError(SlackGFMError):
    """Error during AST transformation.

    Raised when:
    - Invalid visitor implementation
    - Transformation produces invalid AST
    """
    pass
```

### API with Exception Control

```python
def rich_text_to_gfm(
    rich_text_data: dict,
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    team_id: str | None = None,
    raise_on_error: bool = False,  # NEW parameter
) -> str:
    """Convert Rich Text to GFM.

    Args:
        rich_text_data: Slack Rich Text JSON
        user_map: User ID to username mapping
        channel_map: Channel ID to name mapping
        team_id: Slack team/workspace ID for deep linking
        raise_on_error: If True, raise exceptions; if False, return best-effort result

    Returns:
        GFM string

    Raises:
        ParseError: If raise_on_error=True and parsing fails
        RenderError: If raise_on_error=True and rendering fails
    """
    try:
        ast = parse_rich_text(rich_text_data)

        if user_map or channel_map:
            ast = apply_id_mappings(ast, user_map, channel_map)

        renderer = GFMRenderer(team_id=team_id)
        return renderer.render(ast)

    except (ParseError, RenderError) as e:
        if raise_on_error:
            raise

        # Best-effort fallback
        logger.warning(f"Conversion failed, using fallback: {e}")
        return _fallback_render(rich_text_data)
```

### Error Context

Exceptions include helpful context:

```python
try:
    ast = parse_rich_text(data)
except ParseError as e:
    print(e.message)
    # "Unknown element type: rich_text_foo"

    print(e.context)
    # {
    #   "element": {"type": "rich_text_foo", ...},
    #   "position": 42,
    #   "parent": "rich_text_section"
    # }
```

---

## New Features

### 1. Deep Linking with team_id

**Purpose**: Generate workspace-specific Slack URLs

```python
# Without team_id (backward compatible)
gfm = rich_text_to_gfm(rich_text)
# Output: [@user](slack://user?id=U123)

# With team_id (new feature)
gfm = rich_text_to_gfm(rich_text, team_id="T12345")
# Output: [@user](slack://user?team=T12345&id=U123)
```

**Format**:
- User: `slack://user?team={TEAM_ID}&id={USER_ID}`
- Channel: `slack://channel?team={TEAM_ID}&id={CHANNEL_ID}`

**Parsing**: Both formats accepted when parsing GFM:
```python
# Both produce the same AST
gfm1 = "[@user](slack://user?id=U123)"
gfm2 = "[@user](slack://user?team=T456&id=U123)"

ast1 = parse_gfm(gfm1)  # UserMention(user_id="U123")
ast2 = parse_gfm(gfm2)  # UserMention(user_id="U123")
```

### 2. AST Printer Visitor

**Purpose**: Debug and visualize AST structure

```python
class ASTPrinter(NodeVisitor):
    """Pretty-print AST structure."""

    def __init__(self, indent: str = "  "):
        self.indent = indent
        self.depth = 0

    def print(self, node: Node) -> str:
        """Print AST as indented tree."""
        self.depth = 0
        lines: list[str] = []
        self._collect_lines(node, lines)
        return "\n".join(lines)

    def _collect_lines(self, node: Node, lines: list[str]) -> None:
        """Recursively collect formatted lines."""
        indent_str = self.indent * self.depth
        node_name = node.__class__.__name__

        # Format node info
        if isinstance(node, Text):
            lines.append(f"{indent_str}{node_name}: {repr(node.text)}")
        elif isinstance(node, CodeBlock):
            lines.append(f"{indent_str}{node_name}:")
            lines.append(f"{indent_str}{self.indent}{repr(node.content)}")
        elif isinstance(node, UserMention):
            lines.append(f"{indent_str}{node_name}(id={node.user_id})")
        else:
            lines.append(f"{indent_str}{node_name}")

        # Recurse into children
        if hasattr(node, "children") and node.children:
            self.depth += 1
            for child in node.children:
                self._collect_lines(child, lines)
            self.depth -= 1


# Usage
from slack_gfm.ast import print_ast

ast = parse_rich_text(rich_text)
print(print_ast(ast))

# Output:
# Document
#   Paragraph
#     Text: 'Hello '
#     Bold
#       Text: 'world'
#   CodeBlock:
#     'print("code")'
```

### 3. Type-Checking Support

Full PEP 484 type hints + `py.typed` marker:

```python
# Library users get type checking
from slack_gfm import rich_text_to_gfm

# mypy knows the types!
result: str = rich_text_to_gfm(data)
```

---

## API Design

### Simple API (80% use case)

```python
from slack_gfm import (
    rich_text_to_gfm,
    gfm_to_rich_text,
    mrkdwn_to_gfm,
)

# Convert Rich Text to GFM
gfm = rich_text_to_gfm(rich_text_data)

# Convert GFM back to Rich Text
rich_text = gfm_to_rich_text(gfm)

# Migrate legacy mrkdwn
gfm = mrkdwn_to_gfm(mrkdwn_text)

# With ID mappings
gfm = rich_text_to_gfm(
    rich_text_data,
    user_map={"U123": "john", "U456": "jane"},
    channel_map={"C789": "general"}
)

# With deep linking
gfm = rich_text_to_gfm(
    rich_text_data,
    team_id="T12345"
)

# With error handling
try:
    gfm = rich_text_to_gfm(data, raise_on_error=True)
except ParseError as e:
    print(f"Parse failed: {e}")
```

### Advanced API (20% use case)

```python
from slack_gfm import (
    parse_rich_text,
    parse_gfm,
    parse_mrkdwn,
    render_gfm,
    render_rich_text,
)
from slack_gfm.ast import NodeVisitor, print_ast

# Parse to AST
ast = parse_rich_text(rich_text_data)

# Print AST for debugging
print(print_ast(ast))

# Custom transformation
class MyVisitor(NodeVisitor):
    def visit_Link(self, node):
        # Custom logic
        return node

ast = MyVisitor().visit(ast)

# Render to format
gfm = render_gfm(ast)
rich_text = render_rich_text(ast)
```

---

## Implementation Order

### Phase 1: Foundation ✅
- [x] Test suite created (81 tests)
- [x] Design documented

### Phase 2: Core Components
1. **Exception classes** (1 hour)
   - Define hierarchy
   - Add context support
   - Write tests

2. **AST refinements** (2 hours)
   - Add missing fields discovered in tests
   - Ensure frozen dataclasses work correctly
   - Add helper methods

3. **Rich Text parser fixes** (2 hours)
   - Handle inline elements in preformatted blocks correctly
   - Fix trailing newline issues
   - Add error handling

### Phase 3: State Machine Parser (CRITICAL)
4. **Mrkdwn tokenizer** (4 hours)
   - Implement State enum
   - Implement MrkdwnTokenizer with state machine
   - Test tokenization separately
   - Handle edge cases (nested markers, escaping)

5. **Mrkdwn parser** (3 hours)
   - Build AST from tokens
   - Handle code blocks correctly
   - Strip angle brackets from URLs in code blocks
   - Test against all mrkdwn test cases

### Phase 4: Visitor-Based Renderers
6. **GFM renderer** (3 hours)
   - Convert to visitor-based
   - Add team_id support
   - Fix code block newline handling
   - Test against all GFM output tests

7. **Rich Text renderer** (2 hours)
   - Convert to visitor-based
   - Fix trailing newline in code blocks
   - Test round-trip conversions

### Phase 5: New Features
8. **AST printer** (1 hour)
   - Implement ASTPrinter visitor
   - Add print_ast() convenience function

9. **Deep linking** (1 hour)
   - Add team_id parameter
   - Update URL generation
   - Update URL parsing

### Phase 6: Polish
10. **Error handling integration** (2 hours)
    - Add raise_on_error parameter
    - Implement fallback strategies
    - Test error scenarios

11. **Documentation** (2 hours)
    - Update README with examples
    - Add migration guide from v0.1.0
    - Document breaking changes

12. **Final testing** (2 hours)
    - Run full test suite
    - Fix any remaining failures
    - Verify 85%+ coverage

**Total estimated time**: ~25 hours of focused work

---

## Success Criteria

✅ All 81 tests passing
✅ Test coverage ≥ 85%
✅ No ruff errors
✅ No mypy errors
✅ Round-trip conversions lossless
✅ Code blocks handle literals correctly
✅ State machine handles edge cases
✅ Visitor pattern implemented consistently
✅ Exception handling optional
✅ Deep linking works
✅ AST printer works

---

## Migration from v0.1.0

### Breaking Changes

1. **API stays the same** (backward compatible)
2. **Behavior changes**:
   - Code blocks now strip angle brackets from URLs
   - Trailing newlines in code blocks fixed
   - Combined formatting (bold+italic) renders correctly
   - Mentions include team_id when provided

### Migration Path

```python
# v0.1.0 code (still works!)
from slack_gfm import rich_text_to_gfm
gfm = rich_text_to_gfm(rich_text)

# v0.2.0 new features (opt-in)
gfm = rich_text_to_gfm(
    rich_text,
    team_id="T12345",  # NEW: deep linking
    raise_on_error=True  # NEW: exception control
)
```

No code changes required for basic use cases! 🎉
