import os
import subprocess
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio

# Imports LangChain et OpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain.callbacks import StreamingStdOutCallbackHandler

# === CONFIGURATION ===
class SmartDeployConfig:
    def __init__(self):
        self.github_username = os.getenv("GITHUB_USERNAME", "votre-user")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_ssh = False
        self.auto_detect_language = True
        self.auto_generate_readme = True
        self.auto_detect_license = True
        
        if not self.github_token:
            raise Exception("⚠️  GITHUB_TOKEN non défini dans l'environnement.")
        if not self.openai_api_key:
            raise Exception("⚠️  OPENAI_API_KEY non défini dans l'environnement.")

# === ANALYSEUR DE PROJET INTELLIGENT ===
class ProjectAnalyzer:
    """Analyse intelligente de la structure et du contenu du projet"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.file_extensions = {}
        self.dependencies = []
        self.frameworks = []
        
    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analyse la structure du projet et détecte les technologies"""
        analysis = {
            "languages": self._detect_languages(),
            "frameworks": self._detect_frameworks(),
            "dependencies": self._extract_dependencies(),
            "project_type": self._determine_project_type(),
            "files_count": self._count_files(),
            "suggested_topics": self._suggest_github_topics()
        }
        return analysis
    
    def _detect_languages(self) -> Dict[str, int]:
        """Détecte les langages de programmation utilisés"""
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#',
            '.php': 'PHP', '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust',
            '.swift': 'Swift', '.kt': 'Kotlin', '.scala': 'Scala',
            '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
            '.vue': 'Vue', '.jsx': 'React', '.tsx': 'React'
        }
        
        languages = {}
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and not str(file_path).startswith('.'):
                ext = file_path.suffix.lower()
                if ext in language_map:
                    lang = language_map[ext]
                    languages[lang] = languages.get(lang, 0) + 1
        
        return dict(sorted(languages.items(), key=lambda x: x[1], reverse=True))
    
    def _detect_frameworks(self) -> List[str]:
        """Détecte les frameworks utilisés"""
        frameworks = []
        
        # Vérification des fichiers de configuration
        config_files = {
            'package.json': ['React', 'Vue', 'Angular', 'Express'],
            'requirements.txt': ['Django', 'Flask', 'FastAPI'],
            'pom.xml': ['Spring', 'Maven'],
            'build.gradle': ['Spring Boot', 'Android'],
            'Cargo.toml': ['Rust'],
            'go.mod': ['Go'],
            'composer.json': ['Laravel', 'Symfony']
        }
        
        for config_file, possible_frameworks in config_files.items():
            if (self.project_path / config_file).exists():
                content = (self.project_path / config_file).read_text()
                for framework in possible_frameworks:
                    if framework.lower() in content.lower():
                        frameworks.append(framework)
        
        return list(set(frameworks))
    
    def _extract_dependencies(self) -> List[str]:
        """Extrait les dépendances principales"""
        dependencies = []
        
        # Python
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            deps = req_file.read_text().strip().split('\n')
            dependencies.extend([dep.split('==')[0].split('>=')[0] for dep in deps if dep])
        
        # Node.js
        package_file = self.project_path / "package.json"
        if package_file.exists():
            try:
                package_data = json.loads(package_file.read_text())
                if 'dependencies' in package_data:
                    dependencies.extend(package_data['dependencies'].keys())
            except json.JSONDecodeError:
                pass
        
        return dependencies[:10]  # Limite aux 10 principales
    
    def _determine_project_type(self) -> str:
        """Détermine le type de projet"""
        if (self.project_path / "manage.py").exists():
            return "Django Web Application"
        elif (self.project_path / "app.py").exists() or (self.project_path / "main.py").exists():
            return "Python Application"
        elif (self.project_path / "package.json").exists():
            return "Node.js Application"
        elif (self.project_path / "index.html").exists():
            return "Web Application"
        elif (self.project_path / "Dockerfile").exists():
            return "Containerized Application"
        else:
            return "General Project"
    
    def _count_files(self) -> Dict[str, int]:
        """Compte les fichiers par type"""
        counts = {"total": 0, "code": 0, "config": 0}
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs'}
        config_extensions = {'.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.conf'}
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and not str(file_path).startswith('.'):
                counts["total"] += 1
                ext = file_path.suffix.lower()
                if ext in code_extensions:
                    counts["code"] += 1
                elif ext in config_extensions:
                    counts["config"] += 1
        
        return counts
    
    def _suggest_github_topics(self) -> List[str]:
        """Suggère des topics GitHub basés sur l'analyse"""
        topics = []
        languages = self._detect_languages()
        frameworks = self._detect_frameworks()
        
        # Ajouter les langages principaux
        for lang in list(languages.keys())[:3]:
            topics.append(lang.lower().replace('+', 'plus'))
        
        # Ajouter les frameworks
        for framework in frameworks:
            topics.append(framework.lower().replace(' ', '-'))
        
        return topics[:5]  # Limite à 5 topics

