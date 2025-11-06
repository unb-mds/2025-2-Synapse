import logging
import json
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app import create_app 
from app.repositories.user_repository import UserRepository
from app.services.mail_service import MailService
from app.services.ai_service import AIService
from app.services.news_service import NewsService

def build_newsletter_email(user_name, intro_text, news_items):
    header = f"""
    <div style="text-align:center;margin-bottom:40px;">
    <span style="display:block;font-weight:700;font-size:44px;letter-spacing:-2px;line-height:0.8;margin-bottom:5px;">Synapse</span>
    <span style="display:block;font-size:22px;letter-spacing:1px;color:#666;">Newsletter</span>
    </div>
    <div style="border:2px solid #222; border-radius:7px; background:#f7f7f7; padding:18px 24px; margin-bottom:36px;">
    <p style="margin:0 0 12px 0;">Olá {user_name},</p>
    <p style="margin:0 0 12px 0;">Bem-vindo à Synapse newsletter.</p>
    <p style="margin:0;">{intro_text}</p>
    </div>
    """

    sections = []
    for item in news_items:
        block = f"""
        <section style="margin-bottom:38px;">
        <div style="margin-bottom:8px;">
            <span style="font-size:12px;letter-spacing:1px;color:#222;text-transform:uppercase;font-weight:500; border-bottom:1px solid #999;padding-bottom:2px;">{item['category']}</span>
        </div>
        <h2 style="margin:0 0 8px 0;font-size:20px;line-height:1.2;font-weight:700;">{item['title']}</h2>
        <img src="{item['img_url']}" alt="{item['title']}" style="width:100%;max-width:445px;border-radius:6px;margin-bottom:15px;display:block;" />
        <p style="color:#444;margin:0 0 10px 0;font-size:15px;line-height:1.5;">{item['summary']}</p>
        <div style="font-size:12px;color:#888;margin-top:8px;border-top:1px solid #eee;padding-top:7px;">
            {item['source']} | {item['date']}
        </div>
        </section>
        """
        sections.append(block)
    
    html = f"""<!DOCTYPE html>
    <html lang="pt" style="background-color:#fafafa;">
    <head>
        <meta charset="UTF-8">
        <title>Synapse Newsletter</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    </head>
    <body style="margin:0;padding:0;font-family: Arial, sans-serif; background-color:#fafafa; color: #181818;">
        <div style="max-width: 518px;margin:40px auto;background:#fff;box-shadow:0 2px 8px rgba(60,60,67,0.07);border-radius:10px;padding:40px 20px;">
        {header}
        <div>{" ".join(sections)}</div>
        </div>
    </body>
    </html>
    """
    return html


def gerar_texto_intro(ai_service: AIService, user, news_data) -> str:
    """
    Gera um texto introdutório usando a IA (Gemini).
    """

    if isinstance(news_data, str):
        try:
            news_data = json.loads(news_data)
        except json.JSONDecodeError:
            logging.warning("news_data era string simples, convertendo para lista vazia.")
            news_data = []
    elif isinstance(news_data, list) and all(isinstance(n, str) for n in news_data):
        try:
            news_data = [json.loads(n) for n in news_data]
        except Exception:
            logging.warning("Erro ao converter elementos de news_data (strings JSON) para dicionários.")
            news_data = []

    noticias_resumo = "\n".join(
        [f"- {n.get('title')}: {n.get('summary', '')}" for n in news_data if isinstance(n, dict)]
    )

    #Deve ser alterado para que cada usuario cadastre um prompt personalizado
    prompt = f"""
        Você é um assistente que cria introduções de newsletter.
        Crie um parágrafo introdutório amigável e envolvente para o usuário {user.full_name}.
        As notícias selecionadas para ele são:

        {noticias_resumo}

        O texto deve ser curto (3 a 5 frases), convidativo e fazer uma transição natural para a lista de notícias.
        Escreva em português do Brasil.
        """

    resposta = ai_service.generate_content(prompt)
    if not resposta:
        return f"Olá {user.full_name}, aqui está sua seleção personalizada de notícias da semana."

    return resposta.strip()


def send_newsletter_job():
    app = create_app()

    import os
    logging.info(f"MAILTRAP_USER: {os.getenv('MAILTRAP_USER')}")
    logging.info(f"MAILTRAP_PASSWORD set? {'Sim' if os.getenv('MAILTRAP_PASSWORD') else 'Não'}")


    with app.app_context():
        logging.info("=" * 80)
        logging.info("JOB DE ENVIO DE NEWSLETTER INICIADO")
        logging.info("=" * 80)

        try:
            user_repo = UserRepository()
            mail_service = MailService()
            news_service = NewsService()
            ai_service = AIService()

            logging.info("Buscando usuários...")
            users = user_repo.get_users_to_newsletter()

            if not users:
                logging.info("Nenhum usuário manifestou interesse na newsletter. Finalizando.")
                return

            logging.info(f"Encontrados {len(users)} usuários para envio.")
            success_count = 0
            fail_count = 0

            for user in users:
                logging.info(f"--- Processando: {user.full_name} <{user.email}> ---")
                try:
                    news_data = news_service.get_news_to_email(user.id, page=1, per_page=5)

                    if not news_data:
                        logging.warning(f"Nenhuma notícia encontrada para {user.email}. Pulando...")
                        continue

                    intro = gerar_texto_intro(ai_service, user, news_data)

                    newsletter_html = build_newsletter_email(
                        user_name=user.full_name,
                        intro_text=intro,
                        news_items=news_data
                    )
                    assunto = "Seu Resumo Personalizado de Notícias Synapse"

                    sucesso = mail_service.sendemail(
                        recipient_email=user.email,
                        recipient_name=user.full_name,
                        subject=assunto,
                        html_content=newsletter_html
                    )

                    if sucesso:
                        success_count += 1
                    else:
                        fail_count += 1

                except Exception as e:
                    logging.error(f"ERRO no envio para {user.email}. Detalhes: {e}", exc_info=True)
                    fail_count += 1

            logging.info("=" * 80)
            logging.info("JOB DE ENVIO DE NEWSLETTER FINALIZADO")
            logging.info(f"RESULTADO: {success_count} enviados com sucesso, {fail_count} falhas.")
            logging.info("=" * 80)

        except Exception as e:
            logging.critical(f"ERRO FATAL: O job terminou abruptamente: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    send_newsletter_job()
