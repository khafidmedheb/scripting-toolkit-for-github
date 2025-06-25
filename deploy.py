import os
import subprocess
import requests

# === CONFIGURATION ===
GITHUB_USERNAME = "votre-user"  # Remplace par ton nom d'utilisateur GitHub
REPO_NAME = "mon-nouveau-repo"
DESCRIPTION = "Repo créé automatiquement 🚀"
PRIVATE = True  # True ou False
USE_SSH = False  # True pour utiliser SSH

# === AUTHENTIFICATION ===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise Exception("⚠️  GITHUB_TOKEN non défini dans l'environnement.")

# === CRÉATION DU REPO DISTANT ===
print("📡 Création du dépôt GitHub distant...")
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}
data = {
    "name": REPO_NAME,
    "description": DESCRIPTION,
    "private": PRIVATE
}
response = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
if response.status_code != 201:
    raise Exception(f"Erreur GitHub: {response.status_code} - {response.text}")

# === URL DU REPO ===
if USE_SSH:
    remote_url = f"git@github.com:{GITHUB_USERNAME}/{REPO_NAME}.git"
else:
    remote_url = f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"

# === COMMANDES GIT ===
print("📁 Initialisation du repo local...")
subprocess.run(["git", "init"], check=True)
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
subprocess.run(["git", "branch", "-M", "main"], check=True)
subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

print(f"✅ Déploiement terminé : {remote_url}")
