import os
from flask import Flask
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint
from app.routes.user_routes import user_bp
from app.routes.topic_routes import topic_bp
from app.routes.news_source_routes import news_source_bp
from app.routes.news_routes import news_bp

STANDARD_TOPICS = [
    'Technology', 'Crypto', 'Games', 'Economy', 'Business', 'Health',
    'Science', 'Entertainment', 'World'
]

def create_app(config_overrides=None):
    app = Flask(__name__)

    CORS(
        app,
        origins=["http://localhost:5173"],
        supports_credentials=True
    )
    
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
    app.config["MAILTRAP_USER"]= os.getenv("MAILTRAP_USER")
    app.config["MAILTRAP_PASSWORD"]= os.getenv("MAILTRAP_PASSWORD")
    
    if config_overrides:
        app.config.update(config_overrides)

    SWAGGER_URL = '/api/docs' 
    API_URL = '/static/openapi.yaml'  

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Synapse API Documentation"
        }
    )
    app.register_blueprint(swaggerui_blueprint)

    from app.extensions import db
    db.init_app(app)
    jwt = JWTManager(app)

    from app.entities import (custom_topic_entity, news_entity, news_source_entity, topic_entity, user_entity, user_preferred_custom_topics, user_preferred_news_sources_entity, user_saved_news_entity, user_read_history_entity)

    with app.app_context():
        db.create_all()

        from app.models.topic import Topic
        from app.repositories.topic_repository import TopicRepository

        print("Verificando e inicializando tópicos padrão...")
        topic_repo = TopicRepository()

        existing_topic_names = {t.name.lower() for t in topic_repo.list_all()}

        new_topics_created_count = 0
        for topic_name in STANDARD_TOPICS:
            if topic_name.lower() not in existing_topic_names:
                try:
                    topic = Topic(name=topic_name, state=1)  
                    created_topic = topic_repo.create(topic)
                    print(f"Tópico padrão criado: '{created_topic.name}' (ID={created_topic.id})")
                    new_topics_created_count += 1
                except Exception as e:
                    print(f"Erro ao criar tópico padrão '{topic_name}': {e}")

        if new_topics_created_count == 0:
            print("Todos os tópicos padrão já existem.")

    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(topic_bp, url_prefix="/topics")
    app.register_blueprint(news_bp, url_prefix="/news")
    app.register_blueprint(news_source_bp, url_prefix="/news_sources")
    

    return app
