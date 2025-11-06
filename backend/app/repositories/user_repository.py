from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

from app.extensions import db
from app.entities.user_entity import UserEntity
from app.entities.news_entity import NewsEntity
from app.models.user import User
from app.models.exceptions import UserNotFoundError, NewsNotFoundError, NewsAlreadyFavoritedError, NewsNotFavoritedError


class UserRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create(self, user_model: User) -> User:
        try:
            user_entity = user_model.to_orm()
            self.session.add(user_entity)
            self.session.commit()
            self.session.refresh(user_entity)
            return User.from_entity(user_entity)
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco de dados ao criar usuário: {e}", exc_info=True)
            self.session.rollback()
            raise

    def find_by_email(self, email: str) -> User | None:
        stmt = select(UserEntity).where(func.lower(UserEntity.email) == email.lower())
        entity = self.session.execute(stmt).scalar_one_or_none()
        return User.from_entity(entity) if entity else None
    
    def find_by_id(self, user_id: int) -> User | None:
        stmt = select(UserEntity).where(UserEntity.id == user_id)
        entity = self.session.execute(stmt).scalar_one_or_none()
        return User.from_entity(entity) if entity else None

    def update(self, user_model: User) -> User:
        if not user_model.id:
            raise ValueError("O modelo de usuário deve ter um ID para ser atualizado.")
        
        try:
            user_entity = user_model.to_orm()
            updated_entity = self.session.merge(user_entity)
            self.session.commit()
            return User.from_entity(updated_entity)
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco de dados ao atualizar usuário (ID: {user_model.id}): {e}", exc_info=True)
            self.session.rollback()
            raise
    
    def list_all(self) -> list[User]:
        stmt = select(UserEntity)
        entities = self.session.execute(stmt).scalars().all()
        return [User.from_entity(entity) for entity in entities]
    
    def get_users_to_newsletter(self) -> list[User]:
        stmt = select(UserEntity).where(UserEntity.newsletter.is_(True))
        entities = self.session.execute(stmt).scalars().all()
        
        return [User.from_entity(entity) for entity in entities]

    def add_favorite_news(self, user_id: int, news_id: int):
        """Adiciona uma notícia à lista de favoritos de um usuário."""
        try:
            user_entity = self.session.get(UserEntity, user_id)
            if not user_entity:
                raise UserNotFoundError("Usuário não encontrado.")

            news_entity = self.session.get(NewsEntity, news_id)
            if not news_entity:
                raise NewsNotFoundError("Notícia não encontrada.")

            if news_entity not in user_entity.saved_news:
                user_entity.saved_news.append(news_entity)
                self.session.commit()
            else:
                raise NewsAlreadyFavoritedError("Notícia já favoritada pelo usuário.")
        except (SQLAlchemyError, IntegrityError) as e:
            self.session.rollback()
            logging.error(f"Erro de banco ao favoritar notícia (user_id={user_id}, news_id={news_id}): {e}", exc_info=True)
            raise

    def remove_favorite_news(self, user_id: int, news_id: int):
        """Remove uma notícia da lista de favoritos de um usuário."""
        try:
            user_entity = self.session.get(UserEntity, user_id)
            if not user_entity:
                raise UserNotFoundError("Usuário não encontrado.")

            news_entity = self.session.get(NewsEntity, news_id)
            if not news_entity or news_entity not in user_entity.saved_news:
                raise NewsNotFavoritedError("Notícia não encontrada nos favoritos do usuário.")
            
            user_entity.saved_news.remove(news_entity)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Erro de banco ao desfavoritar notícia (user_id={user_id}, news_id={news_id}): {e}", exc_info=True)
            raise
