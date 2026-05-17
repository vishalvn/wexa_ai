import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_creates_user_and_org(client: AsyncClient):
    response = await client.post("/api/v1/auth/signup", json={
        "email": "newuser@test.com",
        "full_name": "New User",
        "password": "securepass123",
        "organization_name": "My Company",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "owner"
    assert data["organization"]["name"] == "My Company"
    assert "api_key" in data["organization"]


@pytest.mark.asyncio
async def test_signup_duplicate_email_rejected(client: AsyncClient):
    payload = {
        "email": "duplicate@test.com",
        "full_name": "Dup User",
        "password": "pass12345",
        "organization_name": "Org A",
    }
    await client.post("/api/v1/auth/signup", json=payload)
    response = await client.post("/api/v1/auth/signup", json={**payload, "organization_name": "Org B"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_returns_token(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={
        "email": "login@test.com",
        "full_name": "Login User",
        "password": "mypassword123",
        "organization_name": "Login Co",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com",
        "password": "mypassword123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={
        "email": "badpass@test.com",
        "full_name": "Bad Pass",
        "password": "correct123",
        "organization_name": "Test Co",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "badpass@test.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_with_token(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "organization" in data


@pytest.mark.asyncio
async def test_weak_password_rejected(client: AsyncClient):
    """Passwords under 8 characters should be rejected."""
    response = await client.post("/api/v1/auth/signup", json={
        "email": "weak@test.com",
        "full_name": "Weak Pass",
        "password": "short",
        "organization_name": "Co",
    })
    assert response.status_code == 422  # Pydantic validation error
