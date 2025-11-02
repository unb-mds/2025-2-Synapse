import os
import logging
from mailersend import MailerSendClient, EmailBuilder

class MailService:
    def __init__(self):
        self.mailersend_api_key = os.getenv('MAILERSEND_API_KEY')
        self.sender_email = os.getenv('MAILERSEND_FROM_EMAIL')
        self.sender_name = os.getenv('MAILERSEND_FROM_NAME')

        if not self.mailersend_api_key:
            logging.error(
                "Erro de Configuração: A chave MAILERSEND_API_KEY não foi configurada no ambiente do container."
            )
        self.ms = MailerSendClient(api_key=self.mailersend_api_key)

    def sendemail(self, recipient_email: str, recipient_name: str,
                  subject: str, html_content: str) -> bool:
        if not self.mailersend_api_key:
            logging.error(
                f"Falha ao tentar enviar e-mail para {recipient_email}. "
                "Chave da API MailerSend ausente."
            )
            return False

        try:
            email = (
                EmailBuilder()
                .from_email(self.sender_email, self.sender_name)
                .to_many([
                    {"email": recipient_email, "name": recipient_name}
                ])
                .subject(subject)
                .html(html_content)
                .text("Versão em texto simples do seu email.")
                .build()
            )

            response = self.ms.emails.send(email)

            if response.status_code in (200, 202):
                logging.info(f"E-mail enviado com sucesso para: {recipient_email}")
                return True
            else:
                status = response.status_code
                try:
                    body = response.json()
                except Exception:
                    body = None
                logging.error(
                    f"Erro de API ao enviar e-mail para {recipient_email}. "
                    f"Status: {status}. Detalhes: {body}"
                )
                return False

        except Exception as e:
            logging.error(
                f"Erro de Conexão/API inesperado ao enviar e-mail para {recipient_email}: {e}",
                exc_info=True
            )
            return False
