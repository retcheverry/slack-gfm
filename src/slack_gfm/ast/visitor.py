"""Visitor pattern implementation for AST traversal and transformation."""


from .nodes import (
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


class NodeVisitor:
    """Base class for AST visitors.

    Subclass this to implement custom AST transformations. Override visit_* methods
    for specific node types. The generic_visit method is called for nodes without
    a specific visitor method.

    Example:
        class UserMapper(NodeVisitor):
            def __init__(self, user_map: dict[str, str]):
                self.user_map = user_map

            def visit_user_mention(self, node: UserMention) -> UserMention:
                if node.user_id in self.user_map:
                    node.username = self.user_map[node.user_id]
                return node
    """

    def visit(self, node: AnyNode) -> AnyNode:
        """Visit a node and dispatch to the appropriate visit_* method."""
        method_name = f"visit_{node.__class__.__name__.lower()}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: AnyNode) -> AnyNode:
        """Default visitor for nodes without specific visit_* methods.

        Recursively visits all children.
        """
        if hasattr(node, "children") and node.children:
            node.children = [self.visit(child) for child in node.children]
        return node

    # Visitor methods for each node type
    # Override these in subclasses for custom behavior

    def visit_document(self, node: Document) -> Document:
        """Visit a Document node."""
        return self.generic_visit(node)  # type: ignore

    def visit_paragraph(self, node: Paragraph) -> Paragraph:
        """Visit a Paragraph node."""
        return self.generic_visit(node)  # type: ignore

    def visit_heading(self, node: Heading) -> Heading:
        """Visit a Heading node."""
        return self.generic_visit(node)  # type: ignore

    def visit_text(self, node: Text) -> Text:
        """Visit a Text node."""
        return node

    def visit_bold(self, node: Bold) -> Bold:
        """Visit a Bold node."""
        return self.generic_visit(node)  # type: ignore

    def visit_italic(self, node: Italic) -> Italic:
        """Visit an Italic node."""
        return self.generic_visit(node)  # type: ignore

    def visit_strikethrough(self, node: Strikethrough) -> Strikethrough:
        """Visit a Strikethrough node."""
        return self.generic_visit(node)  # type: ignore

    def visit_code(self, node: Code) -> Code:
        """Visit a Code node."""
        return node

    def visit_link(self, node: Link) -> Link:
        """Visit a Link node."""
        return self.generic_visit(node)  # type: ignore

    def visit_usermention(self, node: UserMention) -> UserMention:
        """Visit a UserMention node."""
        return node

    def visit_channelmention(self, node: ChannelMention) -> ChannelMention:
        """Visit a ChannelMention node."""
        return node

    def visit_usergroupmention(self, node: UsergroupMention) -> UsergroupMention:
        """Visit a UsergroupMention node."""
        return node

    def visit_broadcast(self, node: Broadcast) -> Broadcast:
        """Visit a Broadcast node."""
        return node

    def visit_emoji(self, node: Emoji) -> Emoji:
        """Visit an Emoji node."""
        return node

    def visit_datetimestamp(self, node: DateTimestamp) -> DateTimestamp:
        """Visit a DateTimestamp node."""
        return node

    def visit_codeblock(self, node: CodeBlock) -> CodeBlock:
        """Visit a CodeBlock node."""
        return node

    def visit_quote(self, node: Quote) -> Quote:
        """Visit a Quote node."""
        return self.generic_visit(node)  # type: ignore

    def visit_list(self, node: List) -> List:
        """Visit a List node."""
        return self.generic_visit(node)  # type: ignore

    def visit_listitem(self, node: ListItem) -> ListItem:
        """Visit a ListItem node."""
        return self.generic_visit(node)  # type: ignore

    def visit_horizontalrule(self, node: HorizontalRule) -> HorizontalRule:
        """Visit a HorizontalRule node."""
        return node

    def visit_table(self, node: Table) -> Table:
        """Visit a Table node."""
        # Tables have nested structure - visit cells
        if node.header:
            node.header = [[self.visit(cell) for cell in row] for row in node.header]  # type: ignore
        if node.rows:
            node.rows = [
                [[self.visit(cell) for cell in row_cells] for row_cells in row]  # type: ignore
                for row in node.rows
            ]
        return node


def transform_ast(root: AnyNode, visitor: NodeVisitor) -> AnyNode:
    """Transform an AST using the given visitor.

    Args:
        root: Root node of the AST
        visitor: Visitor instance to apply transformations

    Returns:
        Transformed AST root node

    Example:
        >>> from slack_gfm.ast import Document, Paragraph, UserMention
        >>> from slack_gfm.ast.visitor import NodeVisitor, transform_ast
        >>>
        >>> class UserMapper(NodeVisitor):
        ...     def visit_usermention(self, node):
        ...         node.username = "John Doe"
        ...         return node
        >>>
        >>> doc = Document(children=[Paragraph(children=[UserMention(user_id="U123")])])
        >>> transformed = transform_ast(doc, UserMapper())
    """
    return visitor.visit(root)
