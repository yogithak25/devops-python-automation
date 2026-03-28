import time
import requests
import json
import os
from config.env_loader import get_env

config = get_env()


# -----------------------------
# AUTH
# -----------------------------
def auth():
    return (config["JENKINS_USER"], config["JENKINS_TOKEN"])


# -----------------------------
# CRUMB 
# -----------------------------
def get_crumb():
    try:
        r = requests.get(
            f"{config['JENKINS_URL']}/crumbIssuer/api/json",
            auth=auth()
        )
        if r.status_code == 200:
            data = r.json()
            return {data["crumbRequestField"]: data["crumb"]}
    except:
        pass
    return {}


# -----------------------------
# WAIT FOR JENKINS
# -----------------------------
def wait_for_jenkins():
    print("\n⏳ Waiting for Jenkins...\n")

    for i in range(30):
        try:
            r = requests.get(
                f"{config['JENKINS_URL']}/api/json",
                auth=auth(),
                timeout=5
            )
            if r.status_code == 200:
                print("✅ Jenkins Ready")
                return
        except:
            pass

        print(f"Waiting... ({i+1}/30)")
        time.sleep(10)

    raise Exception("❌ Jenkins not reachable")


# -----------------------------
# GET INSTALLED PLUGINS
# -----------------------------
def get_plugins():
    try:
        r = requests.get(
            f"{config['JENKINS_URL']}/pluginManager/api/json?depth=1",
            auth=auth()
        )
        return [p["shortName"] for p in r.json().get("plugins", [])]
    except:
        return []


# -----------------------------
# INSTALL PLUGINS 
# -----------------------------
def install_plugins():

    print("\n📦 Installing Plugins...\n")

    plugins = [
        "pipeline-stage-view",
        "github",
        "config-file-provider",
        "maven-plugin",
        "pipeline-maven",
        "sonar",
        "coverage",
        "jacoco",
        "nexus-artifact-uploader",
        "docker-workflow",
        "docker-plugin",
        "kubernetes",
        "kubernetes-cli",
        "dependency-check-jenkins-plugin"
    ]

    installed = get_plugins()

    to_install = [
        f'<install plugin="{p}@latest"/>'
        for p in plugins if p not in installed
    ]

    if not to_install:
        print("✅ All plugins already installed.")
        return

    xml = f"<jenkins>{''.join(to_install)}</jenkins>"

    headers = get_crumb()
    headers["Content-Type"] = "text/xml"

    requests.post(
        f"{config['JENKINS_URL']}/pluginManager/installNecessaryPlugins",
        auth=auth(),
        headers=headers,
        data=xml
    )

    print("⏳ Installing plugins... waiting 60s")
    time.sleep(60)


# -----------------------------
# CHECK CREDENTIAL
# -----------------------------
def credential_exists(cid):
    try:
        r = requests.get(
            f"{config['JENKINS_URL']}/credentials/store/system/domain/_/api/json?depth=2",
            auth=auth()
        )
        if r.status_code != 200:
            return False

        data = r.json()

        def search(creds):
            for c in creds:
                if c.get("id") == cid:
                    return True
                if "credentials" in c:
                    if search(c["credentials"]):
                        return True
            return False

        return search(data.get("credentials", []))

    except:
        return False


# -----------------------------
# ADD CREDENTIALS 
# -----------------------------
def add_credentials():

    print("\n🔐 Adding Credentials...\n")

    url = f"{config['JENKINS_URL']}/credentials/store/system/domain/_/createCredentials"
    headers = get_crumb()

    def create_user_pass(cid, user, pwd):

        if credential_exists(cid):
            print(f"✅ {cid} already exists")
            return

        payload = {
            "": "0",
            "credentials": {
                "scope": "GLOBAL",
                "id": cid,
                "username": user,
                "password": pwd,
                "description": cid,
                "$class": "com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl"
            }
        }

        r = requests.post(
            url,
            auth=auth(),
            headers=headers,
            data={"json": json.dumps(payload)}
        )

        if r.status_code in [200, 201, 204] and credential_exists(cid):
            print(f"✅ {cid} created")
        else:
            print(f"❌ {cid} failed → {r.text}")

    # GitHub
    create_user_pass("github-cred", config["GITHUB_USER"], config["GITHUB_TOKEN"])

    # DockerHub
    create_user_pass("dockerhub-cred", config["DOCKER_USER"], config["DOCKER_PASS"])

    # Nexus
    create_user_pass("nexus-cred", config["NEXUS_USER"], config["NEXUS_PASSWORD"])

    # Sonar Token
    if credential_exists("sonar-token"):
        print("✅ sonar-token already exists")
    else:
        payload = {
            "": "0",
            "credentials": {
                "scope": "GLOBAL",
                "id": "sonar-token",
                "secret": config["SONAR_TOKEN"],
                "description": "sonar-token",
                "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"
            }
        }

        r = requests.post(
            url,
            auth=auth(),
            headers=headers,
            data={"json": json.dumps(payload)}
        )

        if r.status_code in [200, 201, 204]:
            print("✅ sonar-token created")
