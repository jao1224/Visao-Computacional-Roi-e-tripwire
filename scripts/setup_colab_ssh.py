import os
import urllib.request

ssh_dir = os.path.expanduser('~/.ssh')
os.makedirs(ssh_dir, exist_ok=True)
cloudflared_path = os.path.join(ssh_dir, 'cloudflared.exe')

if not os.path.exists(cloudflared_path):
    print("Baixando cloudflared.exe para Windows...")
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    urllib.request.urlretrieve(url, cloudflared_path)
    print(f"[OK] cloudflared.exe instalado em: {cloudflared_path}")
else:
    print(f"[OK] cloudflared.exe já existe em: {cloudflared_path}")

config_path = os.path.join(ssh_dir, 'config')
cf_path_escaped = cloudflared_path.replace('\\', '/')
config_entry = f"""
Host *.trycloudflare.com
  HostName %h
  User root
  Port 22
  ProxyCommand "{cf_path_escaped}" access ssh --hostname %h
"""

existing_config = ""
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        existing_config = f.read()

if '*.trycloudflare.com' not in existing_config:
    with open(config_path, 'a', encoding='utf-8') as f:
        f.write(config_entry)
    print("[OK] SSH Config configurado com sucesso!")
else:
    print("[OK] SSH Config já configurado anteriormente!")

print("\n--> TUDO CONFIGURADO NO SEU WINDOWS!")
