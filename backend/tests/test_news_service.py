import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import math, logging

from app.services.news_service import NewsService
from app.models.exceptions import NewsNotFoundError

# Fixture para mockar o NewsRepository
@pytest.fixture
def mock_news_repo():
    return MagicMock()

# Fixture para mockar o TopicRepository
@pytest.fixture
def mock_topic_repo():
    return MagicMock()

# Fixture para mockar o UserNewsSourceRepository
@pytest.fixture
def mock_user_news_source_repo():
    return MagicMock()

# Fixture para mockar o UserReadHistoryRepository
@pytest.fixture
def mock_user_history_repo():
    return MagicMock()

# Fixture para criar a instância do NewsService com dependências mockadas
@pytest.fixture
def news_service(mock_news_repo, mock_topic_repo, mock_user_news_source_repo, mock_user_history_repo):
    with patch('app.services.news_service.UserCustomTopicService') as mock_custom_topic_service:
        service = NewsService(
            news_repo=mock_news_repo,
            topic_repo=mock_topic_repo,
            user_news_source_repo=mock_user_news_source_repo,
            user_history_repo=mock_user_history_repo
        )
        # Substituir a instância real pela mockada
        service.user_custom_topic_service = mock_custom_topic_service()
        yield service

# Fixture para criar um objeto de notícia mockado, simulando o retorno do repositório
@pytest.fixture
def sample_news():
    news = MagicMock()
    news.id = 1
    news.title = "Test Title"
    news.description = "Test Description"
    news.url = "http://example.com/news/1"
    news.image_url = "http://example.com/image.jpg"
    news.content = "Test content."
    news.published_at = datetime(2023, 10, 26, 10, 0, 0)
    news.source_id = 1
    news.created_at = datetime(2023, 10, 26, 12, 0, 0)
    news.is_favorited = False
    news.source_name = "Test Source"
    news.topic_name = "Technology"
    return news


def test_get_news_by_id_found(news_service, mock_news_repo, sample_news):
    """Testa se get_news_by_id retorna os dados corretos quando a notícia é encontrada."""
    # Arrange
    mock_news_repo.find_by_id.return_value = sample_news

    # Act
    result = news_service.get_news_by_id(user_id=1, news_id=1)

    # Assert
    mock_news_repo.find_by_id.assert_called_once_with(1, user_id=1)
    assert result["id"] == sample_news.id
    assert result["title"] == sample_news.title
    assert result["is_favorited"] == sample_news.is_favorited
    assert result["source_name"] == sample_news.source_name


def test_get_news_by_id_not_found(news_service, mock_news_repo):
    """Testa se get_news_by_id levanta NewsNotFoundError quando a notícia não existe."""
    # Arrange
    mock_news_repo.find_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NewsNotFoundError, match="Notícia com ID 999 não encontrada."):
        news_service.get_news_by_id(user_id=1, news_id=999)


def test_get_all_news(news_service, mock_news_repo, sample_news):
    """Testa a listagem de todas as notícias com paginação."""
    # Arrange
    paginated_list = [sample_news, sample_news]
    total_count = 20
    mock_news_repo.list_all.return_value = paginated_list
    mock_news_repo.count_all.return_value = total_count

    # Act
    result = news_service.get_all_news(user_id=1, page=2, per_page=10)

    # Assert
    mock_news_repo.list_all.assert_called_once_with(page=2, per_page=10, user_id=1)
    mock_news_repo.count_all.assert_called_once()
    assert len(result["news"]) == 2
    assert result["news"][0]["id"] == sample_news.id
    assert result["pagination"]["page"] == 2
    assert result["pagination"]["per_page"] == 10
    assert result["pagination"]["total"] == total_count
    assert result["pagination"]["pages"] == math.ceil(total_count / 10)


