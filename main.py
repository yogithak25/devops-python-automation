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

def main():
    print("🔥 Starting DevOps Automation Setup...\n")

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

    print("\n✅ ALL TOOLS INSTALLED SUCCESSFULLY!")

if __name__ == "__main__":
    main()

