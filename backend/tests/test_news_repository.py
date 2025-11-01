import unittest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.news_repository import NewsRepository
from app.models.news import News

# --- INÍCIO DA CORREÇÃO ---
# Importar todas as entidades ORM necessárias para que o SQLAlchemy
# possa configurar os mappers corretamente antes que os testes sejam executados.
# Isso resolve o InvalidRequestError causado pelo joinedload().
try:
    from app.entities.news_entity import NewsEntity
    from app.entities.news_source_entity import NewsSourceEntity
    from app.entities.user_saved_news_entity import UserSavedNewsEntity
    from app.entities.user_entity import UserEntity
    # A entidade que estava faltando e causando o erro:
    from app.entities.user_read_history_entity import UserReadHistoryEntity 
except ImportError:
    # Se os caminhos estiverem ligeiramente errados, ajuste-os.
    # Esta é uma tentativa de garantir que o teste possa ser analisado
    # mesmo que os imports falhem temporariamente.
    pass
# --- FIM DA CORREÇÃO ---


@pytest.fixture
def mock_session():
    """Fixture para criar um mock da sessão do SQLAlchemy."""
    return MagicMock()


@pytest.fixture
def news_repository(mock_session):
    """Fixture para criar uma instância de NewsRepository com a sessão mockada."""
    return NewsRepository(session=mock_session)


@pytest.fixture
def sample_news_model():
    """Fixture para um modelo News de exemplo."""
    return News(
        id=1,
        title="Test News",
        url="http://www.example.com/news/1",
        content="This is a test.",
        published_at=datetime.now(),
        source_id=1,
        topic_id=1
    )


@pytest.fixture
def sample_news_entity():
    """Fixture para uma entidade NewsEntity de exemplo."""
    # Usar MagicMock para simular a entidade e evitar problemas de inicialização do SQLAlchemy.
    # Isso isola o teste do repositório das dependências do ORM.
    mock_entity = MagicMock()
    mock_entity.id = 1
    mock_entity.title = "Test News"
    mock_entity.url = "http://www.example.com/news/1"
    mock_entity.content = "This is a test."
    mock_entity.published_at = datetime.now()
    mock_entity.image_url = "http://example.com/image.jpg" # Definir valor explícito
    mock_entity.source_id = 1
    mock_entity.topic_id = 1
    mock_entity.source = MagicMock(id=1, name="Test Source")
    return mock_entity


def test_create_news_success(news_repository, mock_session, sample_news_model, sample_news_entity):
    """Testa a criação de uma notícia com sucesso."""
    # Arrange
    mock_session.add.return_value = None
    mock_session.commit.return_value = None

    # Mockar a conversão para a entidade ORM para evitar a chamada real
    sample_news_model.to_orm = MagicMock(return_value=sample_news_entity)

    # Simular que o refresh atribui o ID à entidade mockada.
    def refresh_side_effect(entity):
        entity.id = 1
    mock_session.refresh.side_effect = refresh_side_effect
    
    # Mockar a conversão de volta para o modelo de negócio para controlar o retorno
    # CORREÇÃO: Usar 'with' para garantir que o patch seja parado.
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        created_news = news_repository.create(sample_news_model)

    # Assert
    mock_session.add.assert_called_once_with(ANY)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert created_news is not None
    assert created_news.title == sample_news_model.title


def test_create_news_sqlalchemy_error(news_repository, mock_session, sample_news_model, sample_news_entity):
    """Testa o tratamento de erro do SQLAlchemy ao criar notícia."""
    # Arrange
    # Mockar a conversão para a entidade ORM
    sample_news_model.to_orm = MagicMock(return_value=sample_news_entity)

    # O erro pode acontecer no add ou no commit. Testando no commit.
    mock_session.add.return_value = None
    mock_session.commit.side_effect = SQLAlchemyError("Simulated DB error")

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        news_repository.create(sample_news_model)

    # Verifica se add foi chamado antes do erro e se rollback foi chamado para tratar o erro
    mock_session.add.assert_called_once_with(ANY)
    mock_session.rollback.assert_called_once()


