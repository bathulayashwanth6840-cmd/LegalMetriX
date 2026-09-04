def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Test Officer", "email": "officer@test.com", "password": "password123", "role": "officer"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "officer@test.com"
    assert "id" in data

def test_login_user(client):
    # Register first
    client.post(
        "/api/auth/register",
        json={"name": "Test Officer", "email": "officer2@test.com", "password": "password123", "role": "officer"}
    )
    
    # Login
    response = client.post(
        "/api/auth/login",
        data={"username": "officer2@test.com", "password": "password123"} # OAuth2 form data
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"name": "Test Officer", "email": "officer3@test.com", "password": "password123", "role": "officer"}
    )
    
    response = client.post(
        "/api/auth/login",
        data={"username": "officer3@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    
def test_get_me(client):
    client.post(
        "/api/auth/register",
        json={"name": "Test Officer", "email": "officer4@test.com", "password": "password123", "role": "officer"}
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "officer4@test.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "officer4@test.com"
