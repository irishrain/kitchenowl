def test_recipe_creation(user_client_with_household, household_id, recipe_name, recipe_description, recipe_yields, recipe_time):
    """Test creating a recipe"""
    # Create a recipe
    recipe_data = {
        'name': recipe_name,
        'description': recipe_description,
        'yields': recipe_yields,
        'time': recipe_time,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200
    recipe = response.get_json()
    assert 'id' in recipe
    recipe_id = recipe['id']

    # Verify recipe was created correctly
    response = user_client_with_household.get(f'/api/recipe/{recipe_id}')
    assert response.status_code == 200
    recipe = response.get_json()
    assert recipe['name'] == recipe_name
    assert recipe['description'] == recipe_description
    assert recipe['yields'] == recipe_yields
    assert recipe['time'] == recipe_time


def test_recipe_with_items(user_client_with_household, household_id, recipe_with_items):
    """Test recipe with items"""
    recipe_id = recipe_with_items

    # Get recipe and verify it has items
    response = user_client_with_household.get(f'/api/recipe/{recipe_id}')
    assert response.status_code == 200
    recipe = response.get_json()
    assert len(recipe['items']) == 1
    assert recipe['items'][0]['description'] == '2 pieces'


def test_recipe_update(user_client_with_household, recipe_with_items):
    """Test updating a recipe"""
    recipe_id = recipe_with_items
    
    # Update recipe
    updated_data = {
        'name': 'Updated Recipe',
        'description': 'Updated description',
        'yields': 6,
        'time': 45,
        'cook_time': 25,
        'prep_time': 20,
        'items': []  # Remove all items
    }
    
    response = user_client_with_household.post(
        f'/api/recipe/{recipe_id}',
        json=updated_data
    )
    assert response.status_code == 200

    # Verify updates
    response = user_client_with_household.get(f'/api/recipe/{recipe_id}')
    assert response.status_code == 200
    recipe = response.get_json()
    assert recipe['name'] == 'Updated Recipe'
    assert recipe['description'] == 'Updated description'
    assert recipe['yields'] == 6
    assert recipe['time'] == 45
    assert len(recipe['items']) == 0


def test_recipe_search(user_client_with_household, household_id, recipe_with_items):
    """Test searching for recipes"""
    response = user_client_with_household.get(
        f'/api/household/{household_id}/recipe/search?query=Test'
    )
    assert response.status_code == 200
    recipes = response.get_json()
    assert len(recipes) > 0
    assert any(r['id'] == recipe_with_items for r in recipes)


def test_recipe_deletion(user_client_with_household, recipe_with_items):
    """Test deleting a recipe"""
    recipe_id = recipe_with_items
    
    # Delete recipe
    response = user_client_with_household.delete(f'/api/recipe/{recipe_id}')
    assert response.status_code == 200

    # Verify deletion
    response = user_client_with_household.get(f'/api/recipe/{recipe_id}')
    assert response.status_code == 404  # Should not be found

def test_recipe_creation_invalid_data(user_client_with_household, household_id):
    """Test recipe creation with invalid data"""
    # Test missing name
    recipe_data = {
        'description': 'Test description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test empty name
    recipe_data = {
        'name': '',
        'description': 'Test description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test negative yields value
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test description',
        'yields': -1,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test zero yields value (should be allowed)
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test description',
        'yields': 0,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200

    # Test invalid time value
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test description',
        'yields': 4,
        'time': -30,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test recipe without tags (should be allowed)
    recipe_data = {
        'name': 'Test Recipe Without Tags',
        'description': 'Test description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200

    # Test malformed JSON
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        data='not a json',
        content_type='application/json'
    )
    assert response.status_code == 400

def test_recipe_invalid_household(user_client_with_household):
    """Test recipe operations with invalid household"""
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': []
    }
    # Try to create recipe in non-existent household
    response = user_client_with_household.post(
        '/api/household/999999/recipe',
        json=recipe_data
    )
    assert response.status_code == 404

    # Try to search recipes in non-existent household
    response = user_client_with_household.get(
        '/api/household/999999/recipe/search?query=test'
    )
    assert response.status_code == 404

def test_recipe_invalid_items(user_client_with_household, household_id):
    """Test recipe creation with invalid items"""
    # Test recipe with invalid item format
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': [{'invalid_field': 'value'}]
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test recipe with empty item name
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': [{'name': '', 'description': '1 piece'}]
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400

    # Test recipe with empty item description (should be allowed)
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test description',
        'yields': 4,
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'items': [{'name': 'Test Item', 'description': ''}]
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200

def test_recipe_update_invalid_data(user_client_with_household, recipe_with_items):
    """Test recipe update with invalid data"""
    recipe_id = recipe_with_items

    # Test empty name
    updated_data = {
        'name': '',
        'description': 'Updated description',
        'yields': 6,
        'time': 45,
        'cook_time': 25,
        'prep_time': 20,
        'items': []
    }
    response = user_client_with_household.post(
        f'/api/recipe/{recipe_id}',
        json=updated_data
    )
    assert response.status_code == 400

    # Test invalid recipe ID
    response = user_client_with_household.post(
        '/api/recipe/999999',
        json=updated_data
    )
    assert response.status_code == 404

    # Test malformed JSON
    response = user_client_with_household.post(
        f'/api/recipe/{recipe_id}',
        data='not a json',
        content_type='application/json'
    )
    assert response.status_code == 400