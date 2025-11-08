import pytest
from unittest.mock import patch, MagicMock
import os

from app.services.ai_service import AIService

# Fixture to mock the google.generativeai library
@pytest.fixture
def mock_genai():
    """Mocks the entire google.generativeai library."""
    with patch('app.services.ai_service.genai') as mock_genai_lib:
        # Mock the model instance and its methods
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated content from AI."
        mock_model_instance.generate_content.return_value = mock_response
        
        # Mock the GenerativeModel class to return our mock instance
        mock_genai_lib.GenerativeModel.return_value = mock_model_instance
        yield mock_genai_lib

# Fixture to mock logging to check log messages
@pytest.fixture
def mock_logging():
    """Mocks the logging module used in the service."""
    with patch('app.services.ai_service.logging') as mock_log:
        yield mock_log

# --- Test __init__ ---

def test_init_success(mock_genai, mock_logging):
    """Test successful initialization when API key is present."""
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'}):
        service = AIService(timeout=90)

    # Assertions
    mock_genai.configure.assert_called_once_with(api_key='fake-api-key')
    mock_genai.GenerativeModel.assert_called_once_with(
        'gemini-2.5-flash',
        generation_config={'temperature': 0.1}
    )
    assert service.model is not None
    assert service.timeout == 90
    mock_logging.info.assert_called_once_with("AIService inicializado com sucesso (modelo=gemini-2.5-flash, timeout=90s).")

def test_init_no_api_key(mock_genai, mock_logging):
    """Test initialization when GEMINI_API_KEY is not set."""
    # Ensure the key is not in the environment for this test
    if 'GEMINI_API_KEY' in os.environ:
        del os.environ['GEMINI_API_KEY']
        
    service = AIService()

    # Assertions
    assert service.model is None
    mock_genai.configure.assert_not_called()
    mock_logging.warning.assert_called_once_with("GEMINI_API_KEY não configurada. Serviço de IA desabilitado.")

def test_init_genai_exception(mock_genai, mock_logging):
    """Test initialization failure if genai.configure raises an exception."""
    mock_genai.configure.side_effect = Exception("Configuration failed")
    
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'}):
        service = AIService()

    # Assertions
    assert service.model is None
    mock_logging.error.assert_called_once_with("Erro ao inicializar o modelo Gemini: Configuration failed", exc_info=True)

# --- Test generate_content ---

def test_generate_content_success(mock_genai, mock_logging):
    """Test successful content generation."""
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'}):
        service = AIService(timeout=45)
        prompt = "Tell me a joke."
        
        response = service.generate_content(prompt)

    # Assertions
    assert response == "Generated content from AI."
    service.model.generate_content.assert_called_once_with(
        prompt,
        request_options={'timeout': 45}
    )
    mock_logging.debug.assert_any_call("Chamando API Gemini (timeout=45s, prompt_len=15)")
    mock_logging.debug.assert_any_call("API Gemini respondeu com sucesso (response_len=26)")

def test_generate_content_model_not_available(mock_logging):
    """Test content generation when the model is not initialized."""
    if 'GEMINI_API_KEY' in os.environ:
        del os.environ['GEMINI_API_KEY']
        
    service = AIService()
    response = service.generate_content("some prompt")

    # Assertions
    assert response is None
    mock_logging.warning.assert_any_call("Modelo Gemini não disponível.")

@pytest.mark.parametrize("invalid_prompt", [None, "", "   ", 123])
def test_generate_content_invalid_prompt(invalid_prompt, mock_logging):
    """Test content generation with an invalid or empty prompt."""
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'}):
        service = AIService()
        response = service.generate_content(invalid_prompt)

    # Assertions
    assert response is None
    mock_logging.warning.assert_called_once_with("Prompt inválido ou vazio.")

def test_generate_content_api_exception(mock_genai, mock_logging):
    """Test that an exception during API call is logged and raised."""
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'}):
        service = AIService()
        # Configure the mock to raise an exception
        service.model.generate_content.side_effect = Exception("API Timeout")

        with pytest.raises(Exception, match="API Timeout"):
            service.generate_content("a valid prompt")

    # Assertions
    mock_logging.error.assert_called_once_with("Erro ao chamar a API Gemini: API Timeout", exc_info=True)

@pytest.mark.parametrize("invalid_response", [None, MagicMock(spec=[])]) # No 'text' attribute
def test_generate_content_invalid_api_response(invalid_response, mock_genai, mock_logging):
    """Test handling of an invalid response object from the API."""
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-api-key'}):
        service = AIService()
        # Configure the mock to return an invalid response
        service.model.generate_content.return_value = invalid_response

        response = service.generate_content("a valid prompt")

    # Assertions
    assert response is None
    mock_logging.warning.assert_called_once_with("Resposta inválida da API Gemini.")