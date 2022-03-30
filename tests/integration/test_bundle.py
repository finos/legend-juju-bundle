#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
import requests
import tenacity
from pytest_operator import plugin as pytest_plugin

logger = logging.getLogger(__name__)

BUNDLE_YAML = "./bundle.yaml"

MONGODB_APP_NAME = "mongodb"
ENGINE_APP_NAME = "legend-engine"
SDLC_APP_NAME = "legend-sdlc"
STUDIO_APP_NAME = "legend-studio"

# TODO: Add STUDIO_APP_NAME to the list below once the following issue has been resolved:
# https://github.com/finos/legend-studio/issues/1028
LEGEND_APPS = [ENGINE_APP_NAME, SDLC_APP_NAME]
LEGEND_APPS_CONFIG = [ENGINE_APP_NAME, SDLC_APP_NAME, STUDIO_APP_NAME]

LEGEND_HOST = "legend-host"
ANOTHER_LEGEND_HOST = "another-legend-host"

APP_PORTS = {
    ENGINE_APP_NAME: 6060,
    SDLC_APP_NAME: 7070,
    STUDIO_APP_NAME: 8080,
}
APP_ROUTES = {
    ENGINE_APP_NAME: "/engine",
    SDLC_APP_NAME: "/api",
    STUDIO_APP_NAME: "/studio",
}

GITLAB_CLIENT_ID = "fake-client-id"
GITLAB_CLIENT_SECRET = "fake-client-secret"


async def cli_deploy_bundle(ops_test, name):
    run_args = [
        "juju",
        "deploy",
        "--trust",
        "--channel=edge",
        "-m",
        ops_test.model_full_name,
        name,
    ]

    retcode, stdout, stderr = await ops_test.run(*run_args)
    assert retcode == 0, "Deploy failed: %s" % (stderr or stdout).strip()
    logger.info(stdout)


# When the Ingress Routes are being established, it takes a few seconds to take effect, which
# is why we should retry the connection a few times.
@tenacity.retry(
    retry=tenacity.retry_if_result(lambda x: x is False),
    stop=tenacity.stop_after_attempt(10),
    wait=tenacity.wait_exponential(multiplier=1, min=5, max=30),
)
def check_legend_connection(app_name, url, headers=None):
    """Tests the connection to the given Legend URL.

    When connecting to the FINOS Legend Applications, it will redirect to gitlab for
    authentication, which will not be a 20X status code. We will receive 302 Found
    instead.

    Returns True if the response status code is 302, False in any other case.
    """
    logger.info("Trying to access %s...", app_name)
    try:
        response = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
        return response.status_code == 302
    except Exception as ex:
        logger.info(ex)

    return False


@pytest.mark.abort_on_fail
async def test_deploy_bundle(ops_test: pytest_plugin.OpsTest):
    """Deploy the current FINOS Legend bundle.

    Assert that the mongodb charm becomes active, since it takes the longest to become active.
    """
    # Deploy the bundle from CLI to avoid the charms getting stuck in the Waiting Status because
    # the image docker.io/jujusolutions/charm-base:kubernetes-kubernetes could not be pulled.
    await cli_deploy_bundle(ops_test, BUNDLE_YAML)

    await ops_test.model.wait_for_idle(apps=[MONGODB_APP_NAME], status="active", timeout=2000)
    assert ops_test.model.applications[MONGODB_APP_NAME].units[0].workload_status == "active"

    # effectively disable the update status from firing
    await ops_test.model.set_config({"update-status-hook-interval": "60m"})


@pytest.mark.abort_on_fail
async def test_config_gitlab(ops_test: pytest_plugin.OpsTest):
    """Set the gitlab.com's application secret ID and name.

    After setting the application secret ID and name, the charms should become active.
    """
    # We need valid information here. These should be passed in through the env variables.
    gitlab_integrator = ops_test.model.applications["gitlab-integrator"]
    await gitlab_integrator.set_config(
        {"gitlab-client-id": GITLAB_CLIENT_ID, "gitlab-client-secret": GITLAB_CLIENT_SECRET}
    )

    # Wait for Legend Studio to become Active.
    await ops_test.model.wait_for_idle(apps=[STUDIO_APP_NAME], status="active", timeout=1000)
    assert ops_test.model.applications[STUDIO_APP_NAME].units[0].workload_status == "active"

    # Assert that the right Callback URIs are being returned by the gitlab-integrator's
    # get-redirect-uris action.
    action = await gitlab_integrator.units[0].run_action("get-redirect-uris")
    action = await action.wait()

    expected_uris = [
        "http://%s/engine/callback" % LEGEND_HOST,
        "http://%s/api/auth/callback" % LEGEND_HOST,
        "http://%s/api/pac4j/login/callback" % LEGEND_HOST,
        "http://%s/studio/log.in/callback" % LEGEND_HOST,
    ]

    assert "completed" == action.data.get("status")
    assert expected_uris == action.data.get("results").get("result", "").split("\n")


