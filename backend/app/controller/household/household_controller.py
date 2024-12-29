import gevent
from app.config import SUPPORTED_LANGUAGES
from app.helpers import validate_args, authorize_household, RequiredRights
from flask import jsonify, Blueprint
from app.errors import NotFoundRequest, InvalidUsage, ForbiddenRequest
from flask_jwt_extended import current_user, jwt_required
from app.models import Household, HouseholdMember, Shoppinglist, User
from app.service.import_language import importLanguage
from app.service.file_has_access_or_download import file_has_access_or_download
from .schemas import AddHousehold, UpdateHousehold, UpdateHouseholdMember
from app import socketio, db

household = Blueprint("household", __name__)


@household.route("", methods=["GET"])
@jwt_required()
def getUserHouseholds():
    return jsonify(
        [
            e.household.obj_to_dict()
            for e in HouseholdMember.find_by_user(current_user.id)
        ]
    )


@household.route("/<int:household_id>", methods=["GET"])
@jwt_required()
@authorize_household()
def getHousehold(household_id):
    household = Household.find_by_id(household_id)
    if not household:
        raise NotFoundRequest()
    return jsonify(household.obj_to_dict())


@household.route("", methods=["POST"])
@jwt_required()
@validate_args(AddHousehold)
def addHousehold(args):
    household = Household()
    household.name = args["name"]
    if "photo" in args and args["photo"] != household.photo:
        household.photo = file_has_access_or_download(args["photo"], household.photo)
    if "language" in args and args["language"] in SUPPORTED_LANGUAGES:
        household.language = args["language"]
    if "planner_feature" in args:
        household.planner_feature = args["planner_feature"]
    if "expenses_feature" in args:
        household.expenses_feature = args["expenses_feature"]
    if "view_ordering" in args:
        household.view_ordering = args["view_ordering"]
    household.save()

    member = HouseholdMember()
    member.household_id = household.id
    member.user_id = current_user.id
    member.owner = True
    member.save()

    if "member" in args:
        for uid in args["member"]:
            if uid == current_user.id:
                continue
            if not User.find_by_id(uid):
                continue
            member = HouseholdMember()
            member.household_id = household.id
            member.user_id = uid
            member.save()

    Shoppinglist(name="Default", household_id=household.id).save()

    if household.language:
        gevent.spawn(importLanguage, household.id, household.language, True)

    return jsonify(household.obj_to_dict())


@household.route("/<int:household_id>", methods=["POST", "PUT"])
@jwt_required()
@validate_args(UpdateHousehold)
def updateHousehold(args, household_id):
    household = Household.find_by_id(household_id)
    if not household:
        raise NotFoundRequest()

    # Check if user is admin
    from app.models import HouseholdMember
    member = HouseholdMember.find_by_ids(household_id, current_user.id)
    if not member:
        raise ForbiddenRequest()
    if not member.admin:
        raise ForbiddenRequest("Only household admins can update household settings")

    # Validate fields
    if "name" in args:
        if not args["name"] or not args["name"].strip():
            raise InvalidUsage("Household name cannot be empty")
        household.name = args["name"]
    if "photo" in args and args["photo"] != household.photo:
        household.photo = file_has_access_or_download(args["photo"], household.photo)
    if (
        "language" in args
        and not household.language
        and args["language"] in SUPPORTED_LANGUAGES
    ):
        household.language = args["language"]
        gevent.spawn(importLanguage, household.id, household.language)
    if "planner_feature" in args:
        household.planner_feature = args["planner_feature"]
    if "expenses_feature" in args:
        household.expenses_feature = args["expenses_feature"]
    if "view_ordering" in args:
        household.view_ordering = args["view_ordering"]

    try:
        household.save()
        return jsonify(household.obj_to_dict())
    except Exception as e:
        raise InvalidUsage(f"Failed to update household: {str(e)}")


@household.route("/<int:household_id>", methods=["DELETE"])
@jwt_required()
@authorize_household(required=RequiredRights.ADMIN)
def deleteHouseholdById(household_id):
    household = Household.find_by_id(household_id)
    if not household:
        raise NotFoundRequest()

    hms = HouseholdMember.find_by_household(household_id)
    for hm in hms:
        db.session.delete(hm)
    db.session.commit()
    socketio.close_room(household_id)
    return jsonify({"msg": "DONE"})


@household.route("/<int:household_id>/member/<int:user_id>", methods=["POST"])
@jwt_required()
@authorize_household(required=RequiredRights.ADMIN)
@validate_args(UpdateHouseholdMember)
def putHouseholdMember(args, household_id, user_id):
    hm = HouseholdMember.find_by_ids(household_id, user_id)
    if not hm:
        household = Household.find_by_id(household_id)
        if not household:
            raise NotFoundRequest()
        hm = HouseholdMember()
        hm.household_id = household_id
        hm.user_id = user_id

    if "admin" in args:
        hm.admin = args["admin"]

    hm.save()

    return jsonify(hm.obj_to_user_dict())


@household.route("/<int:household_id>/member/<int:user_id>", methods=["DELETE"])
@jwt_required()
@authorize_household(required=RequiredRights.ADMIN_OR_SELF)
def deleteHouseholdMember(household_id, user_id):
    hm = HouseholdMember.find_by_ids(household_id, user_id)
    if hm:
        hm.delete()
    return jsonify({"msg": "DONE"})