def test_get_news_by_topic(news_service, mock_news_repo, sample_news):
    """Testa a busca de notícias por tópico."""
    # Arrange
    paginated_list = [sample_news]
    total_count = 5
    mock_news_repo.find_by_topic.return_value = paginated_list
    mock_news_repo.count_by_topic.return_value = total_count

    # Act
    result = news_service.get_news_by_topic(topic_id=1, page=1, per_page=10, user_id=1)

    # Assert
    mock_news_repo.find_by_topic.assert_called_once_with(1, 1, 10, 1)
    mock_news_repo.count_by_topic.assert_called_once_with(1)
    assert len(result["news"]) == 1
    assert result["news"][0]["id"] == sample_news.id
    assert result["pagination"]["total"] == total_count


def test_get_news_by_topic_empty(news_service, mock_news_repo):
    """Testa a busca por um tópico que não tem notícias."""
    # Arrange
    mock_news_repo.find_by_topic.return_value = []
    mock_news_repo.count_by_topic.return_value = 0

    # Act
    result = news_service.get_news_by_topic(topic_id=99, page=1, per_page=10, user_id=1)

    # Assert
    mock_news_repo.find_by_topic.assert_called_once_with(99, 1, 10, 1)
    mock_news_repo.count_by_topic.assert_called_once_with(99)
    assert len(result["news"]) == 0
    assert result["pagination"]["total"] == 0
    assert result["pagination"]["pages"] == 1 # Deve ser 1 mesmo com 0 resultados

def test_get_favorite_news(news_service, mock_news_repo, sample_news):
    """Testa a listagem de notícias favoritas de um usuário."""
    # Arrange
    # Simula o comportamento do método, que chama duas vezes
    paginated_favorites = [sample_news]
    all_favorites = [sample_news, sample_news] # Total de 2 favoritos
    mock_news_repo.list_favorites_by_user.side_effect = [
        paginated_favorites,
        all_favorites
    ]

    # Act
    result = news_service.get_favorite_news(user_id=1, page=1, per_page=10)

    # Assert
    assert mock_news_repo.list_favorites_by_user.call_count == 2
    assert len(result["news"]) == 1
    assert result["news"][0]["is_favorited"] is True
    assert result["pagination"]["total"] == 2


def test_get_favorite_news_empty(news_service, mock_news_repo):
    """Testa a listagem de favoritos para um usuário sem notícias favoritas."""
    # Arrange
    mock_news_repo.list_favorites_by_user.side_effect = [
        [], # Paginated
        []  # All for count
    ]

    # Act
    result = news_service.get_favorite_news(user_id=1, page=1, per_page=10)

    # Assert
    assert mock_news_repo.list_favorites_by_user.call_count == 2
    assert len(result["news"]) == 0
    assert result["pagination"]["total"] == 0
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["pages"] == 1



def test_calculate_topic_score():
    """Testa o cálculo de score baseado em custom topics."""
    # Arrange
    service = NewsService()
    news = MagicMock()
    news.title = "Apple lança novo iPhone"
    news.description = "O novo aparelho tem IA."
    news.content = "Mais detalhes sobre tecnologia."
    custom_topics = [
        {'name': 'iPhone'},
        {'name': 'IA'},
        {'name': 'Samsung'} # Não deve dar match
    ]

    # Act
    score = service._calculate_topic_score(news, custom_topics)

    # Assert
    assert score == 400 # 200 para 'iPhone' + 200 para 'IA'


def test_calculate_topic_score_no_match():
    """Testa o cálculo de score quando não há matches."""
    # Arrange
    service = NewsService()
    news = MagicMock(title="Notícia genérica", description="Sem palavras-chave", content="")
    custom_topics = [{'name': 'tecnologia'}, {'name': 'política'}]

    # Act
    score = service._calculate_topic_score(news, custom_topics)

    # Assert
    assert score == 0


