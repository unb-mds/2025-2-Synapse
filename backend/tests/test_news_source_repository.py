import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from unittest.mock import patch
from app.repositories.news_source_repository import NewsSourceRepository
from app.models.news_source import NewsSource
from app.entities.user_entity import UserEntity
from app.entities.news_source_entity import NewsSourceEntity
from app.entities.user_preferred_news_sources_entity import UserPreferredNewsSourceEntity

@pytest.fixture
def news_source_repo(db):
    return NewsSourceRepository(session=db.session)

def test_create_news_source_success(news_source_repo):
    source_model = NewsSource(name="Test Source", url="http://testsource.com")
    created_source = news_source_repo.create(source_model)
    assert created_source.id is not None
    assert created_source.name == "Test Source"

def test_create_duplicate_url_fails(news_source_repo):
    source1 = NewsSource(name="Source One", url="http://duplicate.com")
    news_source_repo.create(source1)
    source2 = NewsSource(name="Source Two", url="http://duplicate.com")
    with pytest.raises(IntegrityError):
        news_source_repo.create(source2)

def test_create_sqlalchemy_error(news_source_repo):
    """Testa o tratamento de erro do SQLAlchemy ao criar."""
    source_model = NewsSource(name="Error Source", url="http://errorsource.com")
    with patch.object(news_source_repo.session, 'commit', side_effect=SQLAlchemyError("DB Error")), \
         patch.object(news_source_repo.session, 'rollback') as mock_rollback:
        with pytest.raises(SQLAlchemyError):
            news_source_repo.create(source_model)
        mock_rollback.assert_called_once()

def test_find_by_id(news_source_repo, db):
    source_entity = NewsSourceEntity(name="Find Me", url="http://findme.com")
    db.session.add(source_entity)
    db.session.commit()
    found = news_source_repo.find_by_id(source_entity.id)
    assert found is not None
    assert found.id == source_entity.id

def test_find_by_id_not_found(news_source_repo):
    assert news_source_repo.find_by_id(9999) is None

def test_find_by_url(news_source_repo, db):
    source_entity = NewsSourceEntity(name="Find By URL", url="http://findbyurl.com")
    db.session.add(source_entity)
    db.session.commit()
    found = news_source_repo.find_by_url("http://findbyurl.com")
    assert found is not None
    assert found.url == "http://findbyurl.com"

def test_find_by_url_not_found(news_source_repo):
    assert news_source_repo.find_by_url("http://notfound.com") is None

def test_find_by_name(news_source_repo, db):
    source_entity = NewsSourceEntity(name="Find By Name", url="http://findbyname.com")
    db.session.add(source_entity)
    db.session.commit()
    # Teste case-insensitive
    found = news_source_repo.find_by_name("find by name")
    assert found is not None
    assert found.name == "Find By Name"

def test_find_by_name_not_found(news_source_repo):
    assert news_source_repo.find_by_name("Non Existent Name") is None

def test_list_all(news_source_repo, db):
    db.session.add(NewsSourceEntity(name="A", url="http://a.com"))
    db.session.add(NewsSourceEntity(name="B", url="http://b.com"))
    db.session.commit()
    sources = news_source_repo.list_all()
    assert len(sources) == 2
    assert sources[0].name == "A" # Verifica a ordenação
    assert sources[1].name == "B"

def test_list_all_empty(news_source_repo, db):
    # Garante que a tabela esteja vazia para este teste
    db.session.query(NewsSourceEntity).delete()
    db.session.commit()
    assert news_source_repo.list_all() == []

def test_list_by_user_id(news_source_repo, db):
    user = UserEntity(full_name="Test User", email="user@test.com")
    user.password_hash = "hash"
    s1 = NewsSourceEntity(name="S1", url="http://s1.com")
    s2 = NewsSourceEntity(name="S2", url="http://s2.com")
    db.session.add_all([user, s1, s2])
    db.session.commit()
    db.session.add(UserPreferredNewsSourceEntity(user_id=user.id, source_id=s1.id))
    db.session.commit()
    
    user_sources = news_source_repo.list_by_user_id(user.id)
    assert len(user_sources) == 1
    assert user_sources[0].name == "S1"

def test_list_by_user_id_empty(news_source_repo, db):
    user = UserEntity(full_name="User No Sources", email="nosources@test.com", password_hash="hash")
    db.session.add(user)
    db.session.commit()
    assert news_source_repo.list_by_user_id(user.id) == []

def test_list_unassociated_by_user_id(news_source_repo, db):
    user = UserEntity(full_name="Test User 2", email="user2@test.com")
    user.password_hash = "hash"
    s1 = NewsSourceEntity(name="S1-un", url="http://s1un.com")
    s2 = NewsSourceEntity(name="S2-un", url="http://s2un.com") 
    s3 = NewsSourceEntity(name="S3-un", url="http://s3un.com") 
    db.session.add_all([user, s1, s2, s3])
    db.session.commit()
    db.session.add(UserPreferredNewsSourceEntity(user_id=user.id, source_id=s1.id))
    db.session.commit()

    unassociated = news_source_repo.list_unassociated_by_user_id(user.id)
    assert len(unassociated) == 2
    names = {s.name for s in unassociated}
    assert "S2-un" in names
    assert "S3-un" in names

def test_list_unassociated_by_user_id_all_associated(news_source_repo, db):
    user = UserEntity(full_name="User All Sources", email="allsources@test.com", password_hash="hash")
    s1 = NewsSourceEntity(name="S1-all", url="http://s1all.com")
    db.session.add_all([user, s1])
    db.session.commit()
    db.session.add(UserPreferredNewsSourceEntity(user_id=user.id, source_id=s1.id))
    db.session.commit()
    assert news_source_repo.list_unassociated_by_user_id(user.id) == []

@pytest.mark.parametrize("method_name, method_args", [
    ("find_by_name", ["test"]),
    ("find_by_url", ["http://test.com"]),
    ("list_all", []),
    ("list_by_user_id", [1]),
    ("list_unassociated_by_user_id", [1]),
])
def test_sqlalchemy_error_handling_execute(news_source_repo, method_name, method_args):
    """Testa o tratamento de SQLAlchemyError para métodos que usam session.execute."""
    with patch.object(news_source_repo.session, 'execute', side_effect=SQLAlchemyError("DB Error")):
        with pytest.raises(SQLAlchemyError):
            getattr(news_source_repo, method_name)(*method_args)

def test_sqlalchemy_error_handling_get(news_source_repo):
    """Testa o tratamento de SQLAlchemyError para o método find_by_id (que usa session.get)."""
    with patch.object(news_source_repo.session, 'get', side_effect=SQLAlchemyError("DB Error")):
        with pytest.raises(SQLAlchemyError):
            news_source_repo.find_by_id(1)