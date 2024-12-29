import pytest
from app.errors import InvalidUsage


def test_cross_household_recipe_operations(user_client_with_household, household_id):
    # Create second household
    response = user_client_with_household.get('/api/user')
    assert response.status_code == 200
    user_id = response.get_json()['id']
    
    data = {
        'name': 'Second Household',
        'member': [user_id]
    }
    response = user_client_with_household.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Create items in both households
    data = {"name": "first_household_item"}
    response = user_client_with_household.post(
        f'/api/household/{household_id}/item', json=data)
    assert response.status_code == 200
    first_item_id = response.get_json()['id']
    
    data = {"name": "second_household_item"}
    response = user_client_with_household.post(
        f'/api/household/{second_household_id}/item', json=data)
    assert response.status_code == 200
    second_item_id = response.get_json()['id']
    
    # Try to create recipe in first household with item from second household
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'items': [{'name': 'second_household_item', 'description': '1 piece'}]
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 400  # Should fail with InvalidUsage


def test_cross_household_planner_operations(user_client_with_household, household_id):
    # Create second household
    response = user_client_with_household.get('/api/user')
    assert response.status_code == 200
    user_id = response.get_json()['id']
    
    data = {
        'name': 'Second Household',
        'member': [user_id]
    }
    response = user_client_with_household.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Create recipe in second household
    recipe_data = {
        'name': 'Second Household Recipe',
        'description': 'Test Description',
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'yields': 4,
        'items': [{'name': 'second_item', 'description': '1 piece'}],
        'tags': ['main']
    }
    response = user_client_with_household.post(
        f'/api/household/{second_household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200
    second_recipe = response.get_json()
    
    # Try to add recipe from second household to first household's planner
    plan_data = {
        'recipe_id': second_recipe['id'],
        'day': 0
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/planner/recipe',
        json=plan_data
    )
    assert response.status_code == 400  # Should fail with InvalidUsage


def test_cross_household_recipe_tags(user_client_with_household, household_id):
    # Create second household
    response = user_client_with_household.get('/api/user')
    assert response.status_code == 200
    user_id = response.get_json()['id']
    
    data = {
        'name': 'Second Household',
        'member': [user_id]
    }
    response = user_client_with_household.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Create a recipe in first household
    recipe_data = {
        'name': 'Test Recipe',
        'description': 'Test Description',
        'time': 30,
        'cook_time': 20,
        'prep_time': 10,
        'yields': 4,
        'items': [{'name': 'first_item', 'description': '1 piece'}],
        'tags': ['first_tag']
    }
    response = user_client_with_household.post(
        f'/api/household/{household_id}/recipe',
        json=recipe_data
    )
    assert response.status_code == 200
    recipe = response.get_json()
    
    # Create a tag in second household
    data = {"name": "second_tag"}
    response = user_client_with_household.post(
        f'/api/household/{second_household_id}/tag', json=data)
    assert response.status_code == 200
    
    # Try to add tag from second household to recipe in first household
    update_data = {
        'tags': ['first_tag', 'second_tag']
    }
    response = user_client_with_household.post(
        f'/api/recipe/{recipe["id"]}',
        json=update_data
    )
    assert response.status_code == 400  # Should fail with InvalidUsage


def test_cross_household_item_merge(user_client_with_household, household_id):
    # Create second household
    response = user_client_with_household.get('/api/user')
    assert response.status_code == 200
    user_id = response.get_json()['id']
    
    data = {
        'name': 'Second Household',
        'member': [user_id]
    }
    response = user_client_with_household.post('/api/household', json=data)
    assert response.status_code == 200
    second_household_id = response.get_json()['id']
    
    # Create items in both households
    data = {"name": "test_item"}
    response = user_client_with_household.post(
        f'/api/household/{household_id}/item', json=data)
    assert response.status_code == 200
    first_item = response.get_json()
    
    data = {"name": "test_item_2"}
    response = user_client_with_household.post(
        f'/api/household/{second_household_id}/item', json=data)
    assert response.status_code == 200
    second_item = response.get_json()
    
    # Try to merge items from different households
    data = {
        "merge_item_id": second_item['id']
    }
    response = user_client_with_household.post(
        f'/api/item/{first_item["id"]}',
        json=data
    )
    assert response.status_code == 400  # Should fail with InvalidUsage