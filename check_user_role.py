#!/usr/bin/env python3
"""
Script pour vérifier le rôle des utilisateurs
Usage: python check_user_role.py
"""

import sqlite3
import os

def check_users():
    """Vérifier les rôles des utilisateurs"""
    
    if not os.path.exists('app.db'):
        print("❌ Fichier de base de données 'app.db' introuvable.")
        return
    
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, email, role, is_active FROM user ORDER BY id")
    users = cursor.fetchall()
    
    if not users:
        print("Aucun utilisateur trouvé.")
        conn.close()
        return
    
    print("\n=== Vérification des rôles utilisateurs ===")
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Rôle':<10} {'Actif':<6}")
    print("-" * 75)
    
    admin_count = 0
    coureur_count = 0
    
    for user in users:
        user_id, username, email, role, is_active = user
        active_status = "Oui" if is_active else "Non"
        print(f"{user_id:<5} {username:<20} {email:<30} {role:<10} {active_status:<6}")
        
        if role == 'admin':
            admin_count += 1
        elif role == 'coureur':
            coureur_count += 1
    
    print("-" * 75)
    print(f"Total: {len(users)} utilisateurs")
    print(f"Administrateurs: {admin_count}")
    print(f"Coureurs: {coureur_count}")
    
    # Vérifier s'il y a des problèmes
    problems = []
    for user in users:
        user_id, username, email, role, is_active = user
        if role not in ['admin', 'coureur']:
            problems.append(f"❌ {username} a un rôle invalide: '{role}'")
        if not is_active and role == 'admin':
            problems.append(f"⚠️  Admin {username} est désactivé")
    
    if problems:
        print("\n=== Problèmes détectés ===")
        for problem in problems:
            print(problem)
    else:
        print("\n✅ Tous les utilisateurs ont des rôles valides")
    
    conn.close()

def fix_user_role():
    """Corriger le rôle d'un utilisateur"""
    print("\n=== Correction du rôle d'un utilisateur ===")
    
    username = input("Nom d'utilisateur à modifier: ").strip()
    if not username:
        print("❌ Le nom d'utilisateur ne peut pas être vide")
        return
    
    print("Rôles disponibles:")
    print("1. admin")
    print("2. coureur")
    
    role_choice = input("Choisissez le nouveau rôle (1-2): ").strip()
    
    if role_choice == '1':
        new_role = 'admin'
    elif role_choice == '2':
        new_role = 'coureur'
    else:
        print("❌ Choix invalide")
        return
    
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Vérifier que l'utilisateur existe
    cursor.execute("SELECT id, role FROM user WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ Utilisateur '{username}' introuvable")
        conn.close()
        return
    
    user_id, current_role = user
    
    if current_role == new_role:
        print(f"ℹ️  L'utilisateur '{username}' a déjà le rôle '{new_role}'")
        conn.close()
        return
    
    try:
        cursor.execute("UPDATE user SET role = ? WHERE username = ?", (new_role, username))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Rôle de '{username}' modifié de '{current_role}' vers '{new_role}'")
        else:
            print(f"❌ Erreur lors de la modification")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    """Fonction principale"""
    print("=== Gestion des rôles utilisateurs ===")
    
    # Vérifier les utilisateurs
    check_users()
    
    print("\nQue voulez-vous faire ?")
    print("1. Corriger le rôle d'un utilisateur")
    print("2. Quitter")
    
    choice = input("\nVotre choix (1-2): ").strip()
    
    if choice == '1':
        fix_user_role()
    elif choice == '2':
        print("Au revoir!")
    else:
        print("❌ Choix invalide")

if __name__ == '__main__':
    main()