"""Transformer tests."""

from slack_gfm.ast import (
    ChannelMention,
    Document,
    Paragraph,
    Text,
    UsergroupMention,
    UserMention,
)
from slack_gfm.transformers import CallbackMapper, IDMapper, apply_id_mappings


class TestIDMapper:
    """Test ID mapping transformer."""

    def test_map_user_id(self):
        """Test user ID mapping."""
        doc = Document(children=[Paragraph(children=[UserMention(user_id="U123")])])
        mapper = IDMapper(user_map={"U123": "john"})
        result = mapper.visit(doc)
        user = result.children[0].children[0]
        assert user.username == "john"

    def test_map_channel_id(self):
        """Test channel ID mapping."""
        doc = Document(children=[Paragraph(children=[ChannelMention(channel_id="C123")])])
        mapper = IDMapper(channel_map={"C123": "general"})
        result = mapper.visit(doc)
        channel = result.children[0].children[0]
        assert channel.channel_name == "general"

    def test_map_usergroup_id(self):
        """Test usergroup ID mapping."""
        doc = Document(children=[Paragraph(children=[UsergroupMention(usergroup_id="S123")])])
        mapper = IDMapper(usergroup_map={"S123": "engineers"})
        result = mapper.visit(doc)
        usergroup = result.children[0].children[0]
        assert usergroup.usergroup_name == "engineers"

    def test_map_missing_id(self):
        """Test mapping with missing ID."""
        doc = Document(children=[Paragraph(children=[UserMention(user_id="U999")])])
        mapper = IDMapper(user_map={"U123": "john"})
        result = mapper.visit(doc)
        user = result.children[0].children[0]
        # Should keep original ID when not in map
        assert user.user_id == "U999"


class TestCallbackMapper:
    """Test callback-based transformer."""

    def test_user_callback(self):
        """Test user mention callback."""
        from dataclasses import replace

        doc = Document(children=[Paragraph(children=[UserMention(user_id="U123")])])

        def user_mapper(node):
            # Use replace() since nodes are frozen
            return replace(node, username="custom_name")

        mapper = CallbackMapper(user_callback=user_mapper)
        result = mapper.visit(doc)
        user = result.children[0].children[0]
        assert user.username == "custom_name"

    def test_channel_callback(self):
        """Test channel mention callback."""
        from dataclasses import replace

        doc = Document(children=[Paragraph(children=[ChannelMention(channel_id="C123")])])

        def channel_mapper(node):
            # Use replace() since nodes are frozen
            return replace(node, channel_name="custom_channel")

        mapper = CallbackMapper(channel_callback=channel_mapper)
        result = mapper.visit(doc)
        channel = result.children[0].children[0]
        assert channel.channel_name == "custom_channel"

    def test_usergroup_callback(self):
        """Test usergroup mention callback."""
        from dataclasses import replace

        doc = Document(children=[Paragraph(children=[UsergroupMention(usergroup_id="S123")])])

        def usergroup_mapper(node):
            # Use replace() since nodes are frozen
            return replace(node, usergroup_name="custom_group")

        mapper = CallbackMapper(usergroup_callback=usergroup_mapper)
        result = mapper.visit(doc)
        usergroup = result.children[0].children[0]
        assert usergroup.usergroup_name == "custom_group"


class TestApplyIDMappings:
    """Test apply_id_mappings convenience function."""

    def test_apply_user_mapping(self):
        """Test applying user mapping."""
        doc = Document(children=[Paragraph(children=[UserMention(user_id="U123")])])
        result = apply_id_mappings(doc, user_map={"U123": "john"})
        user = result.children[0].children[0]
        assert user.username == "john"

    def test_apply_all_mappings(self):
        """Test applying all mappings."""
        doc = Document(
            children=[
                Paragraph(
                    children=[
                        UserMention(user_id="U123"),
                        Text(content=" "),
                        ChannelMention(channel_id="C456"),
                        Text(content=" "),
                        UsergroupMention(usergroup_id="S789"),
                    ]
                )
            ]
        )
        result = apply_id_mappings(
            doc,
            user_map={"U123": "john"},
            channel_map={"C456": "general"},
            usergroup_map={"S789": "engineers"},
        )
        children = result.children[0].children
        assert children[0].username == "john"
        assert children[2].channel_name == "general"
        assert children[4].usergroup_name == "engineers"
