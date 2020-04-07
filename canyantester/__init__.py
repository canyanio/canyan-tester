import os
import signal
import sys
import click
import random
import requests
import shutil
import time
import tempfile
import threading

from yaml import load


try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader  # type: ignore

from .utils import generate_random_seed, get_int_from_config
from .api import api_client
from .sipp import SippWorker


def print_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Version 1.1.0')
    ctx.exit()


@click.command()
@click.option(
    '--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True
)
@click.argument('config', type=click.File('rb'))
@click.option(
    '-t',
    '--target',
    default='sbc:5060',
    type=click.STRING,
    required=False,
    help='IP address of the SIP server to use as target',
)
@click.option(
    '-e',
    '--executable',
    type=click.STRING,
    default="sipp",
    help='Command to exec for running sipp',
)
@click.option(
    '-d',
    '--directory',
    type=click.Path(exists=True),
    default=None,
    help='Working directory, if not specified a temporary directory is created.',
)
@click.option(
    '-s',
    '--seed',
    type=click.INT,
    default=None,
    help='Initialize the Python random machine with this seed value.',
)
@click.option('-a', '--apiurl', default='http://api:8000', show_default=True)
@click.option(
    "--no-setup",
    is_flag=True,
    default=False,
    help="Skip setup step in yaml file",
    hidden=False,
)
@click.option(
    "--no-teardown",
    is_flag=True,
    default=False,
    help="Skip teardown step in yaml file",
    hidden=False,
)
def canyantester(
    config,
    target,
    executable,
    directory,
    seed,
    apiurl=None,
    cache_accounts=None,
    no_setup=False,
    no_teardown=False,
):
    """
    Test coordinator and runner, it allows to run real-world scenarios and stress tests
    coordinating multiple sipp instances.
    """
    if apiurl is None:
        click.echo("No API URI has been defined, quit!")
        raise click.Abort()

    if seed is None:
        seed = generate_random_seed()

    remove_directory_when_done = False
    if directory is None:
        directory = tempfile.mkdtemp()
        remove_directory_when_done = True

    click.echo("Setting the random seed: %s" % seed)
    random.seed(seed)

    click.echo("Using temporary directory: %s" % directory)
    click.echo("Using executable: %s" % executable)
    click.echo("Target: %s" % target)

    config_data = load(config, Loader=Loader)
    basedir = config_data.setdefault('basedir', os.path.dirname(config.name))
    stored_responses = {}

    setup = config_data.get('setup', None)
    if not no_setup and setup is not None:
        for i, setup_config in enumerate(setup):
            if setup_config.get('type', 'api') == 'api':
                store_response = setup_config.get('store_response', None)
                response = APIcall(apiurl, setup_config, stored_responses)
                if store_response:
                    stored_responses[store_response] = response
    else:
        click.echo("Skipping setup...")

    def _do_check():
        do_check(config_data, apiurl, stored_responses)

    def _do_teardown():
        do_teardown(config_data, no_teardown, apiurl, stored_responses)

    signal.signal(signal.SIGINT, _do_teardown)

    try:
        workers = config_data.get('workers')
        if workers is None:
            click.echo("No worker has been defined, quit!")
            raise click.Abort()

        testers = []
        other_testers = []
        for i, worker_config in enumerate(workers):
            number_of_workers = get_int_from_config(worker_config, 'number', 1)

            for j in range(number_of_workers):
                if worker_config.get('type', 'sipp') == 'sipp':
                    tester = SippWorker(
                        worker_id="%06d_%06d" % (i, j),
                        config=worker_config,
                        target=target,
                        executable=executable,
                        directory=directory,
                        basedir=basedir,
                        log=click.echo,
                        stored_responses=stored_responses,
                    )
                    tester.setup()
                    testers.append(tester)
                elif worker_config.get('type', None) == 'kamailio_xhttp':
                    thread = threading.Thread(
                        target=kamailioXHTTP, args=(worker_config,)
                    )
                    other_testers.append(thread)

        click.echo("\nStarting workers:")
        threads = []
        for tester in testers:
            t = threading.Thread(target=tester)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for t in other_testers:
            t.start()

        for t in other_testers:
            t.join()

        click.echo("\nWorkers' results:")
        error = False
        for tester in testers:
            tester.debug()
            exit_status = tester.get_exit_status()
            if exit_status != 0:
                error = True
            tester.teardown()

        if error:
            raise click.Abort("\nError detected, aborted!")
        else:
            if remove_directory_when_done:
                shutil.rmtree(directory)
            click.echo("\nDone!")
    finally:
        _do_check()
        _do_teardown()


def APIcall(apiurl, config, stored_responses):
    return api_client(apiurl=apiurl, config=config, stored_responses=stored_responses)


def kamailioXHTTP(config):
    delay = config.get('delay', 0)
    if delay:
        time.sleep(delay)
    if config.get('method', "POST") == 'POST':
        uri = config.get('uri', "")
        payload = config.get('payload', {})
        response = requests.post(uri, json=payload)
        if response.status_code != 200:
            print(response.text)
            sys.exit(1)


def do_check(config_data, apiurl, stored_responses):
    check = config_data.get('check', None)
    if check is not None:
        click.echo("Starting check process...")
        for _, check_config in enumerate(check):
            if check_config.get('type', 'api') == 'api':
                store_response = check_config.get('store_response', None)
                response = APIcall(apiurl, check_config, stored_responses)
                if store_response:
                    stored_responses[store_response] = response


def do_teardown(config_data, no_teardown, apiurl, stored_responses):
    click.echo("Starting teardown process...")
    teardown = config_data.get('teardown', None)
    if not no_teardown and teardown is not None:
        for _, teardown_config in enumerate(teardown):
            if teardown_config.get('type', 'api') == 'api':
                store_response = teardown_config.get('store_response', None)
                response = APIcall(apiurl, teardown_config, stored_responses)
                if store_response:
                    stored_responses[store_response] = response
            elif teardown_config.get('type', None) == 'kamailio_xhttp':
                kamailioXHTTP(teardown_config)
                time.sleep(5)

    else:
        click.echo("Skipping teardown procedure...")
