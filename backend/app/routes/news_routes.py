from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_access_cookies
from app.controllers.news_controller import NewsController
from app.routes.user_routes import get_user_id_from_token

news_bp = Blueprint("news", __name__)
news_controller = NewsController()


@news_bp.route("/", methods=["GET"])
@jwt_required()
@get_user_id_from_token
def get_news(user_id: int):
    return news_controller.get_news(user_id)


@news_bp.route("/<int:news_id>", methods=["GET"])
@jwt_required()
@get_user_id_from_token
def get_news_by_id(user_id: int, news_id: int):
    return news_controller.get_by_id(user_id, news_id)

@news_bp.route("/<int:news_id>/favorite", methods=["POST"])
@jwt_required()
@get_user_id_from_token
def favorite_news(user_id, news_id):
    return news_controller.favorite_news(user_id, news_id)


@news_bp.route("/<int:news_id>/favorite", methods=["PUT"])
@jwt_required()
@get_user_id_from_token
def unfavorite_news(user_id, news_id):
    return news_controller.unfavorite_news(user_id, news_id)

@news_bp.route("/topic/<int:topic_id>", methods=["GET"])
def get_news_by_topic(topic_id: int):
    return news_controller.get_by_topic(topic_id)

@news_bp.route("/saved", methods=["GET"])
@jwt_required()
@get_user_id_from_token
def get_favorite_news(user_id):
    return news_controller.get_favorite_news(user_id)