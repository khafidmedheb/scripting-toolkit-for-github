⚠️ **This repository is currently under active development. Features and structure may change frequently.**

<h1 align="center">🚀 Git Auto Init</h1>

<p align="center">
  <b>Initialise un dépôt Git local et le pousse automatiquement sur GitHub (via Bash ou Python)</b><br/>
  <i>Inclut un script Shell et un script Python, configurables en 1 minute.</i>
</p>

---

## 🔧 Fonctionnalités

- 📂 Initialise un dépôt Git local (`git init`, `add`, `commit`...)
- ☁️ Crée automatiquement un dépôt distant sur GitHub via l'API
- 🔁 Push initial sur `main`
- 🐍 Script Bash (`deploy.sh`) **ou** Python (`deploy.py`)
- 🔐 Gestion du `GITHUB_TOKEN` via `.env` ou variable d’environnement

---

## 📁 Arborescence

```
git-auto-init/
│
├── deploy.sh         # Script Bash principal
├── deploy.py         # Script Python équivalent
├── .env.example      # Fichier d'exemple pour stocker ton token GitHub
└── README.md         # Ce fichier
```

---

## 🚀 Utilisation rapide

### 1. Cloner ou décompresser le projet

```bash
unzip git-auto-init.zip
cd git-auto-init
```

### 2. Ajouter ton token GitHub

- [Créer un token ici](https://github.com/settings/tokens) (avec droits `repo`)
- Le stocker dans `.env` ou comme variable d’environnement

```bash
# Option 1 (temporaire)
export GITHUB_TOKEN=ghp_tonTokenIci123456

# Option 2 (permanent)
cp .env.example .env
# puis édite le fichier .env avec ton token
```

### 3. Personnaliser le nom du repo

Dans `deploy.sh` ou `deploy.py`, modifie :

```bash
GITHUB_USERNAME="ton-user"
REPO_NAME="nom-du-repo"
DESCRIPTION="Ma description"
PRIVATE=true
```

---

## ⚙️ Exécution

### ➤ Avec le script Bash

```bash
bash deploy.sh
```

### ➤ Avec le script Python

```bash
pip install requests
python deploy.py
```

---

## 💡 Astuces

- Tu peux ajouter un **alias Git** dans `~/.gitconfig` :
```ini
[alias]
  initpush = "!f() { git init && git add . && git commit -m \"init\" && git branch -M main && git remote add origin $1 && git push -u origin main; }; f"
```
Utilisation :
```bash
git initpush https://github.com/ton-user/ton-repo.git
```

---

## ✅ Exigences

- Git installé (`git --version`)
- Un token GitHub valide
- Python ≥ 3.7 si tu utilises `deploy.py`

---

## 📬 Contact

Créé avec ❤️ par Khalid HAFID-MEDHEB

---

> ⭐️ N'oublie pas de donner une ⭐️ à ce repo si tu l'aimes !
