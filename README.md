[![Build Status](https://gitlab.com/canyan/canyan-tester/badges/master/pipeline.svg)](https://gitlab.com/canyan/canyan-tester/pipelines) [![codecov](https://codecov.io/gh/canyanio/canyan-tester/branch/master/graph/badge.svg)](https://codecov.io/gh/canyanio/canyan-tester) [![Docker pulls](https://img.shields.io/docker/pulls/canyan/canyan-tester.svg?maxAge=3600)](https://hub.docker.com/repository/docker/canyan/canyan-tester)

# Canyan Testing tool

Canyan Rating is an open source real-time highly scalable rating system. It is composed of an Agent Service, an API, and a Rating Engine.

The rating system is a critical component in any business, especially when real-time features are a strict requirement to ensure business continuity and congruence of transactions. Any compromise to availability, integrity, and authentication in the billing system makes a huge impact on the services provided.

Canyan aims to address these challenges with a cloud-native scalable solution, easily deployable and easily usable. It has been designed to work atomically ensuring the system status is always consistent, reproducible and coherent. Asynchronous processing of no real-time, consolidation events, prioritization, and time-boxed tasks provide the basics to ensure lightning-fast transaction processing without compromises.

Ease of use is addressed with comprehensive documentation, examples and high-quality software (see the test coverage badge).

Canyan Rating is designed as a microservice architecture and comprises [several repositories](https://github.com/canyanio). Its components are stateless and easily deployable via containers on-premises or in the cloud. 

This repository contains the Canyan coordinator and testing tool.

![Canyan logo](https://canyanio.github.io/rating-integration/canyan-logo.png) 


## Getting started

To start using Canyan Rating, we recommend that you begin with the Getting started
section in [the Canyan Rating documentation](https://canyanio.github.io/rating-integration/).


## Contributing

We welcome and ask for your contribution. If you would like to contribute to Canyan Rating, please read our guide on how to best get started [contributing code or documentation](https://canyanio.github.io/rating-integration/contributing/).


## License

Canyan is licensed under the GNU General Public License version 3. See
[LICENSE](https://canyanio.github.io/rating-integration/license/) for the full license text.


## Security disclosure

We take Canyan's security and our users trust very seriously.
If you believe you have found a security issue in Canyan, please responsibly
disclose by contacting us at [security@canyan.io](mailto:security@canyan.io).


## Running

Enter a Python 3 virtualenv and run the setup:

```
$ make setup
```

You can now run the test runner:

```
$ canyantester -t 1.2.3.4 -a http://api:8000 -e sipp sample.yaml
```

Where:

* **-t** is the target IP address
* **-a** is the address of the API server
* **-e** is the executable to run, defaults to `sipp`
* **sample.yaml** is the path to the canyantester configuration file


## Configuration file

`canyantester` accepts a YAML configuration file with the following root keys:

- setup
- teardown
- workers

### setup
Contain a list of actions to perform before the real testing. The parameters are the following:
- **type**: for now only `api` is implemented which makes a REST API call.

`api` supports the following configuration parameters:
* **uri**: the endpoint of the API where to make the request
* **method**: the http method to be used (defaults to `POST`)
* **store_response**: The name of the key for the `stored_responses` array used in other API calls for populating variables dependant of previous requests
* **payload**: the json payload to be sent (defaults to empty object)

#### Example using stored_responses
If you make an API call and use `store_response` value as `tenant` then in another API call you can use in the payload the value returned from the previous call like this:
```tenant_id: "{tenant.id}"```

### workers
Contains the list of workers to be created to perform the tests. 
There are two type of workers:
* sipp
* kamailio_xhttp

`sipp` supports the following configuration parameters:

* **number**: the number of instances to run (defaults to `1`)
* **repeat**: the number of times this worker should run (defaults to `1`)
* **timeout**: maximum number of seconds the worker can run before being killed, defaults to `None` (no timeout is enforced)
* **scenario**: path to the XML sipp scenario to run relative to the YAML configuration file
* **delay**: number of ms of delay before running the workers (defaults to `0`)
* **call_limit**: maximum number of concurrent active calls (`-l` parameter of sipp), defaults to `1`
* **call_number**: maximum number of calls (`-m` parameter of sipp) (defaults to `1`)
* **call_rate**: call rate increment (`-r` parameter of sipp) (defaults to `1`)
* **call\_rate\_period**: call rate period in ms (`-rp` parameter of sipp) (/(defaults to `1000`)
* **values**: key/value map of numerical or string values to be replaced in the XML tempalte.

The parameters which accept numerical values have support for random values expressed as follows:
```
delay:
  min: 1000
  max: 2000
```

Random values are calculated based on the random machine seed number printed by `canyantester` and configurabile through the `-s` option to make random tests reproducibles.


`kamailio_xhttp` supports the following configuration parameters:
* **uri**: the URI of the kamailio node and path where to send the request
* **delay**: number of seconds of delay before running the workers (defaults to `0`)
* **method**: the http method to be used (defaults to `POST`)
* **payload**: the json payload to be sent (defaults to empty object)


### check
This section contains a list of actions to perform for checking the correct data insertion during the workers process.
Useful for checking CDRs insertion and data consistency.
It implements only the `api` method.

The `api` type is the same as for `setup` except for the added `expected_response` which compares the API call response to the element specified in `expected_response`.

It also implements a `delay` in secods, useful for delays in data consolidation.


### teardown
Contain a list of actions to perform after the SIP tests.
It implements two methods:
* api
* kamailio_xhttp

The `api` type is the same as for `setup`. 
`kamailio_xhttp` is the same as for the `workers` but it's used without a delay and without threading.


## Connect with us

* Follow us on [Twitter](https://twitter.com/canyan_io). Please
  feel free to tweet us questions.
* Connect with us on [LinkedIN](https://www.linkedin.com/company/canyan/).
* Join us on [Slack](http://slack.canyan.io)
* Fork us on [Github](https://github.com/canyanio)
* Email us at [info@canyan.io](mailto:info@canyan.io)
