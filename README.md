[![FINOS - Incubating](https://cdn.jsdelivr.net/gh/finos/contrib-toolbox@master/images/badge-incubating.svg)](https://finosfoundation.atlassian.net/wiki/display/FINOS/Incubating)

# finos-legend-k8s-bundle
Juju bundle for all the [FINOS Legend](https://legend.finos.org)
[Juju](https://juju.is) Charmed operators on Kubernetes.

The bundle will deploy and relate the following applications:
* [mongodb-k8s](https://github.com/canonical/mongodb-operator)
* [finos-legend-db-k8s](https://github.com/canonical/finos-legend-db-operator)
* [finos-legend-gitlab-integrator-k8s](https://github.com/canonical/finos-legend-gitlab-integrator)
* [finos-legend-sdlc-k8s](https://github.com/canonical/finos-legend-sdlc-server-operator)
* [finos-legend-engine-k8s](https://github.com/canonical/finos-legend-engine-server-operator)
* [finos-legend-studio-k8s](https://github.com/canonical/finos-legend-studio-operator/pull/1)

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
sudo snap install juju --classic
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
* a private GitLab deployment configured to use HTTPS
* a [personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) for the GitLab

```bash
juju config finos-legend-gitlab-integrator-k8s \
    gitlab-host="<GitLab IP or hostname>" gitlab-port=443 access-token="CqVrcbHOMeU="
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

### GitLab application reconfiguration or reuse:

Due to intentional security-minded limitations in the GitLab APIs, the client ID and
secret of existing applications cannot be queried programatically, and can only be known
if creating an application on the spot.

In this sense, reusing GitLab applications upon redeploying the integrator will
require taking one of the following options:
1. *reusing an existing GitLab application* can be achieved by reconfiguring the
   charm using the `bypass-client-id` and `bypass-client-secret` configuration
   options with the client ID/secret which can be obtained from
   the GitLab Web user interface as described in section 2.B above.
2. manually deleting the application and having the integrator create a new one on the next run
3. reconfiguring the integrator with the `application-name` config option to create a new
   application with a different name. Note that this does NOT clean up/replace the old app.

## Automatic FINOS Legend image updates

This repository has a [Github action](.github/workflows/publish_images.yaml) configured to check if any new [FINOS Legend releases](https://github.com/finos/legend) have been published. If so, the Github action will pull the FINOS Legend Engine, SDLC, and Studio images defined in the release's ``manifest.josn`` file, pull them, upload them into Charmhub, and release the Legend Charms with those image revisions. For more information on the Github action and how it se set up, see [here](docs/CharmhubPublishing.md).

## Contributing

Visit Legend [Contribution Guide](https://github.com/finos/legend/blob/master/CONTRIBUTING.md) to learn how to contribute to Legend.

## License

Copyright (c) 2021-present, Canonical

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)


