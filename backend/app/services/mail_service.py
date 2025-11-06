import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MailService:
    def __init__(self):
        # self.sender_email = os.getenv('GMAIL_SENDER_EMAIL')
        # self.sender_password = os.getenv('GMAIL_APP_PASSWORD')

        # if not self.sender_email or not self.sender_password:
        #     logging.error(
        #         "Erro de Configuração: As variáveis GMAIL_SENDER_EMAIL e GMAIL_APP_PASSWORD não foram configuradas."
        #     )
    
        self.smtp_host = 'smtp.mailtrap.io'
        self.smtp_port = 2525
        self.smtp_user = os.getenv('MAILTRAP_USER')
        self.smtp_password = os.getenv('MAILTRAP_PASSWORD')

        print(self.smtp_user, self.smtp_password)

        if not self.smtp_user or not self.smtp_password:
            logging.error("Variáveis MAILTRAP_USER ou MAILTRAP_PASSWORD não configuradas.")
            raise EnvironmentError("Credenciais Mailtrap não configuradas no ambiente.")

    def sendemail(self, recipient_email: str, recipient_name: str,
              subject: str, html_content: str) -> bool:
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.smtp_user
            message['To'] = recipient_email

            part = MIMEText(html_content, 'html')
            message.attach(part)

            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, recipient_email, message.as_string())
            server.quit()

            logging.info(f"E-mail enviado com sucesso para: {recipient_email}")
            return True

        except Exception as e:
            logging.error(
                f"Erro ao enviar e-mail para {recipient_email}: {e}",
                exc_info=True
            )
            return False
