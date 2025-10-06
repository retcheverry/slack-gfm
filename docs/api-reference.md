# API Reference

Complete API documentation for slack-gfm.

## Table of Contents

- [Convenience Functions](#convenience-functions)
- [Parsers](#parsers)
- [Renderers](#renderers)
- [Transformers](#transformers)
- [AST Nodes](#ast-nodes)
- [Visitor Pattern](#visitor-pattern)

## Convenience Functions

### `rich_text_to_gfm()`

Convert Slack Rich Text to GitHub Flavored Markdown.

```python
def rich_text_to_gfm(
    rich_text_data: dict[str, Any] | list[dict[str, Any]],
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> str
```

**Parameters:**

- `rich_text_data`: Slack Rich Text JSON (either full block with `"type": "rich_text"` or just the `elements` array)
- `user_map`: Optional dictionary mapping user IDs to usernames
- `channel_map`: Optional dictionary mapping channel IDs to channel names
- `usergroup_map`: Optional dictionary mapping usergroup IDs to usergroup names

**Returns:** GitHub Flavored Markdown string

**Example:**

```python
from slack_gfm import rich_text_to_gfm

rich_text = {
    "type": "rich_text",
    "elements": [{
        "type": "rich_text_section",
        "elements": [
            {"type": "text", "text": "Hello "},
            {"type": "user", "user_id": "U123"}
        ]
    }]
}

gfm = rich_text_to_gfm(rich_text, user_map={"U123": "john"})
# Result: "Hello [@john](slack://user?id=U123&name=john)"
```

### `gfm_to_rich_text()`

Convert GitHub Flavored Markdown to Slack Rich Text.

```python
def gfm_to_rich_text(
    gfm_text: str,
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> dict[str, Any]
```

**Parameters:**

- `gfm_text`: GitHub Flavored Markdown string
- `user_map`: Optional dictionary mapping user IDs to usernames
- `channel_map`: Optional dictionary mapping channel IDs to channel names
- `usergroup_map`: Optional dictionary mapping usergroup IDs to usergroup names

**Returns:** Slack Rich Text JSON block

**Example:**

```python
from slack_gfm import gfm_to_rich_text

gfm = "Hello [@john](slack://user?id=U123&name=john)"
rich_text = gfm_to_rich_text(gfm)

# Result: {
#     "type": "rich_text",
#     "elements": [{
#         "type": "rich_text_section",
#         "elements": [
#             {"type": "text", "text": "Hello "},
#             {"type": "user", "user_id": "U123"}
#         ]
#     }]
# }
```

### `mrkdwn_to_gfm()`

Convert Slack mrkdwn format to GitHub Flavored Markdown.

```python
def mrkdwn_to_gfm(
    mrkdwn_text: str,
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> str
```

**Parameters:**

- `mrkdwn_text`: Slack mrkdwn string
- `user_map`: Optional dictionary mapping user IDs to usernames
- `channel_map`: Optional dictionary mapping channel IDs to channel names
- `usergroup_map`: Optional dictionary mapping usergroup IDs to usergroup names

**Returns:** GitHub Flavored Markdown string

**Example:**

```python
from slack_gfm import mrkdwn_to_gfm

mrkdwn = "*Hello* <@U123|john>"
gfm = mrkdwn_to_gfm(mrkdwn)
# Result: "**Hello** [@john](slack://user?id=U123&name=john)"
```

## Parsers

### `parse_rich_text()`

Parse Slack Rich Text JSON to AST.

```python
def parse_rich_text(
    rich_text_data: dict[str, Any] | list[dict[str, Any]]
) -> Document
```

**Parameters:**

- `rich_text_data`: Slack Rich Text JSON

**Returns:** `Document` AST node

**Example:**

```python
from slack_gfm.parsers import parse_rich_text

ast = parse_rich_text(rich_text_data)
# Returns: Document(children=[Paragraph(...), ...])
```

### `parse_gfm()`

Parse GitHub Flavored Markdown to AST.

```python
def parse_gfm(gfm_text: str) -> Document
```

**Parameters:**

- `gfm_text`: GFM markdown string

**Returns:** `Document` AST node

**Example:**

```python
from slack_gfm.parsers import parse_gfm

ast = parse_gfm("**Hello** world")
# Returns: Document(children=[Paragraph(children=[Bold(...), Text(...)])])
```

### `parse_mrkdwn()`

Parse Slack mrkdwn format to AST.

```python
def parse_mrkdwn(mrkdwn_text: str) -> Document
```

**Parameters:**

- `mrkdwn_text`: Slack mrkdwn string

**Returns:** `Document` AST node

**Example:**

```python
from slack_gfm.parsers import parse_mrkdwn

ast = parse_mrkdwn("*Hello* _world_")
# Returns: Document(children=[Paragraph(children=[Bold(...), Italic(...)])])
```

## Renderers

### `render_gfm()`

Render an AST node to GitHub Flavored Markdown.

```python
def render_gfm(node: AnyNode) -> str
```

**Parameters:**

- `node`: AST node to render (typically a `Document`)

**Returns:** GFM string

**Example:**

```python
from slack_gfm.renderers import render_gfm
from slack_gfm.ast import Document, Paragraph, Text

ast = Document(children=[Paragraph(children=[Text(content="Hello")])])
gfm = render_gfm(ast)
# Result: "Hello"
```

### `render_rich_text()`

Render an AST node to Slack Rich Text JSON.

```python
def render_rich_text(node: AnyNode) -> dict[str, Any]
```

**Parameters:**

- `node`: AST node to render (typically a `Document`)

**Returns:** Rich Text block dict

**Example:**

```python
from slack_gfm.renderers import render_rich_text
from slack_gfm.ast import Document, Paragraph, Text

ast = Document(children=[Paragraph(children=[Text(content="Hello")])])
rich_text = render_rich_text(ast)
# Result: {"type": "rich_text", "elements": [...]}
```

## Transformers

### `apply_id_mappings()`

Apply ID mappings to an AST (convenience function).

```python
def apply_id_mappings(
    ast_node: AnyNode,
    user_map: dict[str, str] | None = None,
    channel_map: dict[str, str] | None = None,
    usergroup_map: dict[str, str] | None = None,
) -> AnyNode
```

**Parameters:**

- `ast_node`: AST node to transform
- `user_map`: Dictionary mapping user IDs to usernames
- `channel_map`: Dictionary mapping channel IDs to names
- `usergroup_map`: Dictionary mapping usergroup IDs to names

**Returns:** Transformed AST node

**Example:**

```python
from slack_gfm.transformers import apply_id_mappings

ast = apply_id_mappings(
    ast,
    user_map={"U123": "john"},
    channel_map={"C456": "general"}
)
```

### `IDMapper`

Visitor class for mapping Slack IDs to display names.

```python
class IDMapper(NodeVisitor):
    def __init__(
        self,
        user_map: dict[str, str] | None = None,
        channel_map: dict[str, str] | None = None,
        usergroup_map: dict[str, str] | None = None,
    )
```

**Parameters:**

- `user_map`: Dictionary mapping user IDs to usernames
- `channel_map`: Dictionary mapping channel IDs to names
- `usergroup_map`: Dictionary mapping usergroup IDs to names

**Example:**

```python
from slack_gfm.transformers import IDMapper
from slack_gfm.ast.visitor import transform_ast

mapper = IDMapper(user_map={"U123": "john"})
ast = transform_ast(ast, mapper)
```

### `CallbackMapper`

Visitor class for applying custom callback functions to nodes.

```python
class CallbackMapper(NodeVisitor):
    def __init__(
        self,
        user_callback: Callable[[UserMention], UserMention] | None = None,
        channel_callback: Callable[[ChannelMention], ChannelMention] | None = None,
        usergroup_callback: Callable[[UsergroupMention], UsergroupMention] | None = None,
    )
```

**Parameters:**

- `user_callback`: Function to transform UserMention nodes
- `channel_callback`: Function to transform ChannelMention nodes
- `usergroup_callback`: Function to transform UsergroupMention nodes

**Example:**

```python
from slack_gfm.transformers import CallbackMapper
from slack_gfm.ast import UserMention

def lookup_user(node: UserMention) -> UserMention:
    user_info = slack_api.users_info(user=node.user_id)
    node.username = user_info["user"]["name"]
    return node

mapper = CallbackMapper(user_callback=lookup_user)
ast = transform_ast(ast, mapper)
```

## AST Nodes

### Document

Root node containing all content blocks.

```python
@dataclass
class Document(Node):
    children: list[BlockNode]
```

### Block Nodes

#### Paragraph

```python
@dataclass
class Paragraph(BlockNode):
    children: list[InlineNode]
```

#### Heading

```python
@dataclass
class Heading(BlockNode):
    level: int  # 1-6
    children: list[InlineNode]
```

#### CodeBlock

```python
@dataclass
class CodeBlock(BlockNode):
    content: str
    language: str | None = None
```

#### Quote

```python
@dataclass
class Quote(BlockNode):
    children: list[BlockNode]
```

#### List

```python
@dataclass
class List(BlockNode):
    ordered: bool
    children: list[ListItem]
    start: int = 1
```

#### ListItem

```python
@dataclass
class ListItem(Node):
    children: list[InlineNode | BlockNode]
```

#### HorizontalRule

```python
@dataclass
class HorizontalRule(BlockNode):
    pass
```

### Inline Nodes

#### Text

```python
@dataclass
class Text(InlineNode):
    content: str
```

#### Bold

```python
@dataclass
class Bold(InlineNode):
    children: list[InlineNode]
```

#### Italic

```python
@dataclass
class Italic(InlineNode):
    children: list[InlineNode]
```

#### Strikethrough

```python
@dataclass
class Strikethrough(InlineNode):
    children: list[InlineNode]
```

#### Code

Inline code.

```python
@dataclass
class Code(InlineNode):
    content: str
```

#### Link

```python
@dataclass
class Link(InlineNode):
    url: str
    children: list[InlineNode]  # Link text
```

#### UserMention

```python
@dataclass
class UserMention(InlineNode):
    user_id: str
    username: str | None = None
```

#### ChannelMention

```python
@dataclass
class ChannelMention(InlineNode):
    channel_id: str
    channel_name: str | None = None
```

#### UsergroupMention

```python
@dataclass
class UsergroupMention(InlineNode):
    usergroup_id: str
    usergroup_name: str | None = None
```

#### Broadcast

```python
@dataclass
class Broadcast(InlineNode):
    type: str  # "here", "channel", "everyone"
```

#### Emoji

```python
@dataclass
class Emoji(InlineNode):
    name: str
    unicode: str | None = None
```

#### DateTimestamp

```python
@dataclass
class DateTimestamp(InlineNode):
    timestamp: int
    format: str | None = None
    fallback: str | None = None
```

## Visitor Pattern

### `NodeVisitor`

Base class for AST visitors.

```python
class NodeVisitor:
    def visit(self, node: AnyNode) -> AnyNode
    def generic_visit(self, node: AnyNode) -> AnyNode

    # Override these methods for custom behavior
    def visit_document(self, node: Document) -> Document
    def visit_paragraph(self, node: Paragraph) -> Paragraph
    def visit_text(self, node: Text) -> Text
    def visit_bold(self, node: Bold) -> Bold
    def visit_usermention(self, node: UserMention) -> UserMention
    # ... and more
```

**Example:**

```python
from slack_gfm.ast import NodeVisitor, UserMention

class MyVisitor(NodeVisitor):
    def visit_usermention(self, node: UserMention):
        # Custom logic here
        node.username = "custom"
        return node
```

### `transform_ast()`

Apply a visitor to transform an AST.

```python
def transform_ast(root: AnyNode, visitor: NodeVisitor) -> AnyNode
```

**Parameters:**

- `root`: Root node of the AST
- `visitor`: Visitor instance to apply

**Returns:** Transformed AST root node

**Example:**

```python
from slack_gfm.ast.visitor import transform_ast

transformed = transform_ast(ast, MyVisitor())
```

## Type Aliases

```python
AnyNode = Node | InlineNode | BlockNode
AnyInline = InlineNode | Text | Bold | Italic | ...
AnyBlock = BlockNode | Paragraph | Heading | CodeBlock | ...
```