def test_find_by_id_found(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa encontrar uma notícia por ID quando ela existe."""
    # Arrange
    mock_result = MagicMock()
    mock_result.first.return_value = (sample_news_entity, False) # entity, is_favorited
    mock_session.execute.return_value = mock_result
    
    # Mockar a conversão de volta para o modelo de negócio
    # CORREÇÃO: Usar 'with'
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        found_news = news_repository.find_by_id(1, user_id=10)

    # Assert
    mock_session.execute.assert_called_once()
    assert found_news is not None
    assert found_news.id == sample_news_model.id
    assert found_news.is_favorited is False


def test_find_by_id_not_found(news_repository, mock_session):
    """Testa encontrar uma notícia por ID quando ela não existe."""
    # Arrange
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    found_news = news_repository.find_by_id(999)

    # Assert
    mock_session.execute.assert_called_once()
    assert found_news is None


def test_find_by_id_sqlalchemy_error(news_repository, mock_session):
    """Testa o tratamento de erro do SQLAlchemy ao buscar por ID."""
    # Arrange
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        news_repository.find_by_id(1)

    # Verifica se a sessão não tentou fazer commit ou rollback, pois é uma operação de leitura
    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_not_called()


@pytest.mark.parametrize("url, expected", [
    ("http://www.example.com/path/", "http://example.com/path"),
    ("https://example.com/path", "https://example.com/path"),
    ("http://example.com/path?query=1", "http://example.com/path"),
    ("HTTP://EXAMPLE.COM/PATH/", "http://example.com/path"),
    ("  http://www.example.com/path/  ", "http://example.com/path"),
    (None, None),
    ("", ""),
])
def test_normalize_url(news_repository, url, expected):
    """Testa a normalização de URLs."""
    assert news_repository._normalize_url(url) == expected


def test_normalize_url_with_malformed_url(news_repository):
    """Testa a normalização com uma URL que causa exceção, esperando um fallback."""
    malformed_url = "http://[::1]/"  # URL que pode causar erro no urlparse
    # A função normaliza a URL removendo a barra final.
    assert news_repository._normalize_url(malformed_url) == "http://[::1]"


def test_find_by_url_normalized(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa encontrar uma notícia por URL normalizada."""
    # Arrange
    # Simula que a busca exata falha, mas a normalizada encontra
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # Busca exata
        MagicMock(scalar_one_or_none=MagicMock(return_value=sample_news_entity)) # Busca normalizada
    ]
    # Mockar a conversão de volta para o modelo de negócio
    # CORREÇÃO: Usar 'with'
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        found_news = news_repository.find_by_url("http://www.example.com/news/1/")

    # Assert
    assert mock_session.execute.call_count == 2
    assert found_news is not None
    assert found_news.id == sample_news_model.id


