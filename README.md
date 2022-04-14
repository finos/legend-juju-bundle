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

## Bundle deployment

For a full guide on how to the FINOS Legend bundle, see the
[legend-integration-juju](https://github.com/finos/legend-integration-juju) repository,
which will contain detailed information about the following topics:

[Local deployment](https://github.com/finos/legend-integration-juju/blob/main/docs/deploy/local.md):

- Prerequisites
- Install Microk8s and Juju
- Bootstrap Juju and add the Juju Legend Model
- Deploy the Legend Bundle
- Configure a hostname for your Legend Applications
- Setup and Configure GitLab and pass the GitLab application details to the Legend stack
- Accessing the Legend Studio dashboard
- Destroy setup
- Updating Legend applications

[EKS deployment](https://github.com/finos/legend-integration-juju/blob/main/docs/deploy/aws-eks.md):

- Prerequisites
- Create and setup an AWS cluster
- Set up Ingress
- Install and Bootstrap Juju
- Create a Model
- Deploy the Legend Bundle
- Configure a hostname for FINOS Legend
- TLS Configuration
- gitlab.com Application setup
- Accessing the Legend Studio dashboard
- Destroy setup
- Alternative methods for accessing Legend Studio dashboard

In a Kubernetes cluster of your choice in which you have bootstrapped a Juju Controller,
you can deploy the bundle by running the following command:
```bash
# Deploy the bundle:
juju deploy finos-legend-bundle --trust --channel=edge
```

The above command will deploy the latest application bundle published.
You can deploy a specific version based on a [FINOS Legend release](https://github.com/finos/legend)
by its year and month (newer than 2022.04.01):

```bash
juju deploy finos-legend-bundle --trust --channel=2022-04/edge
```

The above should yield a model containing all the Legend apps in either
`blocked` or `waiting` status, and require GitLab configuration to proceed.

## Automatic FINOS Legend image updates

This repository has a [Github action](.github/workflows/publish_images.yaml) configured to check if any new [FINOS Legend releases](https://github.com/finos/legend) have been published. If so, the Github action will pull the FINOS Legend Engine, SDLC, and Studio images defined in the release's ``manifest.josn`` file, pull them, upload them into Charmhub, and release the Legend Charms with those image revisions. For more information on the Github action and how it se set up, see [here](docs/CharmhubPublishing.md).

## Contributing

Visit Legend [Contribution Guide](https://github.com/finos/legend/blob/master/CONTRIBUTING.md) to learn how to contribute to Legend.

## License

Copyright (c) 2021-present, Canonical

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)
