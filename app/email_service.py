import os
from flask import current_app, render_template
from flask_mail import Message
from app import mail

def send_questionnaire_notification_email(user, questionnaire):
    """
    Envoie une notification par email à un utilisateur quand un questionnaire est disponible
    
    Args:
        user: L'objet User qui doit recevoir l'email
        questionnaire: L'objet Questionnaire créé
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not user.email:
        return False, "Utilisateur sans adresse email"
    
    if not user.notifications_email:
        return False, "Notifications email désactivées pour cet utilisateur"
    
    try:
        # Création du message
        subject = f"🚴‍♂️ Nouveau questionnaire disponible - {questionnaire.course_name}"
        
        # Récupération de l'URL de l'application
        app_url = current_app.config.get('APP_URL', 'http://localhost:5000')
        questionnaire_url = f"{app_url}/coureur/questionnaires"
        
        # Création du contenu HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Nouveau questionnaire disponible</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #ffd700, #ffed4e);
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    background: #ffd700;
                    color: #333;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 20px;
                }}
                .highlight {{
                    background: #fff3cd;
                    padding: 10px;
                    border-left: 4px solid #ffd700;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚴‍♂️ Nouveau questionnaire disponible !</h1>
            </div>
            
            <div class="content">
                <h2>Bonjour {user.prenom} {user.nom},</h2>
                
                <p>Un nouveau questionnaire de notation est disponible pour la course :</p>
                
                <div class="highlight">
                    <h3>📋 {questionnaire.course_name}</h3>
                    <p><strong>Date de course :</strong> {questionnaire.course_date.strftime('%d/%m/%Y')}</p>
                    <p><strong>Points Evénements :</strong> {questionnaire.direct_velo_points} points</p>
                </div>
                
                <p>Connectez-vous à votre espace coureur pour évaluer vos coéquipiers et contribuer à la notation de l'équipe.</p>
                
                <div style="text-align: center;">
                    <a href="{questionnaire_url}" class="button">
                        🚴‍♂️ Accéder au questionnaire
                    </a>
                </div>
                
                <p><em>Merci de votre participation !</em></p>
            </div>
            
            <div class="footer">
                <p>Cet email a été envoyé automatiquement.</p>
                <p>Si vous ne souhaitez plus recevoir ces notifications, contactez votre administrateur.</p>
            </div>
        </body>
        </html>
        """
        
        # Création du contenu texte simple
        text_content = f"""
        Nouveau questionnaire disponible !
        
        Bonjour {user.prenom} {user.nom},
        
        Un nouveau questionnaire de notation est disponible pour la course : {questionnaire.course_name}
        
        Date de course : {questionnaire.course_date.strftime('%d/%m/%Y')}
        Points Evénements : {questionnaire.direct_velo_points} points
        
        Connectez-vous à votre espace coureur pour évaluer vos coéquipiers.
        
        Merci de votre participation !
        """
        
        # Récupération de l'expéditeur depuis la configuration
        sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
        if not sender:
            return False, "Configuration email manquante : MAIL_DEFAULT_SENDER ou MAIL_USERNAME requis"
        
        # Création du message
        msg = Message(
            subject=subject,
            sender=sender,
            recipients=[user.email],
            body=text_content,
            html=html_content
        )
        
        # Envoi de l'email
        mail.send(msg)
        
        current_app.logger.info(f"Email de notification envoyé à {user.email} pour le questionnaire {questionnaire.course_name}")
        return True, "Email envoyé avec succès"
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'envoi de l'email à {user.email}: {str(e)}")
        return False, f"Erreur lors de l'envoi de l'email: {str(e)}"

def send_bulk_questionnaire_notifications(users, questionnaire):
    """
    Envoie des notifications par email à plusieurs utilisateurs
    
    Args:
        users: Liste d'objets User
        questionnaire: L'objet Questionnaire créé
    
    Returns:
        tuple: (emails_sent: int, emails_errors: int, error_messages: list)
    """
    emails_sent = 0
    emails_errors = 0
    error_messages = []
    
    for user in users:
        if user.email:
            success, message = send_questionnaire_notification_email(user, questionnaire)
            if success:
                emails_sent += 1
            else:
                emails_errors += 1
                error_messages.append(f"Erreur pour {user.prenom} {user.nom}: {message}")
        else:
            emails_errors += 1
            error_messages.append(f"Pas d'email pour {user.prenom} {user.nom}")
    
    return emails_sent, emails_errors, error_messages 