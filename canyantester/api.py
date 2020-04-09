import json
import re
import requests
import sys
import socket

from dotty_dict import dotty  # type: ignore
from uuid import uuid4


RE_VARIABLE = re.compile(r'\{([^}\.]+)\.([^}]+)\}').search


def api_client(
    apiurl: str, config: dict, stored_responses: dict, verbose: bool = False
):
    uri = config.get('uri', '/')
    method = config.get('method', 'POST')
    payload = config.get('payload', None)
    expected_response = config.get('expected_response', None)
    stored_responses['random'] = {'uuid4': uuid4()}
    ipaddr = socket.gethostbyname(socket.gethostname())
    stored_responses['ipaddr'] = {'ip': ipaddr}

    variable_match = RE_VARIABLE(uri)
    if variable_match is not None:
        stored_response = dotty(stored_responses[variable_match.group(1)])
        uri = uri.replace(
            variable_match.group(0), str(stored_response[variable_match.group(2)])
        )

    if payload:
        for k, v in payload.items():
            if not isinstance(v, str):
                continue
            variable_match = RE_VARIABLE(v)
            if variable_match is None:
                continue
            stored_response = dotty(stored_responses[variable_match.group(1)])
            payload[k] = v.replace(
                variable_match.group(0), str(stored_response[variable_match.group(2)])
            )
    if method == 'POST':
        response = requests.post("%s%s" % (apiurl, uri), json=payload)
        if response.status_code != 200:
            print(response)
            sys.exit(1)
        data = json.loads(response.text)
        if expected_response:
            print('Comparing results...')
            if data != json.loads(expected_response):
                print('NO Match! exiting...')
                print(data)
                sys.exit(1)
            else:
                print('OK')
                if verbose:
                    print('Response: ')
                    print(data)
                return data
        elif isinstance(data, dict):
            return data
        else:
            return None
    elif method == 'DELETE':
        response = requests.delete("%s%s" % (apiurl, uri))
        if response.status_code != 200:
            print(response)
            sys.exit(1)
        if verbose:
            data = json.loads(response.text)
            print('Response: ')
            print(data)
        return response.status_code == 200
