#!/bin/bash

# === CONFIGURATION ===
# Remplace ces valeurs par les tiens
GITHUB_USERNAME="votre-user"               # Ex: khaliddev
REPO_NAME="mon-nouveau-repo"              # Ex: test-cypress-agent
DESCRIPTION="Repo créé automatiquement 🚀"
PRIVATE=true                              # true ou false
USE_SSH=false                             # true si tu veux utiliser SSH

# === SCRIPT ===
# 1. Crée un repo distant via l’API GitHub
echo "📡 Création du dépôt GitHub distant..."
if [ "$PRIVATE" = true ]; then
  VISIBILITY="true"
else
  VISIBILITY="false"
fi

AUTH_HEADER="Authorization: token $GITHUB_TOKEN"
RESPONSE=$(curl -s -H "$AUTH_HEADER" https://api.github.com/user/repos -d "{\"name\":\"$REPO_NAME\", \"private\":$VISIBILITY, \"description\":\"$DESCRIPTION\"}")

# 2. Récupère l’URL du repo
if [ "$USE_SSH" = true ]; then
  REMOTE_URL="git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"
else
  REMOTE_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
fi

# 3. Initialise Git localement
echo "📁 Initialisation du repo local..."
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin "$REMOTE_URL"
git push -u origin main

echo "✅ Déploiement terminé : $REMOTE_URL"
