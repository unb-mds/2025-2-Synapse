from sqlalchemy.exc import IntegrityError
from app.repositories.user_news_repository import UserNewsRepository

class UserNews():
    def __init__(self,user_news_repo: UserNewsRepository | None = None):
        self.user_news_repo = user_news_repo or UserNewsRepository()

    def favorite_news(self, user_id, news_id):
        return self.user_news_repo.set_favorite(user_id, news_id, is_favorite=True)

    def unfavorite_news(self, user_id, news_id, is_favorite):
        return self.user_news_repo.remove_favorite(user_id, news_id, is_favorite)
    
    def get_favorite_news(self, user_id):
        return self.get_favorites_by_user(user_id)