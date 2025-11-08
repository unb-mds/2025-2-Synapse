import pytest
from unittest.mock import patch, MagicMock, call
import logging

from app.jobs.send_newsletter import send_newsletter_job, build_newsletter_email, gerar_texto_intro

# Mock de dados para os testes
class MockUser:
    def __init__(self, id, full_name, email):
        self.id = id
        self.full_name = full_name
        self.email = email

MOCK_USER_1 = MockUser(id=1, full_name="John Doe", email="john.doe@test.com")
MOCK_USER_2 = MockUser(id=2, full_name="Jane Smith", email="jane.smith@test.com")

MOCK_NEWS_DATA = [
    {
        'category': 'Technology',
        'title': 'New AI Breakthrough',
        'img_url': 'http://example.com/img1.png',
        'summary': 'An amazing new AI has been developed.',
        'source': 'Tech News',
        'date': '2025-10-26'
    },
    {
        'category': 'Science',
        'title': 'Mars Rover Finds Water',
        'img_url': 'http://example.com/img2.png',
        'summary': 'Evidence of liquid water on Mars.',
        'source': 'Science Today',
        'date': '2025-10-25'
    }
]

MOCK_INTRO_TEXT = "Aqui estão as notícias mais quentes da semana, selecionadas especialmente para você."

@pytest.fixture
def mock_services():
    """Fixture para mockar todos os serviços e repositórios usados pelo job."""
    with patch('app.jobs.send_newsletter.UserRepository') as MockUserRepo, \
         patch('app.jobs.send_newsletter.MailService') as MockMailService, \
         patch('app.jobs.send_newsletter.NewsService') as MockNewsService, \
         patch('app.jobs.send_newsletter.AIService') as MockAIService, \
         patch('app.jobs.send_newsletter.create_app') as mock_create_app:

        # Configurar o mock do app_context
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__.return_value = None
        mock_app.app_context.return_value.__exit__.return_value = None
        mock_create_app.return_value = mock_app

        # Instâncias mockadas
        mock_user_repo_instance = MockUserRepo.return_value
        mock_mail_service_instance = MockMailService.return_value
        mock_news_service_instance = MockNewsService.return_value
        mock_ai_service_instance = MockAIService.return_value

        yield {
            "user_repo": mock_user_repo_instance,
            "mail_service": mock_mail_service_instance,
            "news_service": mock_news_service_instance,
            "ai_service": mock_ai_service_instance,
        }

def test_send_newsletter_job_happy_path(mock_services, caplog):
    """
    Testa o caminho feliz: dois usuários recebem a newsletter com sucesso.
    """
    caplog.set_level(logging.INFO)
    
    # Configuração dos mocks
    mock_services["user_repo"].get_users_to_newsletter.return_value = [MOCK_USER_1, MOCK_USER_2]
    mock_services["news_service"].get_news_to_email.return_value = MOCK_NEWS_DATA
    mock_services["ai_service"].generate_content.return_value = MOCK_INTRO_TEXT
    mock_services["mail_service"].sendemail.return_value = True

    # Execução do job
    send_newsletter_job()

    # Verificações
    assert mock_services["user_repo"].get_users_to_newsletter.call_count == 1
    assert mock_services["news_service"].get_news_to_email.call_count == 2
    assert mock_services["ai_service"].generate_content.call_count == 2
    assert mock_services["mail_service"].sendemail.call_count == 2

    # Verifica se o email para o primeiro usuário foi chamado com os dados corretos
    first_call_args = mock_services["mail_service"].sendemail.call_args_list[0].kwargs
    assert first_call_args['recipient_email'] == MOCK_USER_1.email
    assert MOCK_USER_1.full_name in first_call_args['html_content']
    assert MOCK_INTRO_TEXT in first_call_args['html_content']
    assert "New AI Breakthrough" in first_call_args['html_content']

    assert "JOB DE ENVIO DE NEWSLETTER FINALIZADO" in caplog.text
    assert "RESULTADO: 2 enviados com sucesso, 0 falhas." in caplog.text

def test_send_newsletter_job_no_users(mock_services, caplog):
    """
    Testa o cenário onde não há usuários interessados na newsletter.
    """
    caplog.set_level(logging.INFO)
    mock_services["user_repo"].get_users_to_newsletter.return_value = []

    send_newsletter_job()

    assert "Nenhum usuário manifestou interesse na newsletter. Finalizando." in caplog.text
    assert mock_services["news_service"].get_news_to_email.call_count == 0
    assert mock_services["mail_service"].sendemail.call_count == 0

