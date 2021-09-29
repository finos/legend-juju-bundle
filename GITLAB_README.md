# Quick setup guide for private GitLab

This document aims to detail some quick and easy steps to deploy a GitLab using
the existing Legend Docker-compose scripts.

## Prerequisites:

On an Ubuntu 20.04 machine:

```bash
sudo apt install docker.io python3-pip git
sudo pip3 install --upgrade pip

# NOTE: must be run as a separate command:
sudo pip3 install docker-compose
```

## Repo fetching and editing:

```bash
# Pick a directory for the build files:
BUILD_DIR=/tmp/legend
mkdir -p $BUILD_DIR

# Clone the repo:
git clone https://github.com/finos/legend

# Go to the right directory:
cd legend/installers/docker-compose/legend

# Edit the config and set the following:
# BUILD_DIR=<your build dir>
# HOST_DNS_NAME = localhost
# HOST_ADDRESS = <the IP address of your host>
vim config.properties
```

Replace the 'docker-compose.yml' file with the following:
```bash
version: "3.8"
services:
  gitlab:
    container_name: $GITLAB_SERVICE_NAME
    image: gitlab/gitlab-ce:$GITLAB_IMAGE_VERSION
    hostname: $GITLAB_HOST_NAME
    ports:
      - $GITLAB_PORT:443
    networks:
      - legend
    volumes:
      - $BUILD_DIR/container-data/gitlab:/etc/gitlab
      - $BUILD_DIR/generated-configs/gitlab:/config
      - $BUILD_DIR/scripts:/scripts
    env_file:
      - $BUILD_DIR/.env
    environment:
      GITLAB_POST_RECONFIGURE_SCRIPT: /scripts/setup-gitlab.sh
      # Add any other gitlab.rb configuration here, each on its own line
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'https://$GITLAB_URL'
        gitlab_rails['lfs_enabled'] = true
        nginx['listen_port'] = 443
        nginx['ssl_certificate'] = '$GITLAB_CERT_FILE'
        nginx['ssl_certificate_key'] = '$GITLAB_KEY_FILE'
        letsencrypt['enable'] = false
        gitlab_rails['initial_root_password'] = '$GITLAB_ROOT_PASSWORD'

networks:
  legend: {}
```

## Deployment:

```bash
# NOTE: make sure you're in the correct dir:
cd $LEGEND_REPO/installers/docker-compose/legend

# Generate build files:
./scripts/setup.sh config.properties
### NOTE:
### Save the GitLab user/pass access token!!!

# Run the deployment:
sudo docker-compose --verbose --env-file $BUILD_DIR/.env up --detach

# NOTE: it'll take 5-10 minutes for the GitLab service to be functional!!!
```

## Using with the bundle:

```bash
# Done in advance:
# juju deploy finos-legend-bundle --channel=edge

# NOTE: this is the same `$BUILD_DIR` as before:
CERT=`base64 localhost.der -w 0 $BUILD_DIR/ssl/localhost.der`

# Reconfigure the GitLab intergrator:
juju config finos-legend-gitlab-integrator-k8s \
	gitlab-host=172.16.16.8 gitlab-port=6443 verify-ssl=false \
	application-name="test" \
	gitlab-host-der-b64="$CERT" \
	access-token="<token>"
```


## Cleanup and retry:

```bash
# Removes everything:
cd $LEGEND_REPO/installers/docker-compose/legend
sudo docker-compose --verbose --env-file /tmp/legend/.env down

# NOTE: remember to delete all the state files before retrying!!!
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR
```
