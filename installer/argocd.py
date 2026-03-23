import os
from utils.executor import run_command
def is_argocd_installed():
    return os.system("kubectl get pods -n argocd > /dev/null 2>&1") == 0

def install_argocd():
    if is_argocd_installed():
        print("✅ ArgoCD already installed. Skipping installation.")
        return

    run_command("kubectl create namespace argocd")
    run_command("kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --server-side")

