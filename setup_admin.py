#!/usr/bin/env python3
"""
Script simple pour créer un administrateur et initialiser la DB
Usage: python setup_admin.py
"""

from werkzeug.security import generate_password_hash
import sqlite3
import os

def init_database():
    """Initialise la base de données SQLite"""
    
    # Créer le fichier de base de données s'il n'existe pas
    db_path = 'app.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Créer la table users si elle n'existe pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'coureur',
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de données initialisée")

def create_admin():
    """Créer un compte administrateur"""
    
    print("\n=== Création d'un compte administrateur ===")
    
    username = input("Nom d'utilisateur admin: ").strip()
    if not username:
        print("Erreur: Le nom d'utilisateur ne peut pas être vide")
        return
        
    email = input("Email admin: ").strip()
    if not email:
        print("Erreur: L'email ne peut pas être vide")
        return
        
    password = input("Mot de passe admin: ").strip()
    if not password:
        print("Erreur: Le mot de passe ne peut pas être vide")
        return
    
    # Connexion à la base de données
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Vérifier si l'utilisateur existe déjà
    cursor.execute("SELECT * FROM user WHERE username = ? OR email = ?", (username, email))
    existing_user = cursor.fetchone()
    
    if existing_user:
        print(f"Erreur: Un utilisateur avec ce nom ou cet email existe déjà")
        conn.close()
        return
    
    try:
        # Hasher le mot de passe
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Insérer le nouvel admin
        cursor.execute('''
            INSERT INTO user (username, email, password, role, is_active)
            VALUES (?, ?, ?, 'admin', 1)
        ''', (username, email, hashed_password))
        
        conn.commit()
        print(f"✅ Administrateur '{username}' créé avec succès!")
        print(f"   Email: {email}")
        print(f"   Rôle: admin")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    """Fonction principale"""
    print("=== Configuration de l'application ===")
    
    # Initialiser la base de données
    init_database()
    
    # Créer l'administrateur
    create_admin()
    
    print("\n✅ Configuration terminée!")
    print("Vous pouvez maintenant lancer votre application avec: python app.py")

if __name__ == '__main__':
    main()