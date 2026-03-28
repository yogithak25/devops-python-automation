from installer.common import update_system, install_basic_tools
from installer.python_env import install_python_env
from installer.docker import install_docker, fix_docker
from installer.kubernetes import install_kubernetes
from installer.jenkins import install_jenkins
from installer.maven import install_maven
from installer.sonar import install_sonarqube
from installer.nexus import install_nexus
from installer.trivy import install_trivy
from installer.argocd import install_argocd

# -----------------------------
# CONFIG IMPORTS (NEW)
# -----------------------------
from config.sonarqube_config import setup_sonarqube
from config.nexus_config import setup_nexus
from config.jenkins_config import setup_jenkins
from config.github_config import setup_github
from config.argocd_config import setup_argocd
from config.jenkins_pipeline import setup_pipelines


def main():

    print("🔥 DEVOPS FULL AUTOMATION STARTED\n")

    # =====================================================
    # 🔹 PHASE 1: INSTALLATION
    # =====================================================
    print("\n📦 PHASE 1: INSTALLATION\n")

    update_system()
    install_basic_tools()

    install_python_env()

    install_docker()
    fix_docker()

    install_kubernetes()

    install_jenkins()
    install_maven()
    install_sonarqube()
    install_nexus()
    install_trivy()
    install_argocd()

    print("\n✅ INSTALLATION COMPLETED\n")

    # =====================================================
    # 🔹 PHASE 2: CONFIGURATION
    # =====================================================
    print("\n⚙️ PHASE 2: CONFIGURATION\n")

    # 1️⃣ SonarQube FIRST (generates token)
    sonar_token = setup_sonarqube()

    # 2️⃣ Nexus (repo + credentials)
    setup_nexus()

    # 3️⃣ Jenkins (plugins + creds + tools)
    setup_jenkins()

    # 4️⃣ GitHub (webhooks)
    setup_github()

    # 5️⃣ ArgoCD (apps)
    setup_argocd()

    print("\n✅ CONFIGURATION COMPLETED\n")

    # =====================================================
    # 🔹 PHASE 3: PIPELINE SETUP
    # =====================================================
    print("\n🚀 PHASE 3: PIPELINE SETUP\n")

    setup_pipelines()

    print("\n🎉 FULL DEVOPS AUTOMATION COMPLETED SUCCESSFULLY!\n")


if __name__ == "__main__":
    main()
