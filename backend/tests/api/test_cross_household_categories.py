import pytest

def test_cross_household_categories(client, admin_username, admin_name, admin_password):
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
    
    # Create second household with same user
    data = {
        'name': 'Second Household',
        'member': [first_user_id]
    }
    response = client.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Create categories in both households
    data = {"name": "First Household Category"}
    response = client.post(
        f'/api/household/{first_household_id}/category', json=data)
    assert response.status_code == 200
    first_category = response.get_json()
    
    data = {"name": "Second Household Category"}
    response = client.post(
        f'/api/household/{second_household_id}/category', json=data)
    assert response.status_code == 200
    second_category = response.get_json()
    
    # Test getting categories without show_all
    response = client.get(f'/api/household/{first_household_id}/category')
    assert response.status_code == 200
    categories = response.get_json()
    assert len(categories) == 1
    assert categories[0]['name'] == "First Household Category"
    assert categories[0]['household_id'] == first_household_id
    
    # Test getting categories with show_all=false (explicit)
    response = client.get(f'/api/household/{first_household_id}/category?show_all=false')
    assert response.status_code == 200
    categories = response.get_json()
    assert len(categories) == 1
    assert categories[0]['name'] == "First Household Category"
    assert categories[0]['household_id'] == first_household_id
    
    # Test getting categories with show_all=true
    response = client.get(f'/api/household/{first_household_id}/category?show_all=true')
    assert response.status_code == 200
    categories = response.get_json()
    assert len(categories) == 2
    # Categories should be ordered with current household first
    assert categories[0]['name'] == "First Household Category"
    assert categories[0]['household_id'] == first_household_id
    assert categories[1]['name'] == "Second Household Category"
    assert categories[1]['household_id'] == second_household_id

def test_cross_household_categories_unauthorized(client, admin_username, admin_name, admin_password):
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
    
    # Set auth token for second user
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {second_token}'
    
    # Get second user ID
    response = client.get('/api/user')
    assert response.status_code == 200
    second_user_id = response.get_json()['id']
    
    # Switch to first user to create their household
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {first_token}'
    
    # Create first household with only first user
    data = {
        'name': 'First Household',
        'member': [first_user_id]
    }
    response = client.post('/api/household', json=data)
    assert response.status_code == 200
    first_household_id = response.get_json()['id']
    
    # Switch back to second user (non-admin)
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {second_token}'
    # Try to create category in first household with second user
    # This should fail because the second user is not a member
    data = {"name": "Unauthorized Category"}
    response = client.post(
        f'/api/household/{first_household_id}/category', json=data)
    assert response.status_code == 403  # Should be forbidden
    
    # Create a household for the second user
    data = {
        'name': 'Second User Household',
        'member': [second_user_id]
    }
    response = client.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Create a category in second user's household
    data = {"name": "Second User Category"}
    response = client.post(
        f'/api/household/{second_household_id}/category', json=data)
    assert response.status_code == 200
    
    # Test getting categories with show_all=true
    # Should only show categories from households where the user is a member
    response = client.get(f'/api/household/{second_household_id}/category?show_all=true')
    assert response.status_code == 200
    categories = response.get_json()
    # Verify we only see categories from households where we are a member
    assert len(categories) == 1
    assert categories[0]['name'] == "Second User Category"
    assert categories[0]['household_id'] == second_household_id

def test_cross_household_categories_with_items(client, admin_username, admin_name, admin_password):
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
    
    # Create second household with same user
    data = {
        'name': 'Second Household',
        'member': [first_user_id]
    }
    response = client.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Create categories in both households
    data = {"name": "First Household Category"}
    response = client.post(
        f'/api/household/{first_household_id}/category', json=data)
    assert response.status_code == 200
    first_category = response.get_json()
    
    data = {"name": "Second Household Category"}
    response = client.post(
        f'/api/household/{second_household_id}/category', json=data)
    assert response.status_code == 200
    second_category = response.get_json()
    
    # Create items in both categories
    data = {
        "name": "first_item",
        "category_id": first_category['id']
    }
    response = client.post(
        f'/api/household/{first_household_id}/item', json=data)
    assert response.status_code == 200
    
    data = {
        "name": "second_item",
        "category_id": second_category['id']
    }
    response = client.post(
        f'/api/household/{second_household_id}/item', json=data)
    assert response.status_code == 200
    
    # Test getting categories with show_all=false
    # Should only show first household's category and item
    response = client.get(f'/api/household/{first_household_id}/category')
    assert response.status_code == 200
    categories = response.get_json()
    assert len(categories) == 1
    assert categories[0]['name'] == "First Household Category"
    
    # Test getting categories with show_all=true
    # Should show both categories and their items
    response = client.get(f'/api/household/{first_household_id}/category?show_all=true')
    assert response.status_code == 200
    categories = response.get_json()
    assert len(categories) == 2
    assert categories[0]['name'] == "First Household Category"
    assert categories[1]['name'] == "Second Household Category"