def test_get_for_you_news_success(news_service, mock_news_repo, mock_user_news_source_repo, sample_news):
    """Testa o feed 'For You' com cálculo de score e ordenação."""
    # Arrange
    # Mock das dependências
    mock_user_news_source_repo.get_user_preferred_source_ids.return_value = [1, 5]
    news_service.user_custom_topic_service.get_user_preferred_topics.return_value = [{'name': 'Test'}]

    # Notícia 1: score alto (fonte preferida + match de tópico)
    news1 = MagicMock()
    news1.id = 1
    news1.title = "News with Test keyword"
    news1.description = ""
    news1.content = ""
    news1.published_at = datetime.now()
    news1.time_score = 300
    news1.source_score = 100 # Fonte preferida
    news1.is_favorited = False

    # Notícia 2: score baixo (sem bônus)
    news2 = MagicMock()
    news2.id = 2
    news2.title = "Another news"
    news2.description = ""
    news2.content = ""
    news2.published_at = datetime.now()
    news2.time_score = 75
    news2.source_score = 0
    news2.is_favorited = True

    mock_news_repo.get_recent_news_with_base_score.return_value = [news2, news1] # Desordenado

    # Act
    result = news_service.get_for_you_news(user_id=1, page=1, per_page=10)

    # Assert
    # Verificações das chamadas
    mock_user_news_source_repo.get_user_preferred_source_ids.assert_called_once_with(1)
    news_service.user_custom_topic_service.get_user_preferred_topics.assert_called_once_with(1)
    mock_news_repo.get_recent_news_with_base_score.assert_called_once()

    # Verificações do resultado
    assert len(result["news"]) == 2
    # A primeira notícia deve ser a news1, que tem score maior
    assert result["news"][0]["id"] == 1
    assert result["news"][0]["score"] == 300 + 100 + 200 # time + source + topic

    # A segunda notícia deve ser a news2
    assert result["news"][1]["id"] == 2
    assert result["news"][1]["score"] == 75 + 0 + 0 # time + source + topic

    # Verificação da paginação manual
    assert result["pagination"]["total"] == 2


def test_get_for_you_news_pagination(news_service, mock_news_repo, mock_user_news_source_repo):
    """Testa a paginação manual do feed 'For You'."""
    # Arrange
    mock_user_news_source_repo.get_user_preferred_source_ids.return_value = []
    news_service.user_custom_topic_service.get_user_preferred_topics.return_value = []

    # Criar 15 notícias mockadas, todas com o mesmo score para simplificar
    recent_news_list = []
    for i in range(15):
        news = MagicMock(id=i, time_score=100, source_score=0, published_at=datetime.now())
        recent_news_list.append(news)

    mock_news_repo.get_recent_news_with_base_score.return_value = recent_news_list

    # Act - Pedindo a segunda página
    result = news_service.get_for_you_news(user_id=1, page=2, per_page=10)

    # Assert
    assert len(result["news"]) == 5 # A segunda página deve ter 5 itens
    assert result["pagination"]["page"] == 2
    assert result["pagination"]["per_page"] == 10
    assert result["pagination"]["total"] == 15
    assert result["pagination"]["pages"] == 2


def test_get_for_you_news_exception_fallback(news_service, mock_news_repo, mock_user_news_source_repo):
    """Testa se get_for_you_news retorna get_all_news em caso de exceção."""
    # Arrange
    # Forçar uma exceção em uma das chamadas iniciais
    mock_user_news_source_repo.get_user_preferred_source_ids.side_effect = Exception("DB Error")

    # Mockar o retorno de get_all_news para verificar se foi chamado
    fallback_data = {"news": [{"id": 99, "title": "Fallback News"}], "pagination": {}}
    with patch.object(news_service, 'get_all_news', return_value=fallback_data) as mock_get_all_news:
        # Act
        result = news_service.get_for_you_news(user_id=1, page=1, per_page=10)

        # Assert
        # Verifica se o fallback foi acionado
        mock_get_all_news.assert_called_once_with(1, 1, 10)
        # Verifica se o resultado é o do fallback
        assert result["news"][0]["id"] == 99


def test_save_history_success(news_service, mock_user_history_repo):
    """Testa se save_history chama o repositório corretamente."""
    # Arrange
    mock_user_history_repo.create.return_value = {"user_id": 1, "news_id": 100}
    
    # Força o service a usar o mock, já que o __init__ o ignora.
    with patch.object(news_service, 'user_history_repo', mock_user_history_repo):
        # Act
        result = news_service.save_history(user_id=1, news_id=100)

        # Assert
        mock_user_history_repo.create.assert_called_once_with(1, 100)
        assert result is not None


