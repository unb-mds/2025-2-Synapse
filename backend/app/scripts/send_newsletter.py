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
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #ccc; border-radius: 8px; overflow: hidden; background-color: #f7f7f7;">
                        <header style="background-color: #3B82F6; color: white; padding: 20px; text-align: center;">
                            <h2 style="margin: 0; font-size: 1.5em;">Synapse News - Teste de Envio</h2>
                        </header>
                        <main style="padding: 20px; color: #333;">
                            <p style="font-size: 1.1em;"><strong>Olá!</strong></p>
                            
                            <p>Este é um e-mail de teste de Newsletter.</p>
                        </main>
                        <footer style="background-color: #E5E7EB; color: #6B7280; text-align: center; padding: 10px; font-size: 0.8em;">
                            Este e-mail foi enviado automaticamente.
                        </footer>
                    </div>
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
