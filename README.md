# slack-gfm

Convert between Slack message formats (Mrkdwn, Rich Text) and GitHub Flavored Markdown with AST manipulation.

## TL;DR - Quick Start

```python
from slack_gfm import rich_text_to_gfm, gfm_to_rich_text, mrkdwn_to_gfm

# Convert Slack Rich Text to GitHub Flavored Markdown
rich_text = {
    "type": "rich_text",
    "elements": [{
        "type": "rich_text_section",
        "elements": [
            {"type": "text", "text": "Hello "},
            {"type": "user", "user_id": "U123ABC"}
        ]
    }]
}

gfm = rich_text_to_gfm(rich_text)
# Result: "Hello [@U123ABC](slack://user?id=U123ABC)"

# Convert back to Rich Text
rich_text = gfm_to_rich_text(gfm)

# Migrate legacy mrkdwn to GFM
mrkdwn = "*Hello* <@U123ABC|john>"
gfm = mrkdwn_to_gfm(mrkdwn)
# Result: "**Hello** [@john](slack://user?id=U123ABC&name=john)"
```

## Installation

```bash
pip install --user slack-gfm
```

Or with uv:

```bash
uv add slack-gfm
```

## Features

- **Rich Text <-> GFM**: Bidirectional conversion with full round-trip support
- **Mrkdwn -> GFM**: Migrate legacy Slack messages
- **ID Mapping**: Map Slack user/channel IDs to display names
- **AST Manipulation**: Transform messages for ML/MCP or custom processing
- **Type Safe**: Full type hints for Python 3.12+

## Usage

### Basic Conversions

```python
from slack_gfm import rich_text_to_gfm, gfm_to_rich_text

# Rich Text -> GFM (most common use case)
gfm_text = rich_text_to_gfm(rich_text_data)

# GFM -> Rich Text (for creating Slack messages)
rich_text = gfm_to_rich_text(gfm_text)
```

### ID Mapping

Map Slack IDs to human-readable names:

```python
from slack_gfm import rich_text_to_gfm

gfm = rich_text_to_gfm(
    rich_text_data,
    user_map={"U123ABC": "john", "U456DEF": "jane"},
    channel_map={"C789GHI": "general"}
)
# User mentions become: [@john](slack://user?id=U123ABC&name=john)
# Channel mentions become: [#general](slack://channel?id=C789GHI&name=general)
```

### Advanced: AST Manipulation

For ML training, MCP context, or custom transformations:

```python
from slack_gfm import parse_rich_text, render_gfm
from slack_gfm.ast import NodeVisitor, transform_ast, UserMention, CodeBlock

# Define custom visitor for ML feature extraction
class MLFeatureExtractor(NodeVisitor):
    def __init__(self):
        self.features = {"users": [], "code_blocks": []}

    def visit_usermention(self, node: UserMention):
        self.features["users"].append(node.user_id)
        return node

    def visit_codeblock(self, node: CodeBlock):
        # Detect JSON in code blocks
        if node.content.strip().startswith("{"):
            self.features["code_blocks"].append({
                "type": "json",
                "content": node.content
            })
        return node

# Parse and extract features
ast = parse_rich_text(rich_text_data)
extractor = MLFeatureExtractor()
ast = transform_ast(ast, extractor)

# Use features for ML
print(extractor.features)
# {"users": ["U123", "U456"], "code_blocks": [{"type": "json", ...}]}

# Still render to GFM
gfm = render_gfm(ast)
```

See [docs/user-guide.md](docs/user-guide.md) for more examples and [docs/api-reference.md](docs/api-reference.md) for complete API documentation.

## How It Works

slack-gfm uses a common Abstract Syntax Tree (AST) to represent formatted text:

```
Slack Rich Text -> Parser -> AST -> Renderer -> GFM
      ^                        |
      |                        v
      +-------- Renderer <- AST <- Parser <- GFM

Slack Mrkdwn -> Parser -> AST -> Renderer -> GFM
```

Slack-specific features (user mentions, channel mentions, broadcasts) are preserved using custom `slack://` URLs in GFM, enabling perfect round-trip conversion.

## Format Differences and Limitations

### Rich Text vs Mrkdwn Whitespace Handling

Slack's two formats handle whitespace differently when converting to GFM:

- **Rich Text**: Preserves literal `\n` characters within paragraphs as they appear in the JSON structure
- **Mrkdwn**: Follows Markdown conventions, converting single newlines to spaces (only double newlines create new paragraphs)

**Example:**

```python
# Rich text with embedded newline
rich_text = {
    "type": "rich_text",
    "elements": [{
        "type": "rich_text_section",
        "elements": [{"type": "text", "text": "Line 1\nLine 2"}]
    }]
}

# Mrkdwn equivalent
mrkdwn = "Line 1\nLine 2"

# Converting to GFM produces slightly different results:
rich_text_to_gfm(rich_text)  # "Line 1\nLine 2" (preserves newline)
mrkdwn_to_gfm(mrkdwn)        # "Line 1 Line 2" (converts to space)
```

Both render identically in most Markdown viewers (single newlines don't create line breaks), but the raw GFM strings differ. This is expected behavior, not a bug.

### Slack Compose Bar Elements

This library has been tested against real Slack messages using all 9 compose bar formatting elements:

1. **Bold** - `*bold*` (mrkdwn) or `{"style": {"bold": true}}` (rich text)
2. **Italic** - `_italic_` (mrkdwn) or `{"style": {"italic": true}}` (rich text)
3. **Strikethrough** - `~strike~` (mrkdwn) or `{"style": {"strike": true}}` (rich text)
4. **Inline Code** - `` `code` `` (mrkdwn) or `{"style": {"code": true}}` (rich text)
5. **Code Block** - ```` ```code``` ```` (mrkdwn) or `{"type": "rich_text_preformatted"}` (rich text)
6. **Links** - `<url|text>` (mrkdwn) or `{"type": "link"}` (rich text)
7. **Quotes** - `&gt; quote` (mrkdwn) or `{"type": "rich_text_quote"}` (rich text)
8. **Bullet Lists** - `• item` (mrkdwn) or `{"type": "rich_text_list", "style": "bullet"}` (rich text)
9. **Numbered Lists** - `1. item` (mrkdwn) or `{"type": "rich_text_list", "style": "ordered"}` (rich text)

All elements convert correctly to GFM and support round-trip conversion.

## Development

```bash
# Clone the repository
git clone https://github.com/retcheverry/slack-gfm.git
cd slack-gfm

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=slack_gfm --cov-report=html
```

## Requirements

- Python 3.12+
- markdown-it-py >= 3.0.0

## License

AGPL-3.0-or-later

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Links

- [Documentation](docs/)
- [API Reference](docs/api-reference.md)
- [User Guide](docs/user-guide.md)
- [GitHub Repository](https://github.com/retcheverry/slack-gfm)
- [PyPI Package](https://pypi.org/project/slack-gfm/)
