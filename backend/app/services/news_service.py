from app.repositories.news_repository import NewsRepository
from app.repositories.news_source_repository import NewsSourceRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_news_source_repository import UserNewsSourceRepository
from app.repositories.user_read_history_repository import UserReadHistoryRepository
from app.services.user_custom_topic_service import UserCustomTopicService
from app.models.exceptions import UserNotFoundError, NewsNotFoundError
from app.repositories.user_preferred_custom_topic_repository import UserPreferredCustomTopicRepository
from app.models.news import News, NewsValidationError
from app.models.news_source import NewsSource, NewsSourceValidationError
from app.models.exceptions import NewsNotFoundError
from app.extensions import db
from typing import Optional
import logging
import math


class NewsService():
   
    def __init__(
        self,
        news_repo: NewsRepository | None = None,
        topic_repo: TopicRepository | None = None,
        user_news_source_repo: UserNewsSourceRepository | None = None,
        user_history_repo: UserReadHistoryRepository | None = None
    ):
        self.news_repo = news_repo or NewsRepository()
        self.topic_repo = topic_repo or TopicRepository()
        self.user_news_source_repo = user_news_source_repo or UserNewsSourceRepository()
        self.user_custom_topic_service = UserCustomTopicService()
        self.user_history_repo = UserReadHistoryRepository()

    def get_news_by_id(self, user_id: Optional[int], news_id: int) -> dict:
        news = self.news_repo.find_by_id(news_id, user_id=user_id)
        if not news:
            raise NewsNotFoundError(f"Notícia com ID {news_id} não encontrada.")

        news_dict = {
            "id": news.id,
            "title": news.title,
            "description": news.description,
            "url": news.url,
            "image_url": news.image_url,
            "content": news.content,
            "published_at": news.published_at.isoformat() if news.published_at else None,
            "source_id": news.source_id,
            "created_at": news.created_at.isoformat() if news.created_at else None,
            "is_favorited": news.is_favorited, 
        }

        if news.source_name:
            news_dict["source_name"] = news.source_name

        if news.topic_name:
            news_dict["topic_name"] = news.topic_name

        return news_dict

    def get_all_news(self, user_id: Optional[int], page: int = 1, per_page: int = 10):
        """
        Retorna todas as notícias paginadas.

        Args:
            user_id: ID do usuário
            page: Número da página (começa em 1)
            per_page: Quantidade de itens por página

        Returns:
            Dict com notícias, paginação e metadados
        """

        paginated_news = self.news_repo.list_all(page=page, per_page=per_page, user_id=user_id)

        total_count = self.news_repo.count_all()

        news_list = []
        for news in paginated_news:
            news_dict = {
                "id": news.id,
                "title": news.title,
                "description": news.description,
                "url": news.url,
                "image_url": news.image_url,
                "content": news.content,
                "published_at": news.published_at.isoformat() if news.published_at else None,
                "source_id": news.source_id,
                "created_at": news.created_at.isoformat() if news.created_at else None,
                "is_favorited": news.is_favorited, # Adiciona o campo de favorito
            }

            if news.source_name:
                news_dict["source_name"] = news.source_name

            if news.topic_name:
                news_dict["topic_name"] = news.topic_name

            news_list.append(news_dict)

        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

        return {
            "news": news_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": total_pages
            }
        }

    def get_for_you_news(self, user_id: int, page: int = 1, per_page: int = 10):
        """
        Retorna feed personalizado "For You" com ranking baseado em preferências do usuário.

        Sistema de scoring híbrido (últimos 15 dias):
        - Score temporal: 300 (24h), 150 (1-2d), 75 (2-5d), 25 (5+d)
        - Fonte preferida: +100 pontos
        - Custom topic match: +200 pontos por match

        Args:
            user_id: ID do usuário
            page: Número da página (começa em 1)
            per_page: Quantidade de itens por página

        Returns:
            Dict com notícias rankeadas por score, paginação e metadados
        """
        try:
            preferred_source_ids = self.user_news_source_repo.get_user_preferred_source_ids(user_id)
            custom_topics = self.user_custom_topic_service.get_user_preferred_topics(user_id)

            recent_news = self.news_repo.get_recent_news_with_base_score(
                user_id=user_id,
                preferred_source_ids=preferred_source_ids,
                days_limit=15
            )

            # Calcular score final adicionando score de custom topics
            for news in recent_news:
                base_score = (news.time_score or 0) + (news.source_score or 0)

                topic_score = self._calculate_topic_score(news, custom_topics)

                setattr(news, 'total_score', base_score + topic_score)

            # Ordenar por score total (decrescente) e published_at (decrescente) como desempate
            sorted_news = sorted(
                recent_news,
                key=lambda x: (getattr(x, 'total_score', 0), x.published_at),
                reverse=True
            )

            # Paginação manual
            total_count = len(sorted_news)
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            paginated_news = sorted_news[start_index:end_index]

            news_list = []
            for news in paginated_news:
                news_dict = {
                    "id": news.id,
                    "title": news.title,
                    "description": news.description,
                    "url": news.url,
                    "image_url": news.image_url,
                    "content": news.content,
                    "published_at": news.published_at.isoformat() if news.published_at else None,
                    "source_id": news.source_id,
                    "created_at": news.created_at.isoformat() if news.created_at else None,
                    "is_favorited": news.is_favorited,
                    "score": getattr(news, 'total_score', 0),  
                }

                if news.source_name:
                    news_dict["source_name"] = news.source_name

                if news.topic_name:
                    news_dict["topic_name"] = news.topic_name

                news_list.append(news_dict)

            total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

            return {
                "news": news_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_count,
                    "pages": total_pages
                }
            }

        except Exception as e:
            print(f"Erro no feed personalizado: {e}")
            return self.get_all_news(user_id, page, per_page)

    def _calculate_topic_score(self, news: News, custom_topics: list) -> int:
        """
        Calcula score baseado em matches de custom topics no conteúdo da notícia.

        Args:
            news: Modelo de notícia
            custom_topics: Lista de custom topics do usuário

        Returns:
            Score total baseado em matches (200 pontos por match)
        """
        if not custom_topics:
            return 0

        score = 0
        # Concatenar título, descrição e conteúdo para busca
        text_content = f"{news.title or ''} {news.description or ''} {news.content or ''}".lower()

        for topic in custom_topics:
            # O tópico é um dicionário, ex: {'id': 1, 'name': 'tecnologia'}
            topic_name = topic.get('name', '').lower()
            if topic_name and topic_name in text_content:
                score += 200 # Adiciona 200 pontos para cada match

        return score


    def get_news_by_topic(self, topic_id: int, page: int = 1, per_page: int = 10, user_id: Optional[int] = None) -> dict:
        """Busca notícias paginadas por um tópico específico."""
        paginated_news = self.news_repo.find_by_topic(topic_id, page, per_page, user_id)

        total_count = self.news_repo.count_by_topic(topic_id)

        news_list = []
        for news in paginated_news:
            news_dict = {
                "id": news.id,
                "title": news.title,
                "description": news.description,
                "url": news.url,
                "image_url": news.image_url,
                "published_at": news.published_at.isoformat() if news.published_at else None,
                "source_id": news.source_id,
                "topic_id": news.topic_id,
                "is_favorited": news.is_favorited,
            }
            if news.source_name:
                news_dict["source_name"] = news.source_name
            if news.topic_name:
                news_dict["topic_name"] = news.topic_name
            news_list.append(news_dict)

        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

        return {
            "news": news_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": total_pages
            }
        }

    def get_favorite_news(self, user_id: int, page: int = 1, per_page: int = 20) -> dict:
        """
        Retorna as notícias favoritas de um usuário.

        Args:
            user_id: ID do usuário
            page: Número da página (começa em 1)
            per_page: Quantidade de itens por página

        Returns:
            Dict com notícias favoritas, paginação e metadados
        """
        paginated_news = self.news_repo.list_favorites_by_user(user_id, page, per_page)

        # Para contar o total, vamos buscar todas as favoritas (sem paginação) e contar
        all_favorites = self.news_repo.list_favorites_by_user(user_id, page=1, per_page=1000000)
        total_count = len(all_favorites)

        news_list = []
        for news in paginated_news:
            news_dict = {
                "id": news.id,
                "title": news.title,
                "description": news.description,
                "url": news.url,
                "image_url": news.image_url,
                "content": news.content,
                "published_at": news.published_at.isoformat() if news.published_at else None,
                "source_id": news.source_id,
                "created_at": news.created_at.isoformat() if news.created_at else None,
                "is_favorited": True,  # Sempre True já que são favoritas
            }

            if news.source_name:
                news_dict["source_name"] = news.source_name

            if news.topic_name:
                news_dict["topic_name"] = news.topic_name

            news_list.append(news_dict)

        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

        return {
            "news": news_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": total_pages
            }
        }
    
    def save_history(self, user_id: int, news_id: int):
        try:
            created_history = self.user_history_repo.create(user_id, news_id)
            return created_history
        except (UserNotFoundError,NewsNotFoundError) as e:
            raise e
        except Exception as e:
            logging.error(f"Erro inesperado ao salvar noticia como lida (user_id={user_id}, news_id={news_id}): {e}", exc_info=True)
            raise Exception("Ocorreu um erro interno ao marcar noticia como lida.")
    
    def get_history_news(self, user_id: int, page: int = 1, per_page: int = 10) -> dict:
        try:
            results, total_count = self.user_history_repo.get_user_history(
                user_id=user_id,
                page=page,
                per_page=per_page
            )
            
            news_list = []
            for history_entity, news_entity in results:
                news_model = News.from_entity(news_entity)
                
                from app.entities.user_saved_news_entity import UserSavedNewsEntity
                favorite_check = db.session.query(UserSavedNewsEntity).filter_by(
                    user_id=user_id,
                    news_id=news_model.id,
                    is_favorite=True
                ).first()
                
                news_dict = {
                    "id": news_model.id,
                    "title": news_model.title,
                    "description": news_model.description,
                    "url": news_model.url,
                    "image_url": news_model.image_url,
                    "content": news_model.content,
                    "published_at": news_model.published_at.isoformat() if news_model.published_at else None,
                    "source_id": news_model.source_id,
                    "topic_id": news_model.topic_id,
                    "created_at": news_model.created_at.isoformat() if news_model.created_at else None,
                    "is_favorited": favorite_check is not None,
                    "read_at": history_entity.read_at.isoformat(),
                }
                
                if news_model.source_name:
                    news_dict["source_name"] = news_model.source_name
                
                if news_model.topic_name:
                    news_dict["topic_name"] = news_model.topic_name
                
                news_list.append(news_dict)
            
            total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
            
            logging.info(f"Histórico formatado: user_id={user_id}, total_news={len(news_list)}, total={total_count}")
            
            return {
                "news": news_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_count,
                    "pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            logging.error(f"Erro ao buscar histórico de leitura: {e}", exc_info=True)
            raise Exception(f"Erro ao buscar histórico: {str(e)}")

    # get for you news adaptada para retornar noticias em um formato diferente 
    def get_news_to_email(self, user_id: int, page: int = 1, per_page: int = 10):
        try:
            preferred_source_ids = self.user_news_source_repo.get_user_preferred_source_ids(user_id)
            custom_topics = self.user_custom_topic_service.get_user_preferred_topics(user_id)

            recent_news = self.news_repo.get_recent_news_with_base_score(
                user_id=user_id,
                preferred_source_ids=preferred_source_ids,
                days_limit=15
            )

            for news in recent_news:
                base_score = (news.time_score or 0) + (news.source_score or 0)
                topic_score = self._calculate_topic_score(news, custom_topics)
                setattr(news, 'total_score', base_score + topic_score)

            sorted_news = sorted(
                recent_news,
                key=lambda x: (getattr(x, 'total_score', 0), x.published_at),
                reverse=True
            )

            total_count = len(sorted_news)
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            paginated_news = sorted_news[start_index:end_index]

            news_list = []
            for news in paginated_news:
                news_dict = {
                    "category": getattr(news, "topic_name", "Geral"),
                    "title": news.title,
                    "img_url": news.image_url or "", 
                    "summary": news.description or "",
                    "source": getattr(news, "source_name", "Fonte Desconhecida"),
                    "date": news.published_at.strftime("%d/%m/%Y") if news.published_at else "",
                    "url": news.url
                }
                news_list.append(news_dict)

            return news_list

        except Exception as e:
            print(f"Erro no feed personalizado: {e}")
            return []