# finos-legend-k8s-bundle
Juju bundle for all the [FINOS Legend](https://legend.finos.org)
[Juju](https://juju.is) Charmed operators on Kubernetes.

The bundle will deploy and relate the following applications:
* [mongodb-k8s](https://github.com/canonical/mongodb-operator)
* [finos-legend-db-k8s](https://github.com/aznashwan/legend-database-manager)
* [finos-legend-gitlab-integrator-k8s](https://github.com/aznashwan/finos-legend-gitlab-integrator-k8s)
* [finos-legend-sdlc-k8s](https://github.com/aznashwan/legend-sdlc-server-operator)
* [finos-legend-engine-k8s](https://github.com/aznashwan/legend-engine-server-operator)
* [finos-legend-studio-k8s](https://github.com/aznashwan/legend-studio-operator)

## 0. MicroK8s and Juju setup

The following section will provide quick setup instructions for
[MicroK8s](https://juju.is/docs/olm/microk8s) and Juju on Ubuntu 20.04.
Note that Juju can be configured to use any Kubernetes deployment, so you can
also bring your own.

#### MicroK8s installation:

```bash
sudo snap install microk8s --classic
sudo snap alias microk8s.kubectl kubectl

sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube
newgrp microk8s
microk8s status --wait-ready

sudo microk8s.enable dns storage ingress
# might need to give it a minute, check using:
microk8s status
```

#### Juju setup:

```bash
juju bootstrap microk8s micro

# This may take a while, check the status using:
juju status

juju add-model legend
```

## 1. Bundle deployment

After setting up Juju on the Kubernetes of your choice:
```bash
# Deploy the bundle:
juju deploy finos-legend-bundle
```

The above should yield a model containing all the Legend apps in either
`blocked` or `waiting` status, and require GitLab configuration to proceed.

## 2. GitLab configuration

### 2.A: Using private GitLab (recommended)

Prerequisites:
* a private GitLab deployment
* a [personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) for the GitLab

```bash
juju config finos-legend-gitlab-integrator-k8s \
    gitlab-host=10.107.2.9 gitlab-port 443 \
    access-token="CqVrcbHOMeU="
```

### 2.B: Using pre-created GitLab application

Prerequisites:
* access to the portal of [gitlab.com](https://gitlab.com) or the private GitLab
* application creation rights on said account

#### Creating the GitLab Application:
* login to Gitlab
* Go top-left to User Settings > Applications
* Create a new application with the following:
  - Name: "Legend Demo"
  - Confidential: yes
  - Scopes: openid, profile, api
  - Redirect URI: set it to http://localhost:8080/callback
* __Save the Client ID and Secret for later__

#### Setting the GitLab application creds:

```bash
# NOTE: one may optionally add the following, else it defaults to gitlab.com:
# api-scheme=http gitlab-host=10.107.2.9 gitlab-port 443
juju config finos-legend-gitlab-integrator-k8s \
    bypass-client-id=<cliend id> \
    bypass-client-secret=<client secret>
```

#### Fetching the redirect URIs:

Once the `finos-legend-gitlab-integrator-k8s` becomes `active`:
```bash
user@ubuntu:~$ juju status | grep gitlab
finos-legend-gitlab-integrator-k8s/0*  active    idle   10.1.184.238

user@ubuntu:~$ juju run-action finos-legend-gitlab-integrator-k8s/0 get-redirect-uris
Action queued with id: "2"

user@ubuntu:~$ juju show-action-output 2
UnitId: finos-legend-gitlab-integrator-k8s/0
id: "2"
results:
  result: |-
    http://10.1.184.224:6060/api/callback
    http://10.1.184.236:7070/api/auth/callback
    http://10.1.184.236:7070/api/pac4j/login/callback
    http://10.1.184.241:8080/studio/log.in/callback
status: completed
timing:
  completed: 2021-09-27 18:50:39 +0000 UTC
  enqueued: 2021-09-27 18:50:38 +0000 UTC
  started: 2021-09-27 18:50:38 +0000 UTC
```

#### Setting the above redirect URIs into GitLab:
* log back into your GitLab portal
* go to the application created previously
* edit the Redirect URI setting of the application
* paste the output of the `result` field from the `juju show-action-output`
  command run previously
