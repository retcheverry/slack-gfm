"""AST visitor tests."""

from slack_gfm.ast import (
    Bold,
    Document,
    NodeVisitor,
    Paragraph,
    Text,
    UserMention,
    transform_ast,
)


class TestNodeVisitor:
    """Test NodeVisitor base class."""

    def test_generic_visit(self):
        """Test generic visitor traversal."""
        doc = Document(
            children=[
                Paragraph(children=[Text(content="Hello")]),
                Paragraph(children=[Text(content="World")]),
            ]
        )
        visitor = NodeVisitor()
        result = visitor.visit(doc)
        assert len(result.children) == 2

    def test_visit_specific_node(self):
        """Test visiting specific node type."""
        from dataclasses import replace

        class TextUpperVisitor(NodeVisitor):
            def visit_text(self, node):
                # Use replace() since nodes are frozen
                return replace(node, content=node.content.upper())

        doc = Document(children=[Paragraph(children=[Text(content="hello")])])
        visitor = TextUpperVisitor()
        result = visitor.visit(doc)
        text = result.children[0].children[0]
        assert text.content == "HELLO"

    def test_visit_nested_nodes(self):
        """Test visiting nested nodes."""
        from dataclasses import replace

        class BoldTextVisitor(NodeVisitor):
            def visit_bold(self, node):
                # Process children - use generic_visit which handles immutability
                return self.generic_visit(node)

            def visit_text(self, node):
                if hasattr(node, "content"):
                    # Use replace() since nodes are frozen
                    return replace(node, content=node.content + "!")
                return node

        doc = Document(children=[Paragraph(children=[Bold(children=[Text(content="bold")])])])
        visitor = BoldTextVisitor()
        result = visitor.visit(doc)
        text = result.children[0].children[0].children[0]
        assert text.content == "bold!"

    def test_transform_ast_function(self):
        """Test transform_ast helper function."""
        from dataclasses import replace

        class AppendVisitor(NodeVisitor):
            def visit_text(self, node):
                # Use replace() since nodes are frozen
                return replace(node, content=node.content + " transformed")

        doc = Document(children=[Paragraph(children=[Text(content="original")])])
        result = transform_ast(doc, AppendVisitor())
        text = result.children[0].children[0]
        assert text.content == "original transformed"

    def test_visitor_all_node_types(self):
        """Test visitor can handle all node types."""

        class CountVisitor(NodeVisitor):
            def __init__(self):
                self.count = 0

            def visit_text(self, node):
                self.count += 1
                return node

            def visit_usermention(self, node):
                self.count += 1
                return node

        doc = Document(
            children=[
                Paragraph(
                    children=[
                        Text(content="Hello "),
                        UserMention(user_id="U123"),
                        Text(content="!"),
                    ]
                )
            ]
        )
        visitor = CountVisitor()
        transform_ast(doc, visitor)
        assert visitor.count == 3
