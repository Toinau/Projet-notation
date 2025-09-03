import os
import requests
from flask import current_app

class FreeMobileSMSService:
    def __init__(self):
        self.user = current_app.config.get('FREE_MOBILE_USER')
        self.api_key = current_app.config.get('FREE_MOBILE_API_KEY')
        self.api_url = 'https://smsapi.free-mobile.fr/sendmsg'

    def send_sms(self, message):
        if not self.user or not self.api_key:
            current_app.logger.warning("Identifiants Free Mobile manquants.")
            return False, "Identifiants Free Mobile manquants."
        params = {
            'user': self.user,
            'pass': self.api_key,
            'msg': message
        }
        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            if response.status_code == 200:
                return True, "SMS envoyé avec succès."
            else:
                return False, f"Erreur Free Mobile: {response.status_code} - {response.text}"
        except Exception as e:
            return False, str(e)

    def send_questionnaire_notification(self, user, questionnaire):
        if not user.telephone or not user.notifications_sms:
            return False, "Utilisateur sans téléphone ou notifications SMS désactivées"
        message = f"🏃‍♂️ Nouveau questionnaire ! {questionnaire.course_name} le {questionnaire.course_date.strftime('%d/%m/%Y')}. Connectez-vous pour évaluer vos coéquipiers !"
        return self.send_sms(message)

free_mobile_sms_service = FreeMobileSMSService() 