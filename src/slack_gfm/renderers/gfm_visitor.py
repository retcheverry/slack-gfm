"""Visitor-based GFM renderer for complex nested styles.

This renderer uses the visitor pattern to properly handle complex combinations
of styles (bold, italic, strikethrough) that can be nested in any order.
"""

from urllib.parse import urlencode

from ..ast import (
    AnyNode,
    Bold,
    Broadcast,
    ChannelMention,
    Code,
    CodeBlock,
    DateTimestamp,
    Document,
    Emoji,
    Heading,
    HorizontalRule,
    Italic,
    Link,
    List,
    ListItem,
    Paragraph,
    Quote,
    Strikethrough,
    Table,
    Text,
    UsergroupMention,
    UserMention,
)
from ..ast.visitor import NodeVisitor


class GFMRenderer(NodeVisitor):
    """Visitor-based GFM renderer.

    Handles complex nested styles by properly tracking style context
    and emitting correct GFM markers.
    """

    def __init__(self) -> None:
        self.output: list[str] = []

    def render(self, node: AnyNode) -> str:
        """Render a node to GFM string."""
        self.output = []
        self.visit(node)
        return "".join(self.output)

    # Block-level nodes

    def visit_document(self, node: Document) -> Document:
        """Render Document node."""
        for i, child in enumerate(node.children):
            self.visit(child)
            # Add double newline between blocks, except after last
            if i < len(node.children) - 1:
                self.output.append("\n\n")
        return node

    def visit_paragraph(self, node: Paragraph) -> Paragraph:
        """Render Paragraph node."""
        for child in node.children:
            self.visit(child)
        return node

    def visit_heading(self, node: Heading) -> Heading:
        """Render Heading node."""
        level = max(1, min(6, node.level))  # Clamp to 1-6
        self.output.append("#" * level + " ")
        for child in node.children:
            self.visit(child)
        return node

    def visit_codeblock(self, node: CodeBlock) -> CodeBlock:
        """Render CodeBlock node."""
        lang = node.language or ""

        # Preserve structure for round-trip consistency:
        # - No newlines: ```xyz```
        # - Single trailing newline: ```xyz\n```
        # - Multiline: Add newlines only if not already present

        if "\n" not in node.content:
            # Inline format (no newlines)
            self.output.append(f"```{lang}{node.content}```")
        elif node.content.count("\n") == 1 and node.content.endswith("\n"):
            # Single trailing newline - content on opening line
            self.output.append(f"```{lang}{node.content}```")
        else:
            # Multiline - add newlines only if not already present
            prefix = "" if node.content.startswith("\n") else "\n"
            suffix = "" if node.content.endswith("\n") else "\n"
            self.output.append(f"```{lang}{prefix}{node.content}{suffix}```")
        return node

    def visit_quote(self, node: Quote) -> Quote:
        """Render Quote node."""
        # Render children and prefix each line with >
        content_parts = []
        for child in node.children:
            # Save current output and render child
            saved_output = self.output
            self.output = []
            self.visit(child)
            child_content = "".join(self.output)
            self.output = saved_output

            # Prefix each line with >
            lines = child_content.split("\n")
            quoted_lines = [f"> {line}" if line else ">" for line in lines]
            content_parts.append("\n".join(quoted_lines))

        self.output.append("\n".join(content_parts))
        return node

    def visit_list(self, node: List) -> List:
        """Render List node."""
        for i, item in enumerate(node.children):
            if node.ordered:
                num = node.start + i
                prefix = f"{num}. "
            else:
                prefix = "- "

            # Render item content
            saved_output = self.output
            self.output = []
            self.visit(item)
            item_content = "".join(self.output)
            self.output = saved_output

            # Handle multiline items
            lines = item_content.split("\n")
            if lines:
                self.output.append(prefix + lines[0])
                if i < len(node.children) - 1 or len(lines) > 1:
                    self.output.append("\n")
                # Indent continuation lines
                for line in lines[1:]:
                    self.output.append("  " + line)
                    if line != lines[-1]:
                        self.output.append("\n")
        return node

    def visit_listitem(self, node: ListItem) -> ListItem:
        """Render ListItem node."""
        for child in node.children:
            self.visit(child)
        return node

    def visit_horizontalrule(self, node: HorizontalRule) -> HorizontalRule:
        """Render HorizontalRule node."""
        self.output.append("---")
        return node

    def visit_table(self, node: Table) -> Table:
        """Render Table node."""
        lines = []

        # Header row
        if node.header:
            saved_output = self.output
            header_cells = []
            for header_cell in node.header:
                self.output = []
                for inline_node in header_cell:
                    self.visit(inline_node)
                header_cells.append("".join(self.output))
            self.output = saved_output
            lines.append("| " + " | ".join(header_cells) + " |")

            # Separator row with alignments
            sep_cells = []
            for align in node.alignments:
                if align == "left":
                    sep_cells.append(":---")
                elif align == "right":
                    sep_cells.append("---:")
                elif align == "center":
                    sep_cells.append(":---:")
                else:
                    sep_cells.append("---")
            lines.append("| " + " | ".join(sep_cells) + " |")

        # Data rows
        saved_output = self.output
        for row in node.rows:
            row_cells_rendered = []
            for cell in row:
                self.output = []
                for inline_node in cell:
                    self.visit(inline_node)
                row_cells_rendered.append("".join(self.output))
            lines.append("| " + " | ".join(row_cells_rendered) + " |")
        self.output = saved_output

        self.output.append("\n".join(lines))
        return node

    # Inline nodes

    def visit_text(self, node: Text) -> Text:
        """Render Text node."""
        # Escape special markdown characters
        content = node.content
        # Escape backslashes first
        content = content.replace("\\", "\\\\")
        # Escape markdown special chars
        for char in ["*", "_", "`", "[", "]", "(", ")", "#", "+", "-", ".", "!", "|"]:
            content = content.replace(char, f"\\{char}")
        self.output.append(content)
        return node

    def visit_bold(self, node: Bold) -> Bold:
        """Render Bold node."""
        self.output.append("**")
        for child in node.children:
            self.visit(child)
        self.output.append("**")
        return node

    def visit_italic(self, node: Italic) -> Italic:
        """Render Italic node."""
        self.output.append("*")
        for child in node.children:
            self.visit(child)
        self.output.append("*")
        return node

    def visit_strikethrough(self, node: Strikethrough) -> Strikethrough:
        """Render Strikethrough node."""
        self.output.append("~~")
        for child in node.children:
            self.visit(child)
        self.output.append("~~")
        return node

    def visit_code(self, node: Code) -> Code:
        """Render inline Code node."""
        # Escape backticks in code content
        content = node.content.replace("`", "\\`")
        self.output.append(f"`{content}`")
        return node

    def visit_link(self, node: Link) -> Link:
        """Render Link node."""
        # Render link text
        saved_output = self.output
        self.output = []
        if node.children:
            for child in node.children:
                self.visit(child)
            text = "".join(self.output)
        else:
            text = node.url
        self.output = saved_output

        # Escape special chars in URL
        url = node.url.replace("(", "%28").replace(")", "%29")
        self.output.append(f"[{text}]({url})")
        return node

    def visit_usermention(self, node: UserMention) -> UserMention:
        """Render UserMention as GFM link with slack:// URL."""
        display = f"@{node.username}" if node.username else node.user_id
        params = {"id": node.user_id}
        if node.username:
            params["name"] = node.username
        url = f"slack://user?{urlencode(params)}"
        self.output.append(f"[{display}]({url})")
        return node

    def visit_channelmention(self, node: ChannelMention) -> ChannelMention:
        """Render ChannelMention as GFM link with slack:// URL."""
        display = f"#{node.channel_name}" if node.channel_name else node.channel_id
        params = {"id": node.channel_id}
        if node.channel_name:
            params["name"] = node.channel_name
        url = f"slack://channel?{urlencode(params)}"
        self.output.append(f"[{display}]({url})")
        return node

    def visit_usergroupmention(self, node: UsergroupMention) -> UsergroupMention:
        """Render UsergroupMention as GFM link with slack:// URL."""
        display = f"@{node.usergroup_name}" if node.usergroup_name else node.usergroup_id
        params = {"id": node.usergroup_id}
        if node.usergroup_name:
            params["name"] = node.usergroup_name
        url = f"slack://usergroup?{urlencode(params)}"
        self.output.append(f"[{display}]({url})")
        return node

    def visit_broadcast(self, node: Broadcast) -> Broadcast:
        """Render Broadcast as GFM link with slack:// URL."""
        display = f"@{node.range}"
        url = f"slack://broadcast?type={node.range}"
        self.output.append(f"[{display}]({url})")
        return node

    def visit_emoji(self, node: Emoji) -> Emoji:
        """Render Emoji."""
        if node.unicode:
            self.output.append(node.unicode)
        else:
            self.output.append(f":{node.name}:")
        return node

    def visit_datetimestamp(self, node: DateTimestamp) -> DateTimestamp:
        """Render DateTimestamp as GFM link with slack:// URL."""
        display = node.fallback or str(node.timestamp)
        params = {"ts": str(node.timestamp)}
        if node.format:
            params["format"] = node.format
        url = f"slack://date?{urlencode(params)}"
        self.output.append(f"[{display}]({url})")
        return node


def render_gfm_visitor(node: AnyNode) -> str:
    """Render an AST node to GFM using visitor pattern.

    Args:
        node: AST node to render

    Returns:
        GFM string
    """
    renderer = GFMRenderer()
    return renderer.render(node)