def test_save_history_raises_not_found(news_service, mock_user_history_repo):
    """Testa se save_history propaga exceções de 'não encontrado'."""
    # Arrange
    mock_user_history_repo.create.side_effect = NewsNotFoundError("Notícia não encontrada")

    with patch.object(news_service, 'user_history_repo', mock_user_history_repo):
        # Act & Assert
        with pytest.raises(NewsNotFoundError):
            news_service.save_history(user_id=1, news_id=999)


def test_save_history_generic_exception(news_service, mock_user_history_repo):
    """Testa o tratamento de exceção genérica em save_history."""
    # Arrange
    mock_user_history_repo.create.side_effect = Exception("Erro de banco de dados")

    with patch.object(news_service, 'user_history_repo', mock_user_history_repo):
        # Act & Assert
        with pytest.raises(Exception, match="Ocorreu um erro interno ao marcar noticia como lida."):
            news_service.save_history(user_id=1, news_id=100)


def test_get_history_news_success(news_service, mock_user_history_repo, sample_news):
    """Testa a busca bem-sucedida do histórico de notícias."""
    # Arrange
    history_entity = MagicMock()
    history_entity.read_at = datetime.now()

    # O repositório retorna uma tupla (history_entity, news_entity)
    mock_user_history_repo.get_user_history.return_value = ([(history_entity, sample_news)], 1)

    # Mockar a conversão de entidade, a checagem de favorito (que usa db.session)
    # e forçar o uso do repo mockado.
    with patch('app.services.news_service.News.from_entity', return_value=sample_news), \
         patch('app.services.news_service.db.session.query') as mock_query, \
         patch.object(news_service, 'user_history_repo', mock_user_history_repo):
        
        # Simular que a notícia não é favorita
        mock_query.return_value.filter_by.return_value.first.return_value = None

        # Act
        result = news_service.get_history_news(user_id=1, page=1, per_page=10)

    # Assert
    mock_user_history_repo.get_user_history.assert_called_once_with(user_id=1, page=1, per_page=10)
    assert len(result["news"]) == 1
    news_item = result["news"][0]
    assert news_item["id"] == sample_news.id
    assert news_item["title"] == sample_news.title
    assert "read_at" in news_item
    assert news_item["is_favorited"] is False
    assert result["pagination"]["total"] == 1


def test_get_history_news_is_favorited(news_service, mock_user_history_repo, sample_news):
    """Testa se o histórico de notícias identifica corretamente uma notícia favoritada."""
    # Arrange
    history_entity = MagicMock(read_at=datetime.now())
    mock_user_history_repo.get_user_history.return_value = ([(history_entity, sample_news)], 1)

    with patch('app.services.news_service.News.from_entity', return_value=sample_news), \
         patch('app.services.news_service.db.session.query') as mock_query, \
         patch.object(news_service, 'user_history_repo', mock_user_history_repo):
        
        # Simular que a notícia É favorita
        mock_query.return_value.filter_by.return_value.first.return_value = MagicMock()
        
        # Act
        result = news_service.get_history_news(user_id=1)

    # Assert
    assert len(result["news"]) == 1
    assert result["news"][0]["is_favorited"] is True


def test_get_history_news_exception(news_service, mock_user_history_repo):
    """Testa o tratamento de exceção ao buscar o histórico."""
    # Arrange
    db_error = Exception("DB Error")
    mock_user_history_repo.get_user_history.side_effect = db_error
    
    with patch.object(news_service, 'user_history_repo', mock_user_history_repo):
        # Silenciar o log de erro durante o teste
        logging.disable(logging.ERROR)
        # Act & Assert
        with pytest.raises(Exception, match=f"Erro ao buscar histórico: {db_error}"):
            news_service.get_history_news(user_id=1)
        logging.disable(logging.NOTSET) # Reativar logs
