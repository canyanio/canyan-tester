import os
import re
import subprocess
import time

from dotty_dict import dotty  # type: ignore

from .defaults import TEMPLATE_XML as DEFAULT_TEMPLATE_XML
from .utils import get_int_from_config
from .worker import Worker


class SippWorker(Worker):

    TEMPLATE_XML = DEFAULT_TEMPLATE_XML
    RE_VARIABLE = re.compile(r'\{([^}\.]+)\.([^}]+)\}').search

    def __init__(
        self,
        worker_id,
        config,
        target=None,
        executable=None,
        directory=None,
        basedir=None,
        log=print,
        stored_responses=None,
    ):
        super(SippWorker, self).__init__()
        self._worker_id = worker_id
        self._config = config
        self._directory = directory
        self._basedir = basedir
        self._log = log
        self._exception = None
        self._target = target
        self._executable = executable
        self._stored_responses = stored_responses
        self._values = self._config.get('values', {})
        self._filename_xml = os.path.join(
            self._directory, 'sipp-%s.xml' % self._worker_id
        )
        self._delay = get_int_from_config(self._config, 'delay', 0)
        self._output = None
        self._args = []

    def setup(self):
        for k, v in self._values.items():
            if not isinstance(v, str):
                continue
            variable_match = self.RE_VARIABLE(v)
            if variable_match is None:
                continue
            stored_response = dotty(self._stored_responses[variable_match.group(1)])
            self._values[k] = v.replace(
                variable_match.group(0), str(stored_response[variable_match.group(2)])
            )
        values = {'basedir': self._basedir, 'target': self._target}
        for key in self._values.keys():
            if isinstance(self._values[key], str):
                values[key] = self._values[key]
            elif isinstance(self._values[key], (list, tuple)):
                worker_positional_id = int(self._worker_id.split('_', 1)[1])
                values[key] = self._values[key][
                    worker_positional_id % len(self._values[key])
                ]
            else:
                values[key] = get_int_from_config(self._values, key, None)
        if self._config.get('scenario'):
            template_xml = (
                open(os.path.join(self._basedir, self._config.get('scenario'))).read()
                % values
            )
        else:
            template_xml = self.TEMPLATE_XML % values
        with open(self._filename_xml, 'wb') as f:
            f.write(template_xml.encode('utf-8'))
        self._args = [
            self._executable,
            self._target,
            '-sf',
            self._filename_xml,
            '-l',
            str(get_int_from_config(self._config, 'call_limit', 1)),
            '-r',
            str(get_int_from_config(self._config, 'call_rate', 1)),
            '-rp',
            str(get_int_from_config(self._config, 'call_rate_period', 1000)),
            '-m',
            str(get_int_from_config(self._config, 'call_number', 1)),
        ]
        extra_args = self._config.get('extra_args')
        if isinstance(extra_args, (tuple, list)):
            self._args.extend(extra_args)
        elif isinstance(extra_args, str):
            self._args.extend(extra_args.split())
        self._output = None

    def runner(self):
        if os.path.exists(self._filename_xml.replace('.xml', '.log')):
            os.unlink(self._filename_xml.replace('.xml', '.log'))
        exit_codes = []
        with open(self._filename_xml.replace('.xml', '.log'), 'ab') as log:
            if self._delay:
                time.sleep(self._delay / 1000.0)
            for _ in range(get_int_from_config(self._config, 'repeat', 1)):
                self._log(
                    "[%s] %s (delay = %s)"
                    % (self._worker_id, " ".join(self._args), self._delay)
                )
                try:
                    p = subprocess.run(
                        args=self._args,
                        check=True,
                        stdout=log,
                        stderr=log,
                        timeout=self._config.get('timeout', None),
                    )
                except subprocess.CalledProcessError as e:
                    exit_codes.append(e.returncode)
                except subprocess.TimeoutExpired:
                    exit_codes.append(-1)
                else:
                    exit_codes.append(p.returncode)
        self._exit_codes = exit_codes

    def debug(self):
        non_zero_exit_codes = list(filter(lambda x: x != 0, self._exit_codes))
        self._exit_status = (
            non_zero_exit_codes[0]
            if len(non_zero_exit_codes) > self._config.get('max_errors', 0)
            else 0
        )
        self._log(
            "[%s] runs = %s, errors = %s, exit codes = %s, input = %s, output = %s"
            % (
                self._worker_id,
                len(self._exit_codes),
                len(non_zero_exit_codes),
                ', '.join(map(str, self._exit_codes)),
                self._filename_xml,
                self._filename_xml.replace('.xml', '.log'),
            )
        )
