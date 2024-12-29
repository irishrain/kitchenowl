from app.config import DISABLE_ONBOARDING
from app.helpers import validate_args
from flask import jsonify, Blueprint
from app.models import User, Token
from .schemas import OnboardSchema

onboarding = Blueprint("onboarding", __name__)


@onboarding.route("", methods=["GET"])
def isOnboarding():
    if DISABLE_ONBOARDING: return jsonify({"onboarding": False})
    onboarding = User.count() == 0
    return jsonify({"onboarding": onboarding})


@onboarding.route("", methods=["POST"])
@validate_args(OnboardSchema)
def onboard(args):
    if User.count() > 0 or DISABLE_ONBOARDING:
        return jsonify({"msg": "Onboarding not allowed"}), 400

    # Validate fields
    if not args["username"] or not args["username"].strip():
        return jsonify({"msg": "Username cannot be empty"}), 400
    if not args["name"] or not args["name"].strip():
        return jsonify({"msg": "Name cannot be empty"}), 400
    if not args["password"] or not args["password"].strip():
        return jsonify({"msg": "Password cannot be empty"}), 400

    # Check if username already exists
    if User.find_by_username(args["username"]):
        return jsonify({"msg": "Username already exists"}), 400

    try:
        user = User.create(args["username"], args["password"], args["name"], admin=True)
    except Exception as e:
        return jsonify({"msg": str(e)}), 400

    device = args.get("device", "Unknown")

    try:
        # Create refresh token
        refreshToken, refreshModel = Token.create_refresh_token(user, device)

        # Create first access token
        accessToken, _ = Token.create_access_token(user, refreshModel)
    except Exception as e:
        return jsonify({"msg": str(e)}), 400

    return jsonify({"access_token": accessToken, "refresh_token": refreshToken})
