from sqlalchemy import func
from app.errors import NotFoundRequest, InvalidUsage
from app.models import Household, RecipeItems, RecipeTags
from app import db
from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import marshmallow
import werkzeug.exceptions
from app.helpers import validate_args, authorize_household
from app.models import Recipe, Item, Tag, User, HouseholdMember
from app.service.file_has_access_or_download import file_has_access_or_download
from app.service.recipe_scraping import scrape
from .schemas import (
    SearchByNameRequest,
    AddRecipe,
    UpdateRecipe,
    GetAllFilterRequest,
    ScrapeRecipe,
)

recipe = Blueprint("recipe", __name__)
recipeHousehold = Blueprint("recipe", __name__)

# Import and register the suggestions blueprint
from .suggestions_controller import recipe_suggestions


@recipeHousehold.route("", methods=["GET"])
@jwt_required()
@authorize_household()
def getAllRecipes(household_id):
    return jsonify(
        [e.obj_to_full_dict() for e in Recipe.all_from_household_by_name(household_id)]
    )


@recipe.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def getRecipeById(id):
    recipe = Recipe.find_by_id(id)
    if not recipe:
        raise NotFoundRequest()
    if not recipe.public:
        recipe.checkAuthorized()
    return jsonify(recipe.obj_to_full_dict())


@recipeHousehold.route("", methods=["POST"])
@jwt_required()
def addRecipe(household_id):
    """Add a new recipe to the household
    
    The function will validate:
    - All required fields are present (name, description, time, cook_time, prep_time, yields, items, tags)
    - All fields have valid values (non-empty strings, positive numbers)
    - Items and tags belong to the same household
    """
    # Check if household exists first
    household = Household.find_by_id(household_id)
    if not household:
        raise NotFoundRequest()
    
    # Check if user has access to the household
    from app.models import HouseholdMember
    user_id = get_jwt_identity()
    member = HouseholdMember.find_by_ids(household_id, user_id)
    if not member:
        raise InvalidUsage("User does not have access to this household")
        
    # Now validate the request data
    schema = AddRecipe()
    try:
        json_data = request.get_json()
        if json_data is None:
            raise InvalidUsage("Invalid JSON format")
        args = schema.load(json_data)
    except marshmallow.exceptions.ValidationError as e:
        raise InvalidUsage(str(e.messages))
    except werkzeug.exceptions.BadRequest:
        raise InvalidUsage("Invalid JSON format")
    recipe = Recipe()
    recipe.name = args["name"]
    recipe.description = args["description"]
    recipe.household_id = household_id
    if "time" in args:
        recipe.time = args["time"]
    if "cook_time" in args:
        recipe.cook_time = args["cook_time"]
    if "prep_time" in args:
        recipe.prep_time = args["prep_time"]
    if "yields" in args:
        recipe.yields = args["yields"]
    if "source" in args:
        recipe.source = args["source"]
    if "public" in args:
        recipe.public = args["public"]
    if "photo" in args and args["photo"] != recipe.photo:
        recipe.photo = file_has_access_or_download(args["photo"], recipe.photo)
    recipe.save()
    # Validate required fields
    if not recipe.name or not recipe.name.strip():
        raise InvalidUsage("Recipe name cannot be empty")

    if recipe.yields < 0:
        raise InvalidUsage("Recipe yields must be greater than or equal to 0")
    if recipe.time < 0:
        raise InvalidUsage("Recipe time must be greater than or equal to 0")
    if recipe.cook_time < 0:
        raise InvalidUsage("Cook time must be greater than or equal to 0")
    if recipe.prep_time < 0:
        raise InvalidUsage("Prep time must be greater than or equal to 0")

    # Process items if provided
    if "items" in args:
        for recipeItem in args["items"]:
            # Validate item data
            if not recipeItem.get("name") or not recipeItem["name"].strip():
                raise InvalidUsage("Item name cannot be empty")
            
            # Check if the item exists in the target household
            item = Item.find_by_name(household_id, recipeItem["name"])
            
            # If it doesn't exist in the target household, check if it exists in any other household
            if not item:
                # Use a raw query to check if the item exists in any other household
                other_household_item = Item.query.filter(
                    func.lower(Item.name) == func.lower(recipeItem["name"].strip()),
                    Item.household_id != household_id
                ).first()
                
                if other_household_item:
                    raise InvalidUsage("Cannot add items from different households")
                
                # If the item doesn't exist in any household, create it in the target household
                item = Item.create_by_name(household_id, recipeItem["name"])
                
            con = RecipeItems(
                description=recipeItem["description"], 
                optional=recipeItem.get("optional", False)
            )
            # Add all related objects to session
            db.session.add(item)
            db.session.add(recipe)
            db.session.add(con)
            con.item = item
            con.recipe = recipe
            con.save()

    # Process tags if provided
    if "tags" in args and args["tags"]:
        for tagName in args["tags"]:
            if not tagName or not tagName.strip():
                raise InvalidUsage("Tag name cannot be empty")
                
            tag = Tag.find_by_name(household_id, tagName)
            if not tag:
                tag = Tag.create_by_name(household_id, tagName)
            elif tag.household_id != household_id:
                raise InvalidUsage("Cannot add tags from different households")
                
            con = RecipeTags()
            # Add all related objects to session
            db.session.add(tag)
            db.session.add(recipe)
            db.session.add(con)
            con.tag = tag
            con.recipe = recipe
            con.save()

    # Return the created recipe with detailed error messages if validation fails
    try:
        result = recipe.obj_to_full_dict()
        result['message'] = 'Recipe created successfully'
        return jsonify(result)
    except Exception as e:
        raise InvalidUsage(f"Failed to create recipe: {str(e)}")


