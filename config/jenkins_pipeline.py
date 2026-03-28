import requests
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
    r = requests.get(
        f"{config['JENKINS_URL']}/crumbIssuer/api/json",
        auth=auth()
    )
    data = r.json()
    return {data["crumbRequestField"]: data["crumb"]}


# -----------------------------
# CHECK JOB EXISTS
# -----------------------------
def job_exists(job_name):

    url = f"{config['JENKINS_URL']}/job/{job_name}/api/json"

    r = requests.get(url, auth=auth())

    return r.status_code == 200


# -----------------------------
# CREATE PIPELINE JOB
# -----------------------------
def create_pipeline(job_name, repo_url, branch="main"):

    if job_exists(job_name):
        print(f"✅ {job_name} already exists")
        return

    print(f"🚀 Creating pipeline: {job_name}")

    xml = f"""
<flow-definition plugin="workflow-job">
  <actions/>
  <description>{job_name}</description>
  <keepDependencies>false</keepDependencies>

  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <com.cloudbees.jenkins.GitHubPushTrigger plugin="github">
          <spec></spec>
        </com.cloudbees.jenkins.GitHubPushTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>

  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
    <scm class="hudson.plugins.git.GitSCM">
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>{repo_url}</url>
          <credentialsId>github-cred</credentialsId>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>

      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/{branch}</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
    </scm>

    <scriptPath>Jenkinsfile</scriptPath>
  </definition>

  <triggers/>
</flow-definition>
"""

    headers = get_crumb()
    headers["Content-Type"] = "application/xml"

    r = requests.post(
        f"{config['JENKINS_URL']}/createItem?name={job_name}",
        auth=auth(),
        headers=headers,
        data=xml
    )

    if r.status_code in [200, 201]:
        print(f"✅ {job_name} created")
    else:
        print(f"❌ Failed to create {job_name}: {r.text}")


# -----------------------------
# MAIN
# -----------------------------
def setup_pipelines():

    print("\n🚀 JENKINS PIPELINE SETUP STARTED\n")

    pipelines = [
        {
            "name": "java-devops-pipeline",
            "repo": "https://github.com/yogithak25/end-to-end-devops-project.git"
        },
        {
            "name": "python-devops-pipeline",
            "repo": "https://github.com/yogithak25/python-devops-project.git"
        }
    ]

    for p in pipelines:
        create_pipeline(p["name"], p["repo"])

    print("\n✅ Jenkins Pipelines Created Successfully\n")
