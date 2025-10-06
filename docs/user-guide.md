# User Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [ID Mapping](#id-mapping)
3. [AST Manipulation](#ast-manipulation)
4. [Advanced Usage](#advanced-usage)

## Quick Start

### Converting Rich Text to GFM

The most common use case - convert Slack Rich Text messages to GFM:

```python
from slack_gfm import rich_text_to_gfm

# Your Slack Rich Text data
rich_text = {
    "type": "rich_text",
    "elements": [{
        "type": "rich_text_section",
        "elements": [
            {"type": "text", "text": "Hello world"}
        ]
    }]
}

# Convert to GFM
gfm = rich_text_to_gfm(rich_text)
print(gfm)  # "Hello world"
```

### Converting GFM back to Rich Text

Create Slack messages from stored GFM:

```python
from slack_gfm import gfm_to_rich_text

gfm = "Hello world"

# Convert to Rich Text for Slack API
rich_text = gfm_to_rich_text(gfm)

# Post to Slack
slack_client.chat_postMessage(
    channel="C123",
    blocks=[rich_text]
)
```

### Migrating Mrkdwn Messages

Convert legacy mrkdwn format to GFM:

```python
from slack_gfm import mrkdwn_to_gfm

# Old mrkdwn message
mrkdwn = "*Hello* _world_ ~test~"

# Convert to GFM
gfm = mrkdwn_to_gfm(mrkdwn)
print(gfm)  # "**Hello** *world* ~~test~~"
```

## ID Mapping

### Using Dictionaries for Simple Mapping

Map Slack IDs to display names for better readability:

```python
from slack_gfm import rich_text_to_gfm

rich_text = {
    "type": "rich_text",
    "elements": [{
        "type": "rich_text_section",
        "elements": [
            {"type": "text", "text": "Hey "},
            {"type": "user", "user_id": "U123ABC"},
            {"type": "text", "text": ", check "},
            {"type": "channel", "channel_id": "C456DEF"}
        ]
    }]
}

# Provide ID mappings
gfm = rich_text_to_gfm(
    rich_text,
    user_map={"U123ABC": "john"},
    channel_map={"C456DEF": "general"}
)

print(gfm)
# "Hey [@john](slack://user?id=U123ABC&name=john), check [#general](slack://channel?id=C456DEF&name=general)"
```

### Building Maps from Slack API

```python
from slack_gfm import rich_text_to_gfm

# Fetch user info from Slack
def build_user_map(user_ids, slack_client):
    user_map = {}
    for user_id in user_ids:
        user_info = slack_client.users_info(user=user_id)
        user_map[user_id] = user_info["user"]["name"]
    return user_map

# Extract user IDs from message
user_ids = extract_user_ids(rich_text)
user_map = build_user_map(user_ids, slack_client)

# Convert with mapping
gfm = rich_text_to_gfm(rich_text, user_map=user_map)
```

## AST Manipulation

### Using Visitor Pattern for Custom Transformations

For complex scenarios, manipulate the AST directly:

```python
from slack_gfm import parse_rich_text, render_gfm
from slack_gfm.ast import NodeVisitor, transform_ast, UserMention

class UserLookup(NodeVisitor):
    """Look up usernames from API."""

    def __init__(self, slack_client):
        self.slack_client = slack_client

    def visit_usermention(self, node: UserMention):
        # Call Slack API to get username
        user_info = self.slack_client.users_info(user=node.user_id)
        node.username = user_info["user"]["name"]
        return node

# Parse Rich Text to AST
ast = parse_rich_text(rich_text_data)

# Apply visitor
visitor = UserLookup(slack_client)
ast = transform_ast(ast, visitor)

# Render to GFM
gfm = render_gfm(ast)
```

### Extracting Features for ML Training

```python
from slack_gfm import parse_rich_text
from slack_gfm.ast import NodeVisitor, transform_ast
from slack_gfm.ast import UserMention, ChannelMention, CodeBlock, Link

class FeatureExtractor(NodeVisitor):
    """Extract ML features from messages."""

    def __init__(self):
        self.features = {
            "mentions": [],
            "code_blocks": [],
            "links": [],
            "is_json": False
        }

    def visit_usermention(self, node: UserMention):
        self.features["mentions"].append({
            "type": "user",
            "id": node.user_id,
            "context": "high"  # User mentions are important context
        })
        return node

    def visit_channelmention(self, node: ChannelMention):
        self.features["mentions"].append({
            "type": "channel",
            "id": node.channel_id,
            "context": "medium"
        })
        return node

    def visit_codeblock(self, node: CodeBlock):
        content = node.content.strip()

        # Detect JSON
        if content.startswith("{") or content.startswith("["):
            self.features["is_json"] = True
            self.features["code_blocks"].append({
                "type": "json",
                "language": node.language,
                "content": content
            })
        else:
            self.features["code_blocks"].append({
                "type": "code",
                "language": node.language,
                "content": content
            })
        return node

    def visit_link(self, node: Link):
        self.features["links"].append({
            "url": node.url,
            "is_external": not node.url.startswith("slack://")
        })
        return node

# Use the extractor
ast = parse_rich_text(rich_text_data)
extractor = FeatureExtractor()
ast = transform_ast(ast, extractor)

# Features are now available
print(extractor.features)
# {
#     "mentions": [{"type": "user", "id": "U123", "context": "high"}],
#     "code_blocks": [{"type": "json", "language": None, "content": "..."}],
#     "links": [{"url": "https://...", "is_external": True}],
#     "is_json": True
# }

# Use for ML
model.predict(message_text, context=extractor.features)
```

### Modifying Messages

```python
from slack_gfm import parse_rich_text, render_rich_text
from slack_gfm.ast import NodeVisitor, transform_ast, Text

class ProfanityFilter(NodeVisitor):
    """Replace profanity in messages."""

    def __init__(self, bad_words):
        self.bad_words = bad_words

    def visit_text(self, node: Text):
        for word in self.bad_words:
            node.content = node.content.replace(word, "***")
        return node

# Filter message
ast = parse_rich_text(rich_text_data)
filter_visitor = ProfanityFilter(["badword1", "badword2"])
ast = transform_ast(ast, filter_visitor)

# Convert back to Rich Text for Slack
filtered_rich_text = render_rich_text(ast)
```

## Advanced Usage

### Working with Elements Array Directly

```python
from slack_gfm import rich_text_to_gfm

# Sometimes you only have the elements array
elements = [
    {
        "type": "rich_text_section",
        "elements": [{"type": "text", "text": "Hello"}]
    }
]

# slack-gfm accepts both full blocks and elements arrays
gfm = rich_text_to_gfm(elements)
```

### Combining Multiple Transformations

```python
from slack_gfm import parse_rich_text, render_gfm
from slack_gfm.ast import transform_ast
from slack_gfm.transformers import IDMapper

# Parse once
ast = parse_rich_text(rich_text_data)

# Apply multiple transformers
ast = transform_ast(ast, IDMapper(user_map=user_map))
ast = transform_ast(ast, FeatureExtractor())
ast = transform_ast(ast, ProfanityFilter(bad_words))

# Render once
gfm = render_gfm(ast)
```

### Custom Slack URL Handling

If you need different URL format for Slack mentions:

```python
from slack_gfm import parse_rich_text
from slack_gfm.ast import NodeVisitor, transform_ast, UserMention, Link, Text
from slack_gfm.renderers import render_gfm

class CustomSlackURLs(NodeVisitor):
    """Convert Slack mentions to custom format."""

    def visit_usermention(self, node: UserMention):
        # Convert to plain text link
        display = f"@{node.username}" if node.username else f"@user-{node.user_id}"
        url = f"https://mycompany.slack.com/team/{node.user_id}"
        return Link(url=url, children=[Text(content=display)])

ast = parse_rich_text(rich_text_data)
ast = transform_ast(ast, CustomSlackURLs())
gfm = render_gfm(ast)
```

### Handling Errors

```python
from slack_gfm import rich_text_to_gfm

try:
    gfm = rich_text_to_gfm(rich_text_data)
except Exception as e:
    # Handle parsing errors
    print(f"Failed to convert: {e}")
    # Fall back to plain text
    gfm = extract_plain_text(rich_text_data)
```

## Tips and Best Practices

1. **Use dictionaries for simple mappings**: If you just need to map IDs to names, use `user_map` parameter
2. **Use visitors for complex logic**: For API calls, feature extraction, or modifications, use the visitor pattern
3. **Cache ID mappings**: Build user/channel maps once and reuse them
4. **Parse once, transform many**: If you need multiple transformations, parse to AST once
5. **Round-trip testing**: Test that Rich Text → GFM → Rich Text preserves your data

## Next Steps

- See [API Reference](api-reference.md) for complete function signatures
- Check the [GitHub repository](https://github.com/retcheverry/slack-gfm) for examples
- Review test files for more usage patterns
