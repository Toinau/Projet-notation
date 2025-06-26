#!/usr/bin/env python3
"""
Script pour supprimer un utilisateur
Usage: python delete_user.py
"""

import sqlite3
import os

def list_users():
    """Afficher la liste des utilisateurs"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, email, role, is_active FROM user ORDER BY id")
    users = cursor.fetchall()
    
    if not users:
        print("Aucun utilisateur trouvé.")
        conn.close()
        return []
    
    print("\n=== Liste des utilisateurs ===")
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Rôle':<10} {'Actif':<6}")
    print("-" * 75)
    
    for user in users:
        user_id, username, email, role, is_active = user
        active_status = "Oui" if is_active else "Non"
        print(f"{user_id:<5} {username:<20} {email:<30} {role:<10} {active_status:<6}")
    
    conn.close()
    return users

def delete_user_by_id(user_id):
    """Supprimer un utilisateur par son ID"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Vérifier que l'utilisateur existe
    cursor.execute("SELECT username, email, role FROM user WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        print(f"Aucun utilisateur trouvé avec l'ID {user_id}")
        conn.close()
        return False
    
    username, email, role = user
    
    # Confirmation
    print(f"\nUtilisateur à supprimer :")
    print(f"  ID: {user_id}")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Rôle: {role}")
    
    confirm = input("\nÊtes-vous sûr de vouloir supprimer cet utilisateur ? (oui/non): ").strip().lower()
    
    if confirm not in ['oui', 'o', 'yes', 'y']:
        print("Suppression annulée.")
        conn.close()
        return False
    
    try:
        # Supprimer l'utilisateur
        cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Utilisateur '{username}' supprimé avec succès!")
            return True
        else:
            print("❌ Erreur lors de la suppression")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def delete_user_by_username(username):
    """Supprimer un utilisateur par son nom d'utilisateur"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Vérifier que l'utilisateur existe
    cursor.execute("SELECT id, email, role FROM user WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"Aucun utilisateur trouvé avec le nom '{username}'")
        conn.close()
        return False
    
    user_id, email, role = user
    
    # Confirmation
    print(f"\nUtilisateur à supprimer :")
    print(f"  ID: {user_id}")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Rôle: {role}")
    
    confirm = input("\nÊtes-vous sûr de vouloir supprimer cet utilisateur ? (oui/non): ").strip().lower()
    
    if confirm not in ['oui', 'o', 'yes', 'y']:
        print("Suppression annulée.")
        conn.close()
        return False
    
    try:
        # Supprimer l'utilisateur
        cursor.execute("DELETE FROM user WHERE username = ?", (username,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Utilisateur '{username}' supprimé avec succès!")
            return True
        else:
            print("❌ Erreur lors de la suppression")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def main():
    """Fonction principale"""
    print("=== Suppression d'utilisateur ===")
    
    # Vérifier que la base de données existe
    if not os.path.exists('app.db'):
        print("❌ Fichier de base de données 'app.db' introuvable.")
        return
    
    # Afficher les utilisateurs
    users = list_users()
    if not users:
        return
    
    print("\nComment voulez-vous identifier l'utilisateur à supprimer ?")
    print("1. Par ID")
    print("2. Par nom d'utilisateur")
    print("3. Annuler")
    
    choice = input("\nVotre choix (1-3): ").strip()
    
    if choice == '1':
        try:
            user_id = int(input("ID de l'utilisateur à supprimer: ").strip())
            delete_user_by_id(user_id)
        except ValueError:
            print("❌ L'ID doit être un nombre")
    
    elif choice == '2':
        username = input("Nom d'utilisateur à supprimer: ").strip()
        if username:
            delete_user_by_username(username)
        else:
            print("❌ Le nom d'utilisateur ne peut pas être vide")
    
    elif choice == '3':
        print("Opération annulée.")
    
    else:
        print("❌ Choix invalide")

if __name__ == '__main__':
    main()