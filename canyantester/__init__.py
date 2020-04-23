import click
import os
import random
import requests
import shutil
import signal
import tempfile
import threading
import time

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
    click.echo('Version 1.2.0')
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
@click.option("--verbose", is_flag=True, default=False, hidden=False)
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
    verbose=False,
):
    """
    Test coordinator and runner, it allows to run real-world scenarios and stress tests
    coordinating multiple sipp instances.
    """
    try:
        run_tester(
            config=config,
            target=target,
            executable=executable,
            directory=directory,
            seed=seed,
            apiurl=apiurl,
            cache_accounts=cache_accounts,
            no_setup=no_setup,
            no_teardown=no_teardown,
            verbose=verbose,
            echo=click.echo,
        )
    except RuntimeError as e:
        raise click.Abort(str(e))


def run_tester(
    config,
    target='sbc:5060',
    executable='sipp',
    directory=None,
    seed=None,
    apiurl=None,
    cache_accounts=None,
    no_setup=False,
    no_teardown=False,
    verbose=False,
    echo=print,
):
    if seed is None:
        seed = generate_random_seed()

    remove_directory_when_done = False
    if directory is None:
        directory = tempfile.mkdtemp()
        remove_directory_when_done = True

    echo("Setting the random seed: %s" % seed)
    random.seed(seed)

    echo("Using temporary directory: %s" % directory)
    echo("Using executable: %s" % executable)
    echo("Target: %s" % target)

    if isinstance(config, str):
        config = open(config, 'rb')

    config_data = load(config, Loader=Loader)
    basedir = config_data.setdefault('basedir', os.path.dirname(config.name))
    stored_responses = {}

    setup = config_data.get('setup', None)
    if not no_setup and setup is not None:
        for i, setup_config in enumerate(setup):
            if setup_config.get('type', 'api') == 'api':
                store_response = setup_config.get('store_response', None)
                response = APIcall(apiurl, setup_config, stored_responses, verbose)
                if store_response:
                    stored_responses[store_response] = response
    else:
        echo("Skipping setup...")

    def _do_check():
        do_check(config_data, apiurl, stored_responses, verbose, echo=echo)

    def _do_teardown():
        do_teardown(
            config_data, no_teardown, apiurl, stored_responses, verbose, echo=echo
        )

    signal.signal(signal.SIGINT, _do_teardown)

    try:
        workers = config_data.get('workers')
        if workers is None:
            echo("No worker has been defined, quit!")
            raise RuntimeError()

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
                        log=echo,
                        stored_responses=stored_responses,
                        verbose=verbose,
                    )
                    tester.setup()
                    testers.append(tester)
                elif worker_config.get('type', None) == 'kamailio_xhttp':
                    thread = threading.Thread(
                        target=kamailioXHTTP, args=(worker_config, verbose)
                    )
                    other_testers.append(thread)

        echo("\nStarting workers:")
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

        echo("\nWorkers' results:")
        error = False
        for tester in testers:
            tester.debug()
            exit_status = tester.get_exit_status()
            if exit_status != 0:
                error = True
            tester.teardown()

        if error:
            raise RuntimeError("\nError detected, aborted!")
        else:
            if remove_directory_when_done:
                shutil.rmtree(directory)
            echo("\nDone!")
    finally:
        _do_check()
        _do_teardown()


def do_delay(config):
    delay = config.get('delay', 0)
    if delay:
        time.sleep(delay)


def APIcall(apiurl, config, stored_responses, verbose, echo=print):
    return api_client(
        apiurl=apiurl,
        config=config,
        stored_responses=stored_responses,
        verbose=verbose,
        echo=echo,
    )


def kamailioXHTTP(config, verbose, echo=print):
    do_delay(config)
    if config.get('method', "POST") == 'POST':
        uri = config.get('uri', "")
        payload = config.get('payload', {})
        response = requests.post(uri, json=payload)
        echo("HTTP response code: %d" % response.status_code)
        if response.status_code != 200:
            echo("Payload: %s" % payload)
            echo("Response: %s" % response.text)
            raise RuntimeError()
        if verbose:
            echo("Payload: %s" % payload)
            echo("Response: %s" % response.text)


def do_check(config_data, apiurl, stored_responses, verbose, echo=print):
    check = config_data.get('check', None)
    if check is not None:
        echo("Starting check process...")
        for _, check_config in enumerate(check):
            do_delay(check_config)
            if check_config.get('type', 'api') == 'api':
                store_response = check_config.get('store_response', None)
                response = APIcall(
                    apiurl, check_config, stored_responses, verbose, echo=echo
                )
                if store_response:
                    stored_responses[store_response] = response


def do_teardown(
    config_data, no_teardown, apiurl, stored_responses, verbose, echo=print
):
    echo("Starting teardown process...")
    teardown = config_data.get('teardown', None)
    if not no_teardown and teardown is not None:
        for _, teardown_config in enumerate(teardown):
            if teardown_config.get('type', 'api') == 'api':
                store_response = teardown_config.get('store_response', None)
                response = APIcall(apiurl, teardown_config, stored_responses, verbose)
                if store_response:
                    stored_responses[store_response] = response
            elif teardown_config.get('type', None) == 'kamailio_xhttp':
                kamailioXHTTP(teardown_config, verbose)
                time.sleep(5)

    else:
        echo("Skipping teardown procedure...")