@recipe.route("/<int:id>", methods=["POST"])
@jwt_required()
@validate_args(UpdateRecipe)
def updateRecipe(args, id):  # noqa: C901
    recipe = Recipe.find_by_id(id)
    if not recipe:
        raise NotFoundRequest()
    recipe.checkAuthorized()

    # Validate fields
    if "name" in args:
        if not args["name"] or not args["name"].strip():
            raise InvalidUsage("Recipe name cannot be empty")
        recipe.name = args["name"]
    if "description" in args:
        recipe.description = args["description"]
    if "time" in args:
        if args["time"] < 0:
            raise InvalidUsage("Recipe time must be greater than or equal to 0")
        recipe.time = args["time"]
    if "cook_time" in args:
        if args["cook_time"] < 0:
            raise InvalidUsage("Cook time must be greater than or equal to 0")
        recipe.cook_time = args["cook_time"]
    if "prep_time" in args:
        if args["prep_time"] < 0:
            raise InvalidUsage("Prep time must be greater than or equal to 0")
        recipe.prep_time = args["prep_time"]
    if "yields" in args:
        if args["yields"] < 0:
            raise InvalidUsage("Recipe yields must be greater than or equal to 0")
        recipe.yields = args["yields"]
    if "source" in args:
        recipe.source = args["source"]
    if "public" in args:
        recipe.public = args["public"]
    if "photo" in args and args["photo"] != recipe.photo:
        recipe.photo = file_has_access_or_download(args["photo"], recipe.photo)
    recipe.save()

    # Process items
    if "items" in args:
        # Validate items
        for recipeItem in args["items"]:
            if not recipeItem.get("name") or not recipeItem["name"].strip():
                raise InvalidUsage("Item name cannot be empty")

        # Remove deleted items
        for con in recipe.items:
            item_names = [e["name"] for e in args["items"]]
            if con.item.name not in item_names:
                con.delete()

        # Add/update items
        for recipeItem in args["items"]:
            item = Item.find_by_name(recipe.household_id, recipeItem["name"])
            if not item:
                item = Item.create_by_name(recipe.household_id, recipeItem["name"])
            elif item.household_id != recipe.household_id:
                raise InvalidUsage("Cannot add items from different households")
                
            con = RecipeItems.find_by_ids(recipe.id, item.id)
            if con:
                if "description" in recipeItem:
                    con.description = recipeItem["description"]
                if "optional" in recipeItem:
                    con.optional = recipeItem["optional"]
            else:
                con = RecipeItems(
                    description=recipeItem["description"],
                    optional=recipeItem.get("optional", False)
                )
            # Add all related objects to session
            db.session.add(item)
            db.session.add(recipe)
            db.session.add(con)
            con.item = item
            con.recipe = recipe
            con.save()

    # Process tags
    if "tags" in args:
        # Validate tags
        for tagName in args["tags"]:
            if not tagName or not tagName.strip():
                raise InvalidUsage("Tag name cannot be empty")

        # Remove deleted tags
        for con in recipe.tags:
            if con.tag.name not in args["tags"]:
                con.delete()

        # Add new tags
        for recipeTag in args["tags"]:
            tag = Tag.find_by_name(recipe.household_id, recipeTag)
            if not tag:
                tag = Tag.create_by_name(recipe.household_id, recipeTag)
            elif tag.household_id != recipe.household_id:
                raise InvalidUsage("Cannot add tags from different households")
                
            con = RecipeTags.find_by_ids(recipe.id, tag.id)
            if not con:
                con = RecipeTags()
                # Add all related objects to session
                db.session.add(tag)
                db.session.add(recipe)
                db.session.add(con)
                con.tag = tag
                con.recipe = recipe
                con.save()

    return jsonify(recipe.obj_to_full_dict())


@recipe.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def deleteRecipeById(id):
    recipe = Recipe.find_by_id(id)
    if not recipe:
        raise NotFoundRequest()
    recipe.checkAuthorized()
    recipe.delete()
    return jsonify({"msg": "DONE"})

@recipe.route("/<int:id>/export", methods=["GET"])
@jwt_required()
def exportRecipe(id):
    """Export a recipe in a format suitable for importing"""
    recipe = Recipe.find_by_id(id)
    if not recipe:
        raise NotFoundRequest()
    recipe.checkAuthorized()
    return jsonify(recipe.obj_to_export_dict())


@recipeHousehold.route("/search", methods=["GET"])
@jwt_required()
@validate_args(SearchByNameRequest)
def searchRecipeByName(args, household_id):
    # Check if household exists first
    household = Household.find_by_id(household_id)
    if not household:
        raise NotFoundRequest()
        
    # Check if user has access to the household
    user_id = get_jwt_identity()
    member = HouseholdMember.find_by_ids(household_id, user_id)
    if not member:
        raise InvalidUsage("User does not have access to this household")
        
    if "only_ids" in args and args["only_ids"]:
        return jsonify([e.id for e in Recipe.search_name(household_id, args["query"])])
    return jsonify(
        [e.obj_to_full_dict() for e in Recipe.search_name(household_id, args["query"])]
    )


@recipeHousehold.route("/filter", methods=["POST"])
@jwt_required()
@authorize_household()
@validate_args(GetAllFilterRequest)
def getAllFiltered(args, household_id):
    return jsonify(
        [
            e.obj_to_full_dict()
            for e in Recipe.all_by_name_with_filter(household_id, args["filter"])
        ]
    )


@recipeHousehold.route("/scrape", methods=["GET", "POST"])
@jwt_required()
@authorize_household()
@validate_args(ScrapeRecipe)
def scrapeRecipe(args, household_id):
    household = Household.find_by_id(household_id)
    if not household:
        raise NotFoundRequest()

    res = scrape(args["url"], household)
    if res:
        return jsonify(res)
    return "Unsupported website", 400
