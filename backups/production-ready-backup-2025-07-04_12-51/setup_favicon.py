#!/usr/bin/env python3
"""
Script pour configurer automatiquement le favicon
"""

from PIL import Image, ImageDraw
import os
import requests
import time
import subprocess

def create_favicon():
    """Crée un favicon ICO avec un vélo doré"""
    
    print("🎨 Création du favicon...")
    
    # Créer une image 32x32 pixels
    size = 32
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))  # Fond transparent
    draw = ImageDraw.Draw(img)
    
    # Couleurs
    gold = (255, 215, 0, 255)
    dark_gold = (255, 200, 0, 255)
    
    # Dessiner un vélo stylisé
    # Roue avant
    draw.ellipse([6, 18, 18, 30], outline=gold, fill=None, width=2)
    # Roue arrière
    draw.ellipse([18, 18, 30, 30], outline=gold, fill=None, width=2)
    
    # Cadre du vélo
    draw.line([(12, 24), (18, 16), (24, 24)], fill=gold, width=2)
    draw.line([(12, 24), (24, 24)], fill=gold, width=2)
    
    # Guidon
    draw.line([(10, 20), (8, 18), (10, 16)], fill=gold, width=2)
    
    # Selle
    draw.line([(20, 20), (22, 18), (24, 20)], fill=gold, width=2)
    
    # Rayons des roues
    draw.line([(12, 20), (12, 28)], fill=dark_gold, width=1)
    draw.line([(8, 24), (16, 24)], fill=dark_gold, width=1)
    draw.line([(24, 20), (24, 28)], fill=dark_gold, width=1)
    draw.line([(20, 24), (28, 24)], fill=dark_gold, width=1)
    
    # Sauvegarder en ICO
    favicon_path = 'static/favicon.ico'
    img.save(favicon_path, format='ICO', sizes=[(32, 32), (16, 16)])
    
    print(f"✅ Favicon créé : {favicon_path}")
    print(f"📏 Taille du fichier : {os.path.getsize(favicon_path)} bytes")
    
    return favicon_path

def test_favicon():
    """Teste l'accès au favicon"""
    
    print("\n🔍 Test du favicon...")
    
    try:
        # Démarrer l'application en arrière-plan
        print("🚀 Démarrage de l'application...")
        process = subprocess.Popen(["python", "run.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)  # Attendre que l'app démarre
        
        # Tester l'accès au favicon
        print("🔍 Test de l'accès au favicon...")
        response = requests.get("http://localhost:5000/favicon.ico", timeout=10)
        
        if response.status_code == 200:
            print("✅ Favicon accessible via la route spéciale !")
            print(f"📏 Taille : {len(response.content)} bytes")
            print("🎉 Configuration réussie !")
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
            
        # Arrêter l'app
        process.terminate()
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        print("💡 Assurez-vous que l'application est démarrée sur http://localhost:5000")

def main():
    """Fonction principale"""
    
    print("🚴‍♂️ Configuration automatique du favicon")
    print("=" * 50)
    
    # Créer le favicon
    favicon_path = create_favicon()
    
    # Vérifier que le fichier existe
    if os.path.exists(favicon_path):
        print(f"✅ Fichier favicon trouvé : {favicon_path}")
    else:
        print(f"❌ Erreur : Fichier {favicon_path} non trouvé")
        return
    
    # Test du favicon
    test_favicon()
    
    print("\n" + "=" * 50)
    print("🎯 Instructions finales :")
    print("1. Redémarrez votre application Flask")
    print("2. Ouvrez http://localhost:5000")
    print("3. Videz le cache du navigateur (Ctrl+F5)")
    print("4. Vous devriez voir l'icône de vélo dorée dans l'onglet !")
    print("=" * 50)

if __name__ == "__main__":
    main() 