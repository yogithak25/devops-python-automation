import os
from utils.executor import run_command


# -----------------------------
# CHECK: ArgoCD Installed
# -----------------------------
def is_argocd_installed():
    output = os.popen(
        "kubectl get pods -n argocd --no-headers 2>/dev/null"
    ).read()

    return "argocd-server" in output


# -----------------------------
# GET CURRENT NODEPORT
# -----------------------------
def get_nodeport():
    output = os.popen(
        "kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null"
    ).read().strip()

    return output.replace("'", "")


# -----------------------------
# CHECK: Service Type
# -----------------------------
def is_nodeport():
    output = os.popen(
        "kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.type}' 2>/dev/null"
    ).read().strip()

    return output == "NodePort"


# -----------------------------
# WAIT FOR ARGOCD PODS
# -----------------------------
def wait_for_argocd():
    print("\n⏳ Waiting for ArgoCD pods...\n")

    for i in range(30):
        output = os.popen("kubectl get pods -n argocd").read()

        if "argocd-server" in output and "Running" in output:
            print("✅ ArgoCD pods are running!")
            return

        print(f"Waiting... ({i+1}/30)")
        run_command("sleep 10")

    print("❌ ArgoCD pods not ready!")


# -----------------------------
# EXPOSE SERVICE (FIXED NODEPORT)
# -----------------------------
def expose_argocd():

    FIXED_PORT = "32574"

    print("\n🌐 Configuring ArgoCD NodePort...\n")

    current_port = get_nodeport()

    # Already correct → skip
    if is_nodeport() and current_port == FIXED_PORT:
        print(f"✅ ArgoCD already using NodePort {FIXED_PORT}. Skipping...")
        return

    print("🔧 Setting NodePort to 32574...")

    run_command(f"""
    kubectl patch svc argocd-server -n argocd --type='merge' -p '
    {{
      "spec": {{
        "type": "NodePort",
        "ports": [
          {{
            "port": 80,
            "targetPort": 8080,
            "nodePort": {FIXED_PORT}
          }}
        ]
      }}
    }}'
    """)

    print(f"✅ ArgoCD exposed at NodePort {FIXED_PORT}")


# -----------------------------
# INSTALL ARGOCD
# -----------------------------
def install_argocd():

    print("\n🚀 Installing ArgoCD...\n")

    # Namespace
    run_command("kubectl get ns argocd || kubectl create ns argocd")

    # Install
    if not is_argocd_installed():

        print("📦 Applying ArgoCD manifests...")

        run_command("""
        kubectl apply -n argocd \
        -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --server-side
        """)

        wait_for_argocd()

    else:
        print("✅ ArgoCD already installed.")

    # Fix NodePort
    expose_argocd()

    # Show service
    print("\n🔎 ArgoCD Service Info:\n")
    run_command("kubectl get svc argocd-server -n argocd")

    print("\n✅ ArgoCD Setup Completed!\n")