def test_find_by_url_iterating(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa encontrar uma notícia por URL iterando e normalizando."""
    # Arrange
    # Simula que as buscas diretas falham, mas a iteração encontra
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # Busca exata
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # Busca normalizada direta
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[sample_news_entity])))) # Iteração
    ]
    # Mockar a conversão de volta para o modelo de negócio
    # CORREÇÃO: Usar 'with'
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        # A URL da entidade é 'http://www.example.com/news/1'
        # A URL de busca normalizada será 'http://example.com/news/1'
        found_news = news_repository.find_by_url("http://example.com/news/1?param=true")

    # Assert
    assert mock_session.execute.call_count == 3
    assert found_news is not None
    assert found_news.id == sample_news_model.id


def test_find_by_url_not_found(news_repository, mock_session):
    """Testa a busca por URL quando a notícia não é encontrada em nenhuma etapa."""
    # Arrange
    # Simula que todas as tentativas de busca retornam None
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    mock_session.execute.return_value.scalars.return_value.all.return_value = []

    # Act
    found_news = news_repository.find_by_url("http://nonexistent.com")

    # Assert
    assert found_news is None


def test_find_by_url_exact_match(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa encontrar uma notícia por URL quando há uma correspondência exata na primeira tentativa."""
    # Arrange
    # Simula que a busca exata encontra a entidade
    mock_session.execute.return_value.scalar_one_or_none.return_value = sample_news_entity
    
    # Mockar a conversão de volta para o modelo de negócio
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        found_news = news_repository.find_by_url("http://www.example.com/news/1")

    # Assert
    mock_session.execute.assert_called_once()
    assert found_news is not None
    assert found_news.id == sample_news_model.id


def test_list_all(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa a listagem de todas as notícias."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = [(sample_news_entity, True)] # entity, is_favorited
    mock_session.execute.return_value = mock_result

    # Mockar a conversão de volta para o modelo de negócio
    # CORREÇÃO: Usar 'with'
    with patch('app.models.news.News.from_entity', return_value=sample_news_model) as mock_from_entity:
        # Act
        # Esta chamada agora não deve mais falhar, pois os imports das entidades
        # no topo do arquivo permitiram ao SQLAlchemy configurar os mappers.
        news_list = news_repository.list_all(page=1, per_page=10, user_id=10)

    # Assert
    mock_session.execute.assert_called_once()
    mock_from_entity.assert_called_once_with(sample_news_entity) # Verificar se a conversão foi chamada
    assert len(news_list) == 1
    assert news_list[0].id == sample_news_model.id
    assert news_list[0].is_favorited is True


def test_list_all_without_user_id(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa a listagem de notícias sem um user_id (usuário não logado)."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = [(sample_news_entity, False)] # is_favorited deve ser False
    mock_session.execute.return_value = mock_result

    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        news_list = news_repository.list_all(page=1, per_page=10, user_id=None)

    # Assert
    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    assert news_list[0].is_favorited is False


def test_list_all_empty(news_repository, mock_session):
    """Testa a listagem quando não há notícias."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    # Act
    news_list = news_repository.list_all()

    # Assert
    mock_session.execute.assert_called_once()
    assert news_list == []


def test_list_all_sqlalchemy_error(news_repository, mock_session):
    """Testa o tratamento de erro do SQLAlchemy ao listar notícias."""
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")
    with pytest.raises(SQLAlchemyError):
        news_repository.list_all()


def test_find_by_topic(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa a busca de notícias por tópico."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = [(sample_news_entity, False)]
    mock_session.execute.return_value = mock_result

    # Mockar a conversão de volta para o modelo de negócio
    # CORREÇÃO: Usar 'with'
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        news_list = news_repository.find_by_topic(topic_id=1, user_id=10)

    # Assert
    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    assert news_list[0].topic_id == sample_news_model.topic_id


def test_find_by_topic_empty(news_repository, mock_session):
    """Testa a busca por um tópico que não tem notícias."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    # Act
    news_list = news_repository.find_by_topic(topic_id=99, user_id=10)

    # Assert
    mock_session.execute.assert_called_once()
    assert news_list == []


def test_count_all(news_repository, mock_session):
    """Testa a contagem de todas as notícias."""
    # Arrange
    mock_session.execute.return_value.scalar.return_value = 150

    # Act
    count = news_repository.count_all()

    # Assert
    assert count == 150
    mock_session.execute.assert_called_once()


def test_count_all_sqlalchemy_error(news_repository, mock_session):
    """Testa o tratamento de erro do SQLAlchemy ao contar todas as notícias."""
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")
    with pytest.raises(SQLAlchemyError):
        news_repository.count_all()


def test_count_by_topic(news_repository, mock_session):
    """Testa a contagem de notícias por tópico."""
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5
    mock_session.execute.return_value = mock_result

    # Act
    count = news_repository.count_by_topic(topic_id=1)

    # Assert
    mock_session.execute.assert_called_once()
    assert count == 5


def test_count_by_topic_sqlalchemy_error(news_repository, mock_session):
    """Testa o tratamento de erro do SQLAlchemy ao contar notícias por tópico."""
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")
    with pytest.raises(SQLAlchemyError):
        news_repository.count_by_topic(topic_id=1)


def test_list_favorites_by_user(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa a listagem de notícias favoritas de um usuário."""
    # Arrange
    # O método list_favorites_by_user usa .scalars().all(), então o mock precisa refletir isso.
    mock_result = MagicMock()
    # mock_session.execute(...).scalars().all()
    mock_result.scalars.return_value.all.return_value = [sample_news_entity]
    mock_session.execute.return_value = mock_result

    # Mockar a conversão de volta para o modelo de negócio
    # CORREÇÃO: Usar 'with'
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        news_list = news_repository.list_favorites_by_user(user_id=10)

    # Assert
    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    assert news_list[0].id == sample_news_model.id


def test_list_favorites_by_user_empty(news_repository, mock_session):
    """Testa a listagem de notícias favoritas quando o usuário não tem nenhuma."""
    # Arrange
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    # Act
    news_list = news_repository.list_favorites_by_user(user_id=10)

    # Assert
    mock_session.execute.assert_called_once()
    assert news_list == []


def test_get_recent_news_with_base_score(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa a busca de notícias recentes com cálculo de score."""
    # Arrange
    # Manually set a recent date for the entity to test scoring
    sample_news_entity.published_at = datetime.now() - timedelta(hours=12)
    
    # (news_entity, time_score, source_score, is_favorited)
    result_row = (sample_news_entity, 300, 100, True)
    
    mock_result = MagicMock()
    mock_result.all.return_value = [result_row]
    mock_session.execute.return_value = mock_result

    # Mockar a conversão de volta para o modelo de negócio
    # CORREÇÃO: Usar 'with'
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        news_list = news_repository.get_recent_news_with_base_score(
            user_id=10, 
            preferred_source_ids=[1], 
            days_limit=15
        )

    # Assert
    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    
    scored_news = news_list[0]
    assert scored_news.id == sample_news_model.id
    assert scored_news.is_favorited is True
    assert scored_news.time_score == 300  # "Últimas 24h"
    assert scored_news.source_score == 100 # Fonte preferida


def test_get_recent_news_with_base_score_no_preferred_source(news_repository, mock_session, sample_news_entity, sample_news_model):
    """Testa a busca de notícias recentes quando a fonte não é preferida."""
    # Arrange
    sample_news_entity.published_at = datetime.now() - timedelta(days=3)
    
    # (news_entity, time_score, source_score, is_favorited)
    result_row = (sample_news_entity, 75, 0, False)
    
    mock_result = MagicMock()
    mock_result.all.return_value = [result_row]
    mock_session.execute.return_value = mock_result

    # Mockar a conversão de volta para o modelo de negócio
    # CORREÇÃO: Usar 'with'
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        # Act
        news_list = news_repository.get_recent_news_with_base_score(
            user_id=10, 
            preferred_source_ids=[99], # ID de fonte não correspondente
            days_limit=15
        )

    # Assert
    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    
    scored_news = news_list[0]
    assert scored_news.id == sample_news_model.id
    assert scored_news.is_favorited is False
    assert scored_news.time_score == 75  # "2-5 dias"
    assert scored_news.source_score == 0 # Fonte não preferida


def test_get_recent_news_with_base_score_empty(news_repository, mock_session):
    """Testa a busca de notícias recentes quando nenhuma é encontrada."""
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    # Act
    news_list = news_repository.get_recent_news_with_base_score(user_id=10, preferred_source_ids=[], days_limit=5)

    # Assert
    mock_session.execute.assert_called_once()
    assert news_list == []


def test_get_recent_news_with_base_score_sqlalchemy_error(news_repository, mock_session):
    """Testa o tratamento de erro do SQLAlchemy na busca de notícias com score."""
    # Arrange
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")

    with pytest.raises(SQLAlchemyError):
        news_repository.get_recent_news_with_base_score(user_id=10, preferred_source_ids=[], days_limit=5)