# -----------------
# GROOVY SCRIPT
# -----------------
def run_groovy(script):

    headers = get_crumb()

    response = requests.post(
        f"{config['JENKINS_URL']}/scriptText",
        auth=auth(),
        headers=headers,
        data={"script": script}
    )

    return response.text


# -----------------------------
# CONFIGURE TOOLS 
# -------------------------
def configure_tools():

    print("\n⚙️ Configuring Tools ...\n")

    groovy_script = """
import jenkins.model.*
import hudson.tasks.Maven
import hudson.tools.InstallSourceProperty
import hudson.tasks.Maven.MavenInstaller
import hudson.plugins.sonar.SonarRunnerInstallation
import hudson.plugins.sonar.SonarRunnerInstaller

def jenkins = Jenkins.instance

// MAVEN
def mavenDesc = jenkins.getDescriptorByType(Maven.DescriptorImpl)

def existingMaven = mavenDesc.installations.find { it.name == "maven-3" }

if (existingMaven == null) {

    def installer = new MavenInstaller("3.9.14")
    def prop = new InstallSourceProperty([installer])

    def maven = new Maven.MavenInstallation("maven-3", "", [prop])

    mavenDesc.setInstallations(maven)
    mavenDesc.save()

    println("Maven created")

} else {
    println("Maven already exists")
}

// SONAR SCANNER
def sonarDesc = jenkins.getDescriptorByType(SonarRunnerInstallation.DescriptorImpl)

def existingSonar = sonarDesc.installations.find { it.name == "sonar-scanner" }

if (existingSonar == null) {

    def installer = new SonarRunnerInstaller("latest")
    def prop = new InstallSourceProperty([installer])

    def sonar = new SonarRunnerInstallation("sonar-scanner", "", [prop])

    sonarDesc.setInstallations(sonar)
    sonarDesc.save()

    println("Sonar scanner created")

} else {
    println("Sonar scanner already exists")
}
"""

    output = run_groovy(groovy_script)
    print(output)

# -----------------------------
# CONFIGURE SONAR 
# -----------------------------
def configure_sonar():

    print("\n🔗 Configuring SonarQube ...\n")

    groovy_script = f"""
import jenkins.model.*
import hudson.plugins.sonar.*
import org.jenkinsci.plugins.structs.describable.DescribableModel

def jenkins = Jenkins.instance
def desc = jenkins.getDescriptorByType(SonarGlobalConfiguration.class)

// Check existing
def existing = desc.installations.find {{ it.name == "sonarqube" }}

if (existing != null) {{
    println("SonarQube already exists")
    return
}}

// Use DescribableModel (SAFE METHOD)
def model = DescribableModel.of(SonarInstallation)

def instance = model.instantiate([
    name: "sonarqube",
    serverUrl: "{config['SONAR_URL']}",
    credentialsId: "sonar-token"
])

def newList = desc.installations as List
newList.add(instance)

desc.installations = newList
desc.save()

println("SonarQube added successfully")
"""

    output = run_groovy(groovy_script)
    print(output)

# -----------------------------
# NEXUS SETTINGS
# -----------------------------
def create_nexus_settings():

    print("\n📦 Creating Nexus settings.xml...\n")

    path = "/var/lib/jenkins/.m2/settings.xml"

    if os.path.exists(path):
        print("✅ settings.xml already exists")
        return

    os.system("sudo mkdir -p /var/lib/jenkins/.m2")
    os.system("sudo chown -R jenkins:jenkins /var/lib/jenkins/.m2")
    os.system("sudo chmod -R 755 /var/lib/jenkins/.m2")

    content = f"""
<settings>
  <servers>
    <server>
      <id>nexus</id>
      <username>{config["NEXUS_USER"]}</username>
      <password>{config["NEXUS_PASSWORD"]}</password>
    </server>
  </servers>
</settings>
"""

    with open("settings.xml", "w") as f:
        f.write(content)

    os.system(f"sudo mv settings.xml {path}")
    os.system("sudo chown jenkins:jenkins /var/lib/jenkins/.m2/settings.xml")

    print("✅ Nexus settings.xml created")


# -----------------------------
# MAIN
# -----------------------------
def setup_jenkins():

    print("\n🚀 FULL JENKINS CONFIGURATION STARTED\n")

    wait_for_jenkins()
    install_plugins()
    add_credentials()
    configure_tools()
    configure_sonar()
    create_nexus_settings()

    print("\n✅ Jenkins FULLY CONFIGURED SUCCESSFULLY\n")
