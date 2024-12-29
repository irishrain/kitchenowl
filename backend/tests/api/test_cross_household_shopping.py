import pytest
from app.errors import InvalidUsage


def test_second_user_shopping_operations(client, admin_username, admin_name, admin_password, username, name, password):
    # Create first user and household
    onboard_data = {
        'username': admin_username,
        'name': admin_name,
        'password': admin_password
    }
    response = client.post('/api/onboarding', json=onboard_data)
    data = response.get_json()
    first_token = data["access_token"]
    
    # Set auth token for first user
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {first_token}'
    
    # Get first user ID
    response = client.get('/api/user')
    assert response.status_code == 200
    first_user_id = response.get_json()['id']
    
    # Create first household
    data = {
        'name': 'First Household',
        'member': [first_user_id]
    }
    response = client.post('/api/household', json=data)
    assert response.status_code == 200
    first_household_id = response.get_json()['id']
    
    # Create second user
    data = {
        'username': 'seconduser',
        'name': 'Second User',
        'password': 'secondpwd'
    }
    response = client.post('/api/user/new', json=data)
    assert response.status_code == 200
    
    # Login as second user
    data = {
        'username': 'seconduser',
        'password': 'secondpwd'
    }
    response = client.post('/api/auth', json=data)
    assert response.status_code == 200
    second_token = response.get_json()['access_token']
    
    # Set auth token for second user
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {second_token}'
    
    # Get second user ID
    response = client.get('/api/user')
    assert response.status_code == 200
    second_user_id = response.get_json()['id']
    
    # Create second household with only second user
    data = {
        'name': 'Second Household',
        'member': [second_user_id]
    }
    response = client.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Get second household's shopping list
    response = client.get(f'/api/household/{second_household_id}/shoppinglist')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    second_shoppinglist_id = data[0]['id']
    
    # Create items in second household
    test_items = ['apple', 'banana', 'orange']
    for item_name in test_items:
        data = {"name": item_name}
        response = client.post(
            f'/api/household/{second_household_id}/item', json=data)
        assert response.status_code == 200
    
    # Search for items in second household
    response = client.get(f'/api/household/{second_household_id}/item/search?query=banan')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1  # Should find only 'banana'
    found_items = {item['name'] for item in data}
    assert found_items == {'banana'}
    
    # Add found items to shopping list
    for item in data:
        response = client.post(
            f'/api/shoppinglist/{second_shoppinglist_id}/item/{item["id"]}',
            json={"description": "1 piece"})
        assert response.status_code == 200
    
    # Verify items were added to shopping list
    response = client.get(f'/api/shoppinglist/{second_shoppinglist_id}/items')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    list_items = {item['name'] for item in data}
    assert list_items == {'banana'}
    
    # Try to access first household's shopping list (should fail)
    response = client.get(f'/api/household/{first_household_id}/shoppinglist')
    assert response.status_code == 403  # Forbidden
    
    # Try to search items in first household (should fail)
    response = client.get(f'/api/household/{first_household_id}/item/search?q=an')
    assert response.status_code == 403  # Forbidden


def test_shared_household_shopping_operations(client, admin_username, admin_name, admin_password):
    # Create first user and household
    onboard_data = {
        'username': admin_username,
        'name': admin_name,
        'password': admin_password
    }
    response = client.post('/api/onboarding', json=onboard_data)
    data = response.get_json()
    first_token = data["access_token"]
    
    # Set auth token for first user
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {first_token}'
    
    # Get first user ID
    response = client.get('/api/user')
    assert response.status_code == 200
    first_user_id = response.get_json()['id']
    
    # Create second user
    data = {
        'username': 'seconduser',
        'name': 'Second User',
        'password': 'secondpwd'
    }
    response = client.post('/api/user/new', json=data)
    assert response.status_code == 200
    
    # Login as second user
    data = {
        'username': 'seconduser',
        'password': 'secondpwd'
    }
    response = client.post('/api/auth', json=data)
    assert response.status_code == 200
    second_token = response.get_json()['access_token']
    
    # Get second user ID
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {second_token}'
    response = client.get('/api/user')
    assert response.status_code == 200
    second_user_id = response.get_json()['id']
    
    # Create shared household with both users
    data = {
        'name': 'Shared Household',
        'member': [first_user_id, second_user_id]
    }
    response = client.post('/api/household', json=data)
    assert response.status_code == 200
    shared_household_id = response.get_json()['id']
    
    # Create second household with only second user
    data = {
        'name': 'Second Household',
        'member': [second_user_id]
    }
    response = client.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Get shopping lists for both households
    response = client.get(f'/api/household/{shared_household_id}/shoppinglist')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    shared_shoppinglist_id = data[0]['id']
    
    response = client.get(f'/api/household/{second_household_id}/shoppinglist')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    second_shoppinglist_id = data[0]['id']
    
    # Create items in both households
    shared_items = ['milk', 'bread', 'eggs']
    for item_name in shared_items:
        data = {"name": item_name}
        response = client.post(
            f'/api/household/{shared_household_id}/item', json=data)
        assert response.status_code == 200
    
    second_items = ['apple', 'banana', 'orange']
    for item_name in second_items:
        data = {"name": item_name}
        response = client.post(
            f'/api/household/{second_household_id}/item', json=data)
        assert response.status_code == 200
    
    # Search for items in shared household
    response = client.get(f'/api/household/{shared_household_id}/item/search?query=bread')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'bread'
    
    # Add item to shared household's shopping list
    response = client.post(
        f'/api/shoppinglist/{shared_shoppinglist_id}/item/{data[0]["id"]}',
        json={"description": "1 piece"})
    assert response.status_code == 200
    
    # Search for items in second household
    response = client.get(f'/api/household/{second_household_id}/item/search?query=banan')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1  # Should find only 'banana'
    
    # Add items to second household's shopping list
    for item in data:
        response = client.post(
            f'/api/shoppinglist/{second_shoppinglist_id}/item/{item["id"]}',
            json={"description": "1 piece"})
        assert response.status_code == 200
    
    # Verify items in shared household's list
    response = client.get(f'/api/shoppinglist/{shared_shoppinglist_id}/items')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'bread'
    
    # Verify items in second household's list
    response = client.get(f'/api/shoppinglist/{second_shoppinglist_id}/items')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    list_items = {item['name'] for item in data}
    assert list_items == {'banana'}
