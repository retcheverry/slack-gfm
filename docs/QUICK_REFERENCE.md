# Quick Reference - slack-gfm v0.2.0

## State Machine for Mrkdwn Parser

```python
States: OUTSIDE_CODE_BLOCK, IN_CODE_BLOCK

Transitions:
  OUTSIDE --[```]--> IN_CODE_BLOCK
  IN_CODE_BLOCK --[```]--> OUTSIDE

Rules by State:
  OUTSIDE_CODE_BLOCK:
    - <url> → parse as link, STRIP angle brackets
    - <@USER> → user mention
    - <#CHANNEL> → channel mention
    - *text* → bold
    - _text_ → italic
    - ~text~ → strikethrough
    - `text` → inline code

  IN_CODE_BLOCK:
    - <url> → STRIP angle brackets, literal text
    - *text* → literal text (no formatting)
    - Everything else → literal text
```

## Visitor Pattern for Renderers

```python
class MyRenderer(NodeVisitor):
    def visit_Document(self, node): ...
    def visit_Paragraph(self, node): ...
    def visit_Bold(self, node): ...
    # ... one method per AST node type

renderer = MyRenderer()
output = renderer.visit(ast)
```

## Exception Hierarchy

```python
SlackGFMError
├── ParseError        # Invalid input format
├── RenderError       # Cannot produce output
├── ValidationError   # Invalid data
└── TransformError    # Visitor/transformation failed
```

## Deep Linking URLs

```python
# With team_id:
slack://user?team=T12345&id=U123
slack://channel?team=T12345&id=C456

# Without team_id (backward compatible):
slack://user?id=U123
slack://channel?id=C456
```

## API Examples

### Simple Use
```python
from slack_gfm import rich_text_to_gfm, gfm_to_rich_text

gfm = rich_text_to_gfm(rich_text)
rich_text = gfm_to_rich_text(gfm)
```

### With Mappings
```python
gfm = rich_text_to_gfm(
    rich_text,
    user_map={"U123": "john"},
    channel_map={"C456": "general"},
    team_id="T789"
)
```

### With Error Handling
```python
try:
    gfm = rich_text_to_gfm(data, raise_on_error=True)
except ParseError as e:
    print(f"Failed: {e.message}")
    print(f"Context: {e.context}")
```

### Advanced: Custom Visitor
```python
from slack_gfm import parse_rich_text, render_gfm
from slack_gfm.ast import NodeVisitor

class MyTransformer(NodeVisitor):
    def visit_Link(self, node):
        # Custom transformation
        return node

ast = parse_rich_text(rich_text)
ast = MyTransformer().visit(ast)
gfm = render_gfm(ast)
```

### Debug: Print AST
```python
from slack_gfm.ast import print_ast

ast = parse_rich_text(rich_text)
print(print_ast(ast))
```

## Critical Implementation Details

### Code Block Newlines

**Rich Text → GFM:**
```python
# Input Rich Text:
{"type": "text", "text": "xyz\n"}

# Output GFM (WRONG - v0.1.0):
```
xyz

```  # Extra newline!

# Output GFM (CORRECT - v0.2.0):
```
xyz
```  # No extra newline
```

**Implementation:**
```python
def visit_CodeBlock(self, node: CodeBlock) -> None:
    self.output.append("```\n")
    self.output.append(node.content)
    # Don't add newline if content already ends with one
    if not node.content.endswith("\n"):
        self.output.append("\n")
    self.output.append("```")
```

### Angle Brackets in Code Blocks

**Mrkdwn → GFM:**
```python
# Input mrkdwn:
```
<https://example.com>
```

# Output GFM (WRONG - v0.1.0):
```
<https://example.com>
```

# Output GFM (CORRECT - v0.2.0):
```
https://example.com  # Brackets stripped
```
```

**State Machine Implementation:**
```python
def _tokenize_inside(self):
    """Inside code block."""
    if self.text[self.pos] == "<":
        url = self._extract_url()
        if url:
            # Strip brackets, return URL as text
            self.tokens.append(Token("text", url, self.pos))
            return
    # ... rest of literal text handling
```

## Implementation Order Checklist

- [ ] 1. Exception classes (1h)
- [ ] 2. AST refinements (2h)
- [ ] 3. Rich Text parser fixes (2h)
- [ ] 4. Mrkdwn tokenizer with state machine (4h) ← CRITICAL
- [ ] 5. Mrkdwn parser (3h)
- [ ] 6. GFM renderer (visitor-based) (3h)
- [ ] 7. Rich Text renderer (visitor-based) (2h)
- [ ] 8. AST printer (1h)
- [ ] 9. Deep linking (1h)
- [ ] 10. Error handling integration (2h)
- [ ] 11. Documentation (2h)
- [ ] 12. Final testing (2h)

**Total**: ~25 hours

## Test Success Criteria

- [ ] All 81 tests passing
- [ ] Coverage ≥ 85%
- [ ] No ruff errors
- [ ] No mypy errors
- [ ] test-case-020 validates angle bracket stripping
- [ ] Round-trip tests pass (GFM ↔ Rich Text)
