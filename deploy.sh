#!/bin/bash

# Script de déploiement automatique pour VPS Ionos
# Usage: ./deploy.sh IP_DU_SERVEUR

if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh IP_DU_SERVEUR"
    echo "Exemple: ./deploy.sh 123.456.789.012"
    exit 1
fi

SERVER_IP=$1
echo "🚀 Déploiement sur le serveur: $SERVER_IP"

# 1. Mise à jour du système
echo "📦 Mise à jour du système..."
ssh root@$SERVER_IP "apt update && apt upgrade -y"

# 2. Installation des dépendances
echo "🔧 Installation des dépendances..."
ssh root@$SERVER_IP "apt install -y python3 python3-pip python3-venv nginx git supervisor postgresql postgresql-contrib"

# 3. Configuration de PostgreSQL
echo "🗄️ Configuration de PostgreSQL..."
ssh root@$SERVER_IP "sudo -u postgres psql -c \"CREATE DATABASE notation_app;\""
ssh root@$SERVER_IP "sudo -u postgres psql -c \"CREATE USER notation_user WITH PASSWORD 'notation_password_2024';\""
ssh root@$SERVER_IP "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE notation_app TO notation_user;\""

# 4. Cloner le projet
echo "📥 Clonage du projet..."
ssh root@$SERVER_IP "cd /var/www && git clone https://github.com/Toinau/Projet-notation.git"

# 5. Configuration de l'environnement
echo "🐍 Configuration de l'environnement Python..."
ssh root@$SERVER_IP "cd /var/www/Projet-notation && python3 -m venv venv"
ssh root@$SERVER_IP "cd /var/www/Projet-notation && source venv/bin/activate && pip install -r requirements.txt"

# 6. Configuration des permissions
echo "🔐 Configuration des permissions..."
ssh root@$SERVER_IP "chown -R www-data:www-data /var/www/Projet-notation"
ssh root@$SERVER_IP "chmod -R 755 /var/www/Projet-notation"

echo "✅ Déploiement automatique terminé !"
echo "📝 Prochaines étapes manuelles :"
echo "1. Se connecter au serveur: ssh root@$SERVER_IP"
echo "2. Configurer le fichier .env"
echo "3. Initialiser la base de données"
echo "4. Configurer Nginx et Gunicorn" 