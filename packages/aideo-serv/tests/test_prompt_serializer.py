"""Tests for prompt serialization from structured canvas blocks."""

from uuid import uuid4

from aideo_serv.models.generate import (
    BlockConnection,
    BlockType,
    GenerationParams,
    PromptBlock,
)
from aideo_serv.services.prompt_serializer import serialize_prompt


def _block(type_: BlockType, content: str, scene_tag=None, **params) -> PromptBlock:
    """Helper to build a PromptBlock with minimal boilerplate."""
    return PromptBlock(
        id=uuid4(),
        type=type_,
        content=content,
        scene_tag=scene_tag,
        params=GenerationParams(**params),
    )


class TestSerializePrompt:
    def test_empty_blocks_returns_empty(self):
        assert serialize_prompt([]) == ""

    def test_single_scene_block(self):
        result = serialize_prompt([
            _block(BlockType.SCENE, "A dark forest", scene_tag=0),
        ])
        assert "[Scene 1]" in result
        assert "Scene: A dark forest" in result

    def test_multiple_blocks_same_scene(self):
        result = serialize_prompt([
            _block(BlockType.SCENE, "Cyberpunk alley", scene_tag=0),
            _block(BlockType.CHARACTER, "Samurai warrior", scene_tag=0),
            _block(BlockType.ACTION, "Walking in rain", scene_tag=0),
        ])
        assert "[Scene 1]" in result
        assert "Scene: Cyberpunk alley" in result
        assert "Character: Samurai warrior" in result
        assert "Action: Walking in rain" in result

    def test_multiple_scenes_grouped(self):
        result = serialize_prompt([
            _block(BlockType.SCENE, "Forest", scene_tag=0),
            _block(BlockType.CHARACTER, "Elf", scene_tag=0),
            _block(BlockType.SCENE, "Castle", scene_tag=1),
            _block(BlockType.CHARACTER, "Knight", scene_tag=1),
        ])
        assert "[Scene 1]" in result
        assert "[Scene 2]" in result
        # Scene 1 content
        assert "Scene: Forest" in result
        assert "Character: Elf" in result
        # Scene 2 content
        assert "Scene: Castle" in result
        assert "Character: Knight" in result

    def test_ungrouped_blocks_no_scene_header(self):
        result = serialize_prompt([
            _block(BlockType.STYLE, "Cinematic lighting"),
            _block(BlockType.MOOD, "Dark and moody"),
        ])
        assert "[Scene" not in result
        assert "Visual Style: Cinematic lighting" in result
        assert "Atmosphere & Mood: Dark and moody" in result

    def test_mixed_grouped_and_ungrouped(self):
        result = serialize_prompt([
            _block(BlockType.SCENE, "Ocean", scene_tag=0),
            _block(BlockType.CHARACTER, "Mermaid", scene_tag=0),
            _block(BlockType.STYLE, "Fantasy"),
        ])
        assert "[Scene 1]" in result
        assert "Visual Style: Fantasy" in result

    def test_params_formatted_inline(self):
        result = serialize_prompt([
            _block(BlockType.STYLE, "Anime style", style="anime", duration=10),
        ])
        assert "Visual Style: Anime style" in result
        assert "(duration=10s, style=anime)" in result

    def test_blocks_ordered_by_type_priority(self):
        result = serialize_prompt([
            _block(BlockType.CUSTOM, "Custom note", scene_tag=0),
            _block(BlockType.SCENE, "Main scene", scene_tag=0),
            _block(BlockType.CHARACTER, "Hero", scene_tag=0),
        ])
        scene1_idx = result.index("[Scene 1]")
        scene_idx = result.index("Scene: Main scene")
        char_idx = result.index("Character: Hero")
        custom_idx = result.index("Additional Notes: Custom note")
        assert scene1_idx < scene_idx < char_idx < custom_idx

    def test_connections_not_used_in_serialization(self):
        """Connections are for reference only, not in output."""
        blocks = [_block(BlockType.SCENE, "Test", scene_tag=0)]
        connections = [BlockConnection(source_id=blocks[0].id, target_id=uuid4())]
        result = serialize_prompt(blocks, connections)
        assert "Test" in result
        # No connection info should leak into the prompt


class TestFormatParams:
    def test_empty_params_no_output(self):
        result = serialize_prompt([
            _block(BlockType.SCENE, "Scene only", scene_tag=0),
        ])
        assert "(" not in result  # No inline params

    def test_partial_params(self):
        result = serialize_prompt([
            _block(BlockType.STYLE, "Style", style="3d-render"),
        ])
        assert "(style=3d-render)" in result
        assert "duration" not in result
