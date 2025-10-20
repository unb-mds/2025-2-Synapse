from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
import logging
from app.services.user_news_service import UserNews
from app.services.news_service import NewsService
from app.services.news_topics_service import NewsTopicsService
from flask_jwt_extended import set_access_cookies, create_access_token, unset_jwt_cookies
from app.models.exceptions import UserNotFoundError, EmailInUseError, NewsNotFoundError


class NewsController:
    def __init__(self):
        self.user_news_service = UserNews()
        self.news_service = NewsService()
        self.news_topics_service = NewsTopicsService()

    def favorite_news(self, user_id, news_id):
        try:
            print(user_id, news_id)
            fav = self.user_news_service.favorite_news(user_id, news_id)
            return jsonify({"success": True, "message": "Notícia favoritada.", "data": {"news_id": news_id}, "error": None}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Erro ao favoritar notícia.", "data": None, "error": str(e)}), 500

    def unfavorite_news(self, user_id, news_id, is_favorite: bool = False):
        try:
            fav = self.user_news_service.unfavorite_news(user_id, news_id, is_favorite)
            return jsonify({"success": True, "message": "Notícia removida dos favoritos.", "data": {"news_id": news_id}, "error": None}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Erro ao remover favorito.", "data": None, "error": str(e)}), 500

    def get_news(self, user_id: int):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            result = self.news_service.get_news_for_user(user_id, page, per_page)

            return jsonify({
                "success": True,
                "message": "Notícias obtidas com sucesso.",
                "data": result,
                "error": None
            }), 200
        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Erro ao obter notícias.",
                "data": None,
                "error": str(e)
            }), 500

    def get_by_id(self, user_id: int, news_id: int):
        try:
            news_data = self.news_service.get_news_by_id(user_id, news_id)
            return jsonify({
                "success": True,
                "message": "Notícia obtida com sucesso.",
                "data": news_data,
                "error": None
            }), 200
        except NewsNotFoundError as e:
            return jsonify({
                "success": False,
                "message": "Notícia não encontrada.",
                "data": None,
                "error": str(e)
            }), 404
    
    def get_by_topic(self, user_id: int, topic_id: int):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 10  # fixo conforme solicitado

            items = self.news_topics_service.find_by_topic(topic_id, page, per_page)

            return jsonify({
                "success": True,
                "message": "Notícias recuperadas com sucesso.",
                "data": items,
                "page": page,
                "per_page": per_page,
                "error": None,
            }), 200
        except Exception as e:
            logging.error(f"Erro inesperado ao listar notícias por tópico: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Erro interno do servidor.",
                "data": None,
                "error": "Ocorreu um erro inesperado."
            }), 500

    def get_favorite_news(self, user_id: int):
        try:
            news_data = self.user_news_service.get_favorite_news(user_id)
            return jsonify({
                "success": True,
                "message": "Notícias favoritas obtida com sucesso.",
                "data": news_data,
                "error": None
            }), 200
        except NewsNotFoundError as e:
            return jsonify({
                "success": False,
                "message": "Notícias favoritas não encontrada.",
                "data": None,
                "error": str(e)
            }), 404