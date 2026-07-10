"""Tests for Canvas Assist stub endpoints."""


class TestStructureEndpoint:
    def test_structure_returns_blocks(self, client):
        response = client.post(
            "/api/v1/canvas/structure",
            json={"description": "A samurai in a cyberpunk city at night"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "blocks" in data
        assert len(data["blocks"]) >= 2
        # Each block should have the required fields
        for block in data["blocks"]:
            assert "id" in block
            assert "type" in block
            assert "content" in block

    def test_structure_with_character_detection(self, client):
        response = client.post(
            "/api/v1/canvas/structure",
            json={"description": "A warrior princess walking through an ancient temple"},
        )
        assert response.status_code == 200
        types = [b["type"] for b in response.json()["blocks"]]
        assert "scene" in types
        assert "character" in types
        assert "action" in types

    def test_structure_empty_description_rejected(self, client):
        response = client.post(
            "/api/v1/canvas/structure",
            json={"description": ""},
        )
        assert response.status_code == 422


class TestCompleteEndpoint:
    def test_complete_returns_suggestions(self, client):
        response = client.post(
            "/api/v1/canvas/complete",
            json={
                "context": "A sci-fi battle scene",
                "existing_blocks": [],
                "mode": "completion",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) >= 1
        for s in data["suggestions"]:
            assert "title" in s
            assert "blocks" in s
            assert len(s["blocks"]) >= 1
            for b in s["blocks"]:
                assert "type" in b
                assert "content" in b

    def test_complete_mode_completion(self, client):
        response = client.post(
            "/api/v1/canvas/complete",
            json={
                "context": "Underwater civilization",
                "existing_blocks": [],
                "mode": "completion",
            },
        )
        assert response.status_code == 200
        # Should suggest additional blocks
        assert len(response.json()["suggestions"]) >= 1

    def test_complete_mode_suggestion(self, client):
        response = client.post(
            "/api/v1/canvas/complete",
            json={
                "context": "Desert landscape",
                "existing_blocks": [],
                "mode": "suggestion",
            },
        )
        assert response.status_code == 200
        assert len(response.json()["suggestions"]) >= 1


class TestInspireEndpoint:
    def test_inspire_returns_themes(self, client):
        response = client.post(
            "/api/v1/canvas/inspire",
            json={"theme": "underwater civilization"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "themes" in data
        assert len(data["themes"]) >= 1
        for theme in data["themes"]:
            assert "title" in theme
            assert "prompt" in theme
            assert "style_hint" in theme
            assert "tags" in theme
            assert "blocks" in theme
            assert len(theme["blocks"]) >= 1

    def test_inspire_different_themes(self, client):
        r1 = client.post("/api/v1/canvas/inspire", json={"theme": "space"}).json()
        r2 = client.post("/api/v1/canvas/inspire", json={"theme": "forest"}).json()
        # Each should have 2 themes
        assert len(r1["themes"]) == 2
        assert len(r2["themes"]) == 2
        # Titles should differ based on theme
        assert r1["themes"][0]["title"] != r2["themes"][0]["title"]

    def test_inspire_empty_theme_rejected(self, client):
        response = client.post("/api/v1/canvas/inspire", json={"theme": ""})
        assert response.status_code == 422