# === GÉNÉRATEUR IA DE CONTENU ===
class AIContentGenerator:
    """Génère du contenu intelligent pour le repository"""
    
    def __init__(self, config: SmartDeployConfig):
        self.config = config
        self.llm = ChatOpenAI(
            api_key=config.openai_api_key,
            model="gpt-4",
            temperature=0.7,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
    
    def generate_repo_description(self, analysis: Dict[str, Any]) -> str:
        """Génère une description intelligente du repository"""
        prompt = f"""
        Basé sur l'analyse suivante d'un projet de code, génère une description concise et professionnelle 
        pour un repository GitHub (maximum 100 caractères):

        Type de projet: {analysis['project_type']}
        Langages principaux: {', '.join(list(analysis['languages'].keys())[:3])}
        Frameworks détectés: {', '.join(analysis['frameworks'])}
        Nombre de fichiers: {analysis['files_count']['total']}

        La description doit être en français et mettre en valeur l'aspect technique du projet.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    
    def generate_readme_content(self, analysis: Dict[str, Any], repo_name: str) -> str:
        """Génère un README.md complet et professionnel"""
        prompt = f"""
        Crée un README.md complet et professionnel pour un projet GitHub avec les informations suivantes:

        Nom du projet: {repo_name}
        Type de projet: {analysis['project_type']}
        Langages: {', '.join(analysis['languages'].keys())}
        Frameworks: {', '.join(analysis['frameworks'])}
        Dépendances principales: {', '.join(analysis['dependencies'][:5])}

        Le README doit inclure:
        - Une description engageante du projet
        - Les prérequis d'installation
        - Les instructions d'installation
        - Un exemple d'utilisation
        - Une section de contribution
        - Les badges appropriés

        Utilise le markdown et sois professionnel mais accessible.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    
    def suggest_repo_name(self, analysis: Dict[str, Any]) -> str:
        """Suggère un nom de repository intelligent"""
        prompt = f"""
        Suggère un nom de repository GitHub créatif et professionnel basé sur:
        
        Type de projet: {analysis['project_type']}
        Langages principaux: {', '.join(list(analysis['languages'].keys())[:2])}
        Frameworks: {', '.join(analysis['frameworks'][:2])}
        
        Le nom doit être:
        - Court (max 30 caractères)
        - Mémorable
        - Professionnel
        - Sans espaces (utilise des tirets)
        
        Réponds seulement avec le nom suggéré.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip().lower().replace(' ', '-')

# === AGENT INTELLIGENT DE DÉPLOIEMENT ===
class SmartDeployAgent:
    """Agent intelligent qui orchestre le déploiement"""
    
    def __init__(self, config: SmartDeployConfig):
        self.config = config
        self.analyzer = ProjectAnalyzer()
        self.content_generator = AIContentGenerator(config)
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Initialisation de l'agent avec des outils
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Crée les outils disponibles pour l'agent"""
        tools = [
            Tool(
                name="analyze_project",
                description="Analyse la structure et le contenu du projet actuel",
                func=self._analyze_project_tool
            ),
            Tool(
                name="generate_description",
                description="Génère une description intelligente pour le repository",
                func=self._generate_description_tool
            ),
            Tool(
                name="create_readme",
                description="Crée un fichier README.md professionnel",
                func=self._create_readme_tool
            ),
            Tool(
                name="suggest_name",
                description="Suggère un nom de repository intelligent",
                func=self._suggest_name_tool
            )
        ]
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Crée l'agent OpenAI Functions"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un assistant intelligent spécialisé dans le déploiement de projets sur GitHub.
            Tu peux analyser des projets de code, générer du contenu professionnel, et prendre des décisions
            intelligentes sur la configuration des repositories.
            
            Utilise tes outils pour analyser le projet et proposer les meilleures configurations.
            Sois proactif et donne des conseils professionnels."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        llm = ChatOpenAI(
            api_key=self.config.openai_api_key,
            model="gpt-4",
            temperature=0.3
        )
        
        agent = create_openai_functions_agent(llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, memory=self.memory, verbose=True)
    
    def _analyze_project_tool(self, input_str: str) -> str:
        """Outil d'analyse de projet"""
        analysis = self.analyzer.analyze_project_structure()
        return json.dumps(analysis, indent=2, ensure_ascii=False)
    
    def _generate_description_tool(self, input_str: str) -> str:
        """Outil de génération de description"""
        analysis = self.analyzer.analyze_project_structure()
        description = self.content_generator.generate_repo_description(analysis)
        return description
    
    def _create_readme_tool(self, repo_name: str) -> str:
        """Outil de création de README"""
        analysis = self.analyzer.analyze_project_structure()
        readme_content = self.content_generator.generate_readme_content(analysis, repo_name)
        
        # Écrire le README
        readme_path = Path("README.md")
        readme_path.write_text(readme_content, encoding='utf-8')
        
        return f"README.md créé avec succès ({len(readme_content)} caractères)"
    
    def _suggest_name_tool(self, input_str: str) -> str:
        """Outil de suggestion de nom"""
        analysis = self.analyzer.analyze_project_structure()
        suggested_name = self.content_generator.suggest_repo_name(analysis)
        return suggested_name
    
    async def deploy_intelligently(self) -> Dict[str, Any]:
        """Déploie le projet de manière intelligente"""
        print("🤖 Démarrage du déploiement intelligent...")
        
        # Étape 1: Analyse du projet
        print("\n📊 Analyse du projet...")
        analysis_result = self.agent.invoke({
            "input": "Analyse le projet actuel et donne-moi un résumé détaillé"
        })
        
        # Étape 2: Génération du nom de repository
        print("\n🏷️  Génération du nom de repository...")
        name_result = self.agent.invoke({
            "input": "Suggère un nom intelligent pour ce repository"
        })
        
        # Étape 3: Génération de la description
        print("\n📝 Génération de la description...")
        description_result = self.agent.invoke({
            "input": "Génère une description professionnelle pour ce repository"
        })
        
        # Étape 4: Création du README
        print("\n📖 Création du README...")
        readme_result = self.agent.invoke({
            "input": f"Crée un README.md professionnel pour le repository"
        })
        
        # Récupération des résultats
        analysis = self.analyzer.analyze_project_structure()
        suggested_name = self.content_generator.suggest_repo_name(analysis)
        description = self.content_generator.generate_repo_description(analysis)
        
        return {
            "repo_name": suggested_name,
            "description": description,
            "analysis": analysis,
            "readme_created": True
        }

