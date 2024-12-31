import pytest
from datetime import datetime, timezone
from app.models import Token


import jwt

def get_jti(token):
    decoded = jwt.decode(token, options={"verify_signature": False})
    return decoded.get('jti')

def test_normal_token_refresh(user_client, username, password):
    """Test normal token refresh flow."""
    # Login
    response = user_client.post("/api/auth", json={"username": username, "password": password, "device": "test"})
    assert response.status_code == 200
    data = response.get_json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Use access token
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200

    # Refresh token
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.get_json()
    new_access_token = data["access_token"]
    new_refresh_token = data["refresh_token"]

    # Use new access token
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {new_access_token}"})
    assert response.status_code == 200

def test_shaky_network_token_refresh(user_client, username, password):
    """Test token refresh with network issues (client ignores new tokens)."""
    # Login
    response = user_client.post("/api/auth", json={"username": username, "password": password, "device": "test"})
    assert response.status_code == 200
    data = response.get_json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Use access token
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200

    # Refresh token but "lose" the response
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    # Intentionally ignore new tokens

    # Use old access token, should still work since we didn't use the new one
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200


    # Original refresh token should still work since we didn't use the new one
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.get_json()
    new_access_token = data["access_token"]

    # New access token should work
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {new_access_token}"})
    assert response.status_code == 200

def test_token_hijack_attempt(user_client, username, password):
    """Test attempted token hijacking scenario."""
    # Login
    response = user_client.post("/api/auth", json={"username": username, "password": password, "device": "test"})
    assert response.status_code == 200
    data = response.get_json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
  
    # Create new refresh token but don't use its access token (simulating leak)
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.get_json()
    leaked_access_token = data["access_token"]
    leaked_refresh_token = data["refresh_token"]
    
    
    # User continues normal use with original tokens
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200

    # Create another refresh token (normal use)
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.get_json()
    new_access_token = data["access_token"]
    new_refresh_token = data["refresh_token"]
    

    # Use new access token to make it the active chain
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {new_access_token}"})
    assert response.status_code == 200

    # Attacker tries to use leaked access token
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {leaked_access_token}"})
    assert response.status_code == 401  # Should be rejected

    # Attacker tries to use leaked refresh token
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {leaked_refresh_token}"})
    assert response.status_code == 401  # Should be rejected

    # Original user's new tokens should also be rejected, as there was a breach
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {new_refresh_token}"})
    assert response.status_code == 401

def test_token_hijack_attacker_first(user_client, username, password):
    """Test attempted token hijacking scenario where attacker acts first."""
    # Login
    response = user_client.post("/api/auth", json={"username": username, "password": password, "device": "test"})
    assert response.status_code == 200
    data = response.get_json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Attacker uses refresh token first
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.get_json()
    attacker_access_token = data["access_token"]
    attacker_refresh_token = data["refresh_token"]

    # Attacker uses their access token
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {attacker_access_token}"})
    assert response.status_code == 200

    # Original user tries to use original access token - should be rejected
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401  # Should be rejected

    # Original user tries to use original refresh token - should be rejected
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 401  # Should be rejected

    # Attacker uses their access token - should be rejected after compromise detected
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {attacker_access_token}"})
    assert response.status_code == 401

    # Attacker tries to refresh - should be rejected after compromise detected
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {attacker_refresh_token}"})
    assert response.status_code == 401  # Should be rejected

def test_token_refresh_race_condition(user_client, username, password):
    """Test race condition where two refresh requests happen before either access token is used."""
    # Login
    response = user_client.post("/api/auth", json={"username": username, "password": password, "device": "test"})
    assert response.status_code == 200
    data = response.get_json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # First client requests refresh
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.get_json()
    first_access_token = data["access_token"]
    first_refresh_token = data["refresh_token"]

    # Second client requests refresh before first access token is used
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.get_json()
    second_access_token = data["access_token"]
    second_refresh_token = data["refresh_token"]

    # Second client uses their access token first
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {second_access_token}"})
    assert response.status_code == 200

    # First client tries to use their access token - should be rejected
    response = user_client.get("/api/user", headers={"Authorization": f"Bearer {first_access_token}"})
    assert response.status_code == 401  # Should be rejected

    # First client tries to use their refresh token - should be rejected
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {first_refresh_token}"})
    assert response.status_code == 401  # Should be rejected

    # Original refresh token should be rejected
    response = user_client.get("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 401  # Should be rejected
