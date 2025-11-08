from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class UserEntity(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(db.String(80), nullable=False)
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    birthdate: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    password_hash: Mapped[str] = mapped_column(db.String(200), nullable=False)
    newsletter: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    saved_news = relationship(
        "NewsEntity",
        secondary="user_saved_news",
        back_populates="saved_by_users"
    )
    
    read_history = relationship(
        "UserReadHistoryEntity", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