def test_send_newsletter_job_user_with_no_news(mock_services, caplog):
    """
    Testa o cenário onde um usuário não tem notícias para receber.
    """
    caplog.set_level(logging.INFO)
    mock_services["user_repo"].get_users_to_newsletter.return_value = [MOCK_USER_1]
    mock_services["news_service"].get_news_to_email.return_value = []

    send_newsletter_job()

    assert f"Nenhuma notícia encontrada para {MOCK_USER_1.email}. Pulando..." in caplog.text
    assert mock_services["mail_service"].sendemail.call_count == 0
    assert "RESULTADO: 0 enviados com sucesso, 0 falhas." in caplog.text

def test_send_newsletter_job_email_send_fails(mock_services, caplog):
    """
    Testa o cenário onde o serviço de e-mail falha ao enviar.
    """
    caplog.set_level(logging.INFO)
    mock_services["user_repo"].get_users_to_newsletter.return_value = [MOCK_USER_1]
    mock_services["news_service"].get_news_to_email.return_value = MOCK_NEWS_DATA
    mock_services["ai_service"].generate_content.return_value = MOCK_INTRO_TEXT
    mock_services["mail_service"].sendemail.return_value = False # Simula falha

    send_newsletter_job()

    assert mock_services["mail_service"].sendemail.call_count == 1
    assert "RESULTADO: 0 enviados com sucesso, 1 falhas." in caplog.text

def test_send_newsletter_job_exception_during_user_processing(mock_services, caplog):
    """
    Testa se o job continua para o próximo usuário se ocorrer um erro em um.
    """
    caplog.set_level(logging.INFO) # Alterado de ERROR para INFO
    mock_services["user_repo"].get_users_to_newsletter.return_value = [MOCK_USER_1, MOCK_USER_2]
    
    # Simula um erro para o primeiro usuário e sucesso para o segundo
    mock_services["news_service"].get_news_to_email.side_effect = [
        Exception("Erro de rede!"), 
        MOCK_NEWS_DATA
    ]
    mock_services["ai_service"].generate_content.return_value = MOCK_INTRO_TEXT
    mock_services["mail_service"].sendemail.return_value = True

    send_newsletter_job()

    assert f"ERRO no envio para {MOCK_USER_1.email}" in caplog.text
    assert "Erro de rede!" in caplog.text
    
    # Verifica se o email para o segundo usuário foi enviado mesmo assim
    assert mock_services["mail_service"].sendemail.call_count == 1
    last_call_args = mock_services["mail_service"].sendemail.call_args.kwargs
    assert last_call_args['recipient_email'] == MOCK_USER_2.email

    assert "RESULTADO: 1 enviados com sucesso, 1 falhas." in caplog.text

def test_build_newsletter_email():
    """
    Testa a função pura que constrói o HTML do e-mail.
    """
    html = build_newsletter_email(
        user_name="Tester",
        intro_text="Test intro.",
        news_items=MOCK_NEWS_DATA
    )

    assert '<!DOCTYPE html>' in html
    assert 'Olá Tester,' in html
    assert 'Test intro.' in html
    assert 'New AI Breakthrough' in html
    assert 'http://example.com/img1.png' in html
    assert 'Mars Rover Finds Water' in html
    assert 'http://example.com/img2.png' in html
    assert 'Tech News' in html
    assert 'Science Today' in html

def test_gerar_texto_intro_success():
    """
    Testa a geração de texto introdutório com sucesso.
    """
    mock_ai_service = MagicMock()
    mock_ai_service.generate_content.return_value = "  Intro gerada pela IA.  "

    intro = gerar_texto_intro(mock_ai_service, MOCK_USER_1, MOCK_NEWS_DATA)

    # Verifica se o prompt foi construído corretamente
    prompt_call = mock_ai_service.generate_content.call_args[0][0]
    assert MOCK_USER_1.full_name in prompt_call
    assert "New AI Breakthrough" in prompt_call
    assert "Mars Rover Finds Water" in prompt_call

    assert intro == "Intro gerada pela IA." # Verifica se o .strip() funcionou

def test_gerar_texto_intro_fallback():
    """
    Testa o fallback quando a IA não retorna texto.
    """
    mock_ai_service = MagicMock()
    mock_ai_service.generate_content.return_value = None # Simula falha da IA

    intro = gerar_texto_intro(mock_ai_service, MOCK_USER_1, MOCK_NEWS_DATA)

    expected_fallback = f"Olá {MOCK_USER_1.full_name}, aqui está sua seleção personalizada de notícias da semana."
    assert intro == expected_fallback
