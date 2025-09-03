import sys
import os

TOKEN_KEY = 'WHATSAPP_ACCESS_TOKEN'

def update_env_token(token, env_path='.env'):
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(TOKEN_KEY + '='):
                    lines.append(f'{TOKEN_KEY}={token}\n')
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f'{TOKEN_KEY}={token}\n')
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ Token WhatsApp mis à jour dans {env_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python update_whatsapp_token.py <NOUVEAU_TOKEN>")
        sys.exit(1)
    token = sys.argv[1]
    update_env_token(token) 