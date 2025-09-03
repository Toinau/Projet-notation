import requests
import json
from flask import current_app
import re

class WhatsAppService:
    def __init__(self):
        self.phone_number_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = current_app.config.get('WHATSAPP_ACCESS_TOKEN')
        self.phone_number = current_app.config.get('WHATSAPP_PHONE_NUMBER')
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
    
    def send_whatsapp_message(self, to_number, message):
        """Envoie un message WhatsApp via l'API Business"""
        if not self.phone_number_id or not self.access_token:
            current_app.logger.warning("Configuration WhatsApp manquante")
            return False, "Configuration WhatsApp manquante"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Préparer le message
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                current_app.logger.info(f"WhatsApp message sent successfully: {response.json()}")
                return True, "Message WhatsApp envoyé avec succès"
            else:
                current_app.logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return False, f"Erreur WhatsApp API: {response.status_code} - {response.text}"
                
        except Exception as e:
            current_app.logger.error(f"Erreur envoi WhatsApp: {e}")
            return False, str(e)
    
    def _clean_phone_number(self, phone_number):
        """Nettoie et formate le numéro de téléphone pour WhatsApp"""
        if not phone_number:
            return None
        
        # Supprimer les espaces, tirets, points et parenthèses
        cleaned = re.sub(r'[\s\-\.\(\)]', '', phone_number)
        
        # Supprimer tous les caractères non numériques sauf le +
        cleaned = re.sub(r'[^\d\+]', '', cleaned)
        
        # Gestion des formats français
        if cleaned.startswith('0'):
            # Format 06 12 34 56 78 -> +33612345678
            cleaned = '+33' + cleaned[1:]
        elif cleaned.startswith('33') and not cleaned.startswith('+33'):
            # Format 33 6 12 34 56 78 -> +33612345678
            cleaned = '+' + cleaned
        elif not cleaned.startswith('+33'):
            # Si pas d'indicatif, ajouter +33
            cleaned = '+33' + cleaned
        
        # Vérifier que le numéro fait 12 caractères (+33 + 9 chiffres)
        if len(cleaned) != 12 or not cleaned.startswith('+33'):
            current_app.logger.warning(f"Format de numéro invalide après nettoyage: {cleaned}")
            return None
            
        current_app.logger.info(f"Numéro formaté: {phone_number} -> {cleaned}")
        return cleaned
    
    def send_questionnaire_notification(self, user, questionnaire):
        """Envoie une notification WhatsApp pour un nouveau questionnaire"""
        if not user.telephone or not user.notifications_sms:
            return False, "Utilisateur sans téléphone ou notifications désactivées"
        
        # Nettoyer le numéro de téléphone
        clean_number = self._clean_phone_number(user.telephone)
        if not clean_number:
            return False, "Numéro de téléphone invalide"
        
        message = f"""🏃‍♂️ *Nouveau questionnaire disponible !*

*Course :* {questionnaire.course_name}
*Date :* {questionnaire.course_date.strftime('%d/%m/%Y')}
*Points Direct Vélo :* {questionnaire.direct_velo_points}

Connectez-vous pour évaluer vos coéquipiers !

_Moyon Percy Vélo Club_"""
        
        return self.send_whatsapp_message(clean_number, message)
    
    def send_reminder_notification(self, user, questionnaire):
        """Envoie un rappel WhatsApp pour un questionnaire non complété"""
        if not user.telephone or not user.notifications_sms:
            return False, "Utilisateur sans téléphone ou notifications désactivées"
        
        clean_number = self._clean_phone_number(user.telephone)
        if not clean_number:
            return False, "Numéro de téléphone invalide"
        
        message = f"""📱 *Rappel questionnaire*

*Course :* {questionnaire.course_name}
*Date :* {questionnaire.course_date.strftime('%d/%m/%Y')}

N'oubliez pas de compléter votre évaluation !

_Moyon Percy Vélo Club_"""
        
        return self.send_whatsapp_message(clean_number, message)
    
    def send_questionnaire_template(self, to_number, nom_coureur, nom_course, date_course, points_direct_velo=None):
        """Envoie le template questionnaire_notification avec les variables fournies. Ajoute points_direct_velo si le template WhatsApp l'accepte."""
        if not self.phone_number_id or not self.access_token:
            current_app.logger.warning("Configuration WhatsApp manquante")
            return False, "Configuration WhatsApp manquante"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        parameters = [
            {"type": "text", "text": nom_coureur},
            {"type": "text", "text": nom_course},
            {"type": "text", "text": date_course}
        ]
        if points_direct_velo is not None:
            parameters.append({"type": "text", "text": str(points_direct_velo)})

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": "questionnaire_notification",
                "language": {"code": "fr"},
                "components": [
                    {
                        "type": "body",
                        "parameters": parameters
                    }
                ]
            }
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            if response.status_code == 200:
                current_app.logger.info(f"WhatsApp template envoyé: {response.json()}")
                return True, "Template WhatsApp envoyé avec succès"
            else:
                current_app.logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return False, f"Erreur WhatsApp API: {response.status_code} - {response.text}"
        except Exception as e:
            current_app.logger.error(f"Erreur envoi WhatsApp template: {e}")
            return False, str(e)
    
    def send_hello_world_template(self, to_number):
        """Envoie le template officiel hello_world (aucune variable)"""
        if not self.phone_number_id or not self.access_token:
            current_app.logger.warning("Configuration WhatsApp manquante")
            return False, "Configuration WhatsApp manquante"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {"code": "en_US"}
            }
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            if response.status_code == 200:
                current_app.logger.info(f"WhatsApp template hello_world envoyé: {response.json()}")
                return True, "Template hello_world envoyé avec succès"
            else:
                current_app.logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return False, f"Erreur WhatsApp API: {response.status_code} - {response.text}"
        except Exception as e:
            current_app.logger.error(f"Erreur envoi WhatsApp template hello_world: {e}")
            return False, str(e) 