# === DÉPLOYEUR GITHUB INTELLIGENT ===
class IntelligentGitHubDeployer:
    """Déployeur GitHub avec intelligence artificielle"""
    
    def __init__(self, config: SmartDeployConfig):
        self.config = config
        self.agent = SmartDeployAgent(config)
    
    async def deploy(self, custom_repo_name: Optional[str] = None) -> None:
        """Déploie le projet avec l'intelligence artificielle"""
        try:
            # Déploiement intelligent
            smart_results = await self.agent.deploy_intelligently()
            
            # Utilisation du nom personnalisé ou suggéré
            repo_name = custom_repo_name or smart_results["repo_name"]
            description = smart_results["description"]
            analysis = smart_results["analysis"]
            
            print(f"\n🚀 Déploiement de '{repo_name}'")
            print(f"📄 Description: {description}")
            print(f"🔧 Technologies détectées: {', '.join(analysis['languages'].keys())}")
            
            # Création du repository GitHub
            await self._create_github_repo(repo_name, description, analysis)
            
            # Configuration Git et push
            await self._setup_git_and_push(repo_name)
            
            print(f"\n✅ Déploiement intelligent terminé!")
            print(f"🔗 Repository: https://github.com/{self.config.github_username}/{repo_name}")
            
        except Exception as e:
            print(f"❌ Erreur lors du déploiement: {str(e)}")
            raise
    
    async def _create_github_repo(self, repo_name: str, description: str, analysis: Dict[str, Any]) -> None:
        """Crée le repository GitHub avec les métadonnées intelligentes"""
        print("📡 Création du repository GitHub...")
        
        headers = {
            "Authorization": f"token {self.config.github_token}",
            "Accept": "application/vnd.github+json",
        }
        
        # Détermination de la visibilité basée sur le type de projet
        is_private = "personal" in analysis.get("project_type", "").lower()
        
        data = {
            "name": repo_name,
            "description": description,
            "private": is_private,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": len(analysis.get("dependencies", [])) > 5,  # Wiki si projet complexe
            "auto_init": False,
            "license_template": "mit" if not is_private else None,
            "topics": analysis.get("suggested_topics", [])
        }
        
        response = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
        if response.status_code != 201:
            raise Exception(f"Erreur GitHub: {response.status_code} - {response.text}")
        
        print(f"✅ Repository créé: {'privé' if is_private else 'public'}")
    
    async def _setup_git_and_push(self, repo_name: str) -> None:
        """Configure Git et pousse le code"""
        print("📁 Configuration Git...")
        
        # URL du repository
        if self.config.use_ssh:
            remote_url = f"git@github.com:{self.config.github_username}/{repo_name}.git"
        else:
            remote_url = f"https://github.com/{self.config.github_username}/{repo_name}.git"
        
        # Commandes Git
        commands = [
            ["git", "init"],
            ["git", "add", "."],
            ["git", "commit", "-m", "🚀 Initial commit - Deployed with AI"],
            ["git", "branch", "-M", "main"],
            ["git", "remote", "add", "origin", remote_url],
            ["git", "push", "-u", "origin", "main"]
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️  Avertissement: {' '.join(cmd)} - {result.stderr}")
        
        print("✅ Code poussé vers GitHub")

# === FONCTION PRINCIPALE ===
async def main():
    """Fonction principale du déploiement intelligent"""
    print("🤖 === DÉPLOYEUR INTELLIGENT GITHUB ===")
    print("Powered by OpenAI & LangChain\n")
    
    try:
        # Configuration
        config = SmartDeployConfig()
        
        # Déployeur intelligent
        deployer = IntelligentGitHubDeployer(config)
        
        # Déploiement
        await deployer.deploy()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Installation des dépendances requises
    required_packages = [
        "langchain",
        "langchain-openai", 
        "requests",
        "openai"
    ]
    
    print("📦 Vérification des dépendances...")
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"⚠️  Installation de {package}...")
            subprocess.run(["pip", "install", package], check=True)
    
    # Exécution
    asyncio.run(main())