@pytest.mark.abort_on_fail
async def test_applications_are_up(ops_test: pytest_plugin.OpsTest):
    """Test the direct FINOS Legend connection.

    The FINOS Legend application services should be accessible through their IP, ports,
    and routes.
    """
    status = await ops_test.model.get_status()

    for app_name in LEGEND_APPS:
        unit_name = "%s/0" % app_name
        address = status["applications"][app_name]["units"][unit_name]["address"]

        url = "http://%s:%s%s" % (address, APP_PORTS[app_name], APP_ROUTES[app_name])
        can_connect = check_legend_connection(app_name, url)

        assert can_connect, "Could not reach %s through its IP." % app_name
        logger.info("Successfully reached %s through its IP.", app_name)


@pytest.mark.abort_on_fail
async def test_nginx_ingress_integration(ops_test: pytest_plugin.OpsTest):
    """Test the FINOS Legend connection through NGINX Ingress.

    The Legend applications have been configured with the legend-host external-hostname by default,
    and they should be accessible through it due to the nginx-ingress-integrator charm.
    """
    # We should now be able to connect to FINOS Legend through it's service-hostname (this bundle
    # sets it to "legend-host"). In this test scenario, we don't have a resolver for it. One could
    # configure the /etc/hosts file to have the line:
    # 127.0.0.1 legend-host
    # Having the line above would resolve the hostname. For the current testing purposes, we
    # can simply connect to 127.0.0.1 and having the hostname as a header. This is the
    # equivalent of:
    # curl --header 'Host: legend-host' http://127.0.0.1

    for app_name in LEGEND_APPS:
        url = "http://127.0.0.1%s" % APP_ROUTES[app_name]
        headers = {"Host": LEGEND_HOST}
        can_connect = check_legend_connection(app_name, url, headers)

        assert can_connect, "Could not reach %s through its service-hostname." % app_name

        logger.info("Successfully reached %s through its service-hostname.", app_name)


@pytest.mark.abort_on_fail
async def test_config_another_hostname(ops_test: pytest_plugin.OpsTest):
    """Set a different hostname for the Legend Applications.

    After setting a different application hostname, the gitlab-integrator get-redirect-uris
    action results should update accordingly, and the Legend Applications should respond to
    the new hostname.
    """
    for app_name in LEGEND_APPS_CONFIG:
        app = ops_test.model.applications[app_name]
        await app.set_config({"external-hostname": ANOTHER_LEGEND_HOST})

    # Wait for the Legend applications to become Active.
    for app_name in LEGEND_APPS_CONFIG:
        await ops_test.model.wait_for_idle(apps=[app_name], status="active", timeout=1000)
        assert ops_test.model.applications[app_name].units[0].workload_status == "active"

    for app_name in LEGEND_APPS:
        url = "http://127.0.0.1%s" % APP_ROUTES[app_name]
        headers = {"Host": ANOTHER_LEGEND_HOST}
        can_connect = check_legend_connection(app_name, url, headers)

        assert can_connect, "Could not reach %s through its new service-hostname." % app_name

        logger.info("Successfully reached %s through its new service-hostname.", app_name)

    gitlab_integrator = ops_test.model.applications["gitlab-integrator"]
    action = await gitlab_integrator.units[0].run_action("get-redirect-uris")
    action = await action.wait()

    expected_uris = [
        "http://%s/engine/callback" % ANOTHER_LEGEND_HOST,
        "http://%s/api/auth/callback" % ANOTHER_LEGEND_HOST,
        "http://%s/api/pac4j/login/callback" % ANOTHER_LEGEND_HOST,
        "http://%s/studio/log.in/callback" % ANOTHER_LEGEND_HOST,
    ]

    assert "completed" == action.data.get("status")
    assert expected_uris == action.data.get("results").get("result", "").split("\n")
