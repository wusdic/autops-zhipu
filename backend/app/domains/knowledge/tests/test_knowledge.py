"""Knowledge domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_knowledge_api_list(client):
    """Test GET /api/v1/knowledge returns list."""
    resp = await client.get("/api/v1/knowledge")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_knowledge_model():
    """Test knowledge article model."""
    from app.domains.knowledge.models import KnowledgeArticle
    a = KnowledgeArticle(title="Test Article", article_type="standard_solution")
    assert a.title == "Test Article"
    assert a.article_type == "standard_solution"