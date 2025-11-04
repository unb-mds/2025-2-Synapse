import logging
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

def send_newsletter_job():
    app = create_app()

    conteudo_email =  f"""
                        <!DOCTYPE html>
                            <html lang="en" style="background-color:#fafafa;">
                            <head>
                            <meta charset="UTF-8">
                            <title>Synapse Newsletter</title>
                            <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                            </head>
                            <body style="margin:0;padding:0;font-family: Arial, sans-serif; background-color:#fafafa; color: #181818;">
                            <div style="max-width: 518px;margin:40px auto;background:#fff;box-shadow:0 2px 8px rgba(60,60,67,0.07);border-radius:10px;padding:40px 20px;">
                                <!-- Header -->
                                <div style="text-align:center;margin-bottom:40px;">
                                <span style="display:block;font-weight:700;font-size:44px;letter-spacing:-2px;line-height:0.8;margin-bottom:5px;">Synapse</span>
                                <span style="display:block;font-size:22px;letter-spacing:1px;color:#666;">Newsletter</span>
                                </div>
                                <!-- Intro box -->
                                <div style="border:2px solid #222; border-radius:7px; background:#f7f7f7; padding:18px 24px; margin-bottom:36px;">
                                <p style="margin:0 0 12px 0;">Hi [name],</p>
                                <p style="margin:0 0 12px 0;">Welcome to the Synapse newsletter.</p>
                                <p style="margin:0;">[Introdução]</p>
                                </div>

                                <!-- News Section (repeat block below for each news) -->
                                <div>
                                <!-- Example for 1st news, copy this <section> and paste for each news -->
                                <section style="margin-bottom:38px;">
                                    <div style="margin-bottom:8px;">
                                    <span style="font-size:12px;letter-spacing:1px;color:#222;text-transform:uppercase;font-weight:500; border-bottom:1px solid #999;padding-bottom:2px;">TECHNOLOGY</span>
                                    </div>
                                    <h2 style="margin:0 0 8px 0;font-size:20px;line-height:1.2;font-weight:700;">What's the big deal about AI data centres?</h2>
                                    <img src="https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=518&q=80" alt="AI Data Centre" style="width:100%;max-width:445px;border-radius:6px;margin-bottom:15px;display:block;" />
                                    <p style="color:#444;margin:0 0 10px 0;font-size:15px;line-height:1.5;">
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                                    </p>
                                    <p style="color:#444;margin:0 0 10px 0;font-size:15px;line-height:1.5;">
                                    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Lorem dolor sit amet, consectetur adipiscing elit.
                                    </p>
                                    <div style="font-size:12px;color:#888;margin-top:8px;border-top:1px solid #eee;padding-top:7px;">
                                    BBC News | 22 September 2025
                                    </div>
                                </section>
                                <!-- FIM 1º BLOCO NOTÍCIA -->
                                <!-- Cole mais 4 blocos como o acima -->
                                </div>
                                <!-- Fim das notícias -->
                            </div>
                        </body>
                    </html>
                 """
    
    with app.app_context():
        logging.info("=" * 80)
        logging.info("JOB DE ENVIO DE NEWSLETTER INICIADO")
        logging.info("=" * 80)

        try:
            user_repo    = UserRepository()
            mail_service = MailService()
            ai_service   = AIService()

            logging.info("Buscando usuários com interesse em receber newsletter...")
            
            users = user_repo.list_all() # Por enquanto busca todos os usuários
            
            if not users:
                logging.info("Nenhum usuário manifestou interesse na newsletter. Finalizando.")
                return

            logging.info(f"Encontrados {len(users)} usuários para envio.")
            
            success_count = 0
            fail_count = 0 
            
            for user in users:
                logging.info(f"--- Processando: {user.full_name} <{user.email}> ---")
                
                # try:
                #     noticias_personalizadas = ai_service.get_for_you_news(user.id)
                # except Exception as e:
                #     logging.error(f"ERRO: Falha ao obter notícias para {user.email}. Pulando. Detalhes: {e}")
                #     fail_count += 1
                #     continue
                
                assunto = "Seu Resumo Personalizado de Notícias Synapse"
                
                # try:
                #     prompt = f"Gere um resumo atrativo em português das notícias a seguir para o usuário {user.nome}, formatando o conteúdo para um e-mail HTML: {noticias_personalizadas}"
                #     # conteudo_email = ai_service.generate_content(prompt)

                # except Exception as e:
                #     logging.error(f"ERRO: Falha na geração de conteúdo de IA para {user.email}. Pulando. Detalhes: {e}")
                #     fail_count += 1
                #     continue
                
                if conteudo_email:
                    try:
                        sucesso = mail_service.sendemail(
                            recipient_email=user.email,
                            recipient_name=user.full_name,
                            subject=assunto,
                            html_content=f"<html><body>{conteudo_email}</body></html>" 
                        )
                        
                        if sucesso:
                            success_count += 1
                        else:
                            fail_count += 1
                            
                    except Exception as e:
                        logging.error(f"ERRO CRÍTICO: Falha no envio do e-mail para {user.email}. Detalhes: {e}", exc_info=True)
                        fail_count += 1
                else:
                    logging.warning(f"AVISO: Conteúdo da IA vazio para {user.email}. Pulando envio.")
                    fail_count += 1


            logging.info("=" * 80)
            logging.info("JOB DE ENVIO DE NEWSLETTER FINALIZADO")
            logging.info(f"RESULTADO: {success_count} e-mails enviados com sucesso. {fail_count} falhas.")
            logging.info("=" * 80)

        except Exception as e:
            logging.critical(f"ERRO FATAL: O job terminou abruptamente devido a uma exceção crítica: {e}", exc_info=True)
            raise 

if __name__ == "__main__":
    send_newsletter_job()
