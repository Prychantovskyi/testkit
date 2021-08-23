# Neo4j drivers integration/conformance tests

## Running all test suites within docker containers

Requirements on host:
  * Python >= 3.7
  * Docker >= 19.03

Environment variables:
  * `TEST_DRIVER_NAME`  
    Set to the name of the driver in lowercase. This is currently used for
    adjusting the set of skipped tests and the expected outcome of some tests.  
    Currently known drivers are `dotnet`, `go`, `java`, `javascript`, and 
    `python`.
  * `TEST_DRIVER_REPO`  
    Path to driver repository
  * `TEST_BRANCH`  
    Name of testkit branch. When running locally, this defaults to 'local'.
  * `TEST_BUILD_CACHE_ENABLED`  
    Set to `true` to enable build cache persistence via Docker Volumes for 
    supported build systems. Only Maven is supported at the moment and it stores
    its data in `testkit-m2` volume.
  * `TEST_RUN_ALL_TESTS`  
    Set to `true` to make sure all tests are run even if some fail. Testkit will
    still exit with a non-zero exit code if any test failed.
  * `TEST_DOCKER_USER`  
    If specified, all docker containers are run as the specified user. Value is
    directly passed to docker, if present. See `docker run -u` for more details.
  * `TEST_DOCKER_RMI`  
    Set to `true` to make testkit remove all tags it created/overwrote after
    they are not needed anymore. If said tag is the only tag of that image,
    docker will remove the image and all intermediate parent images.
  * `ARTIFACTS_DIR`  
    Name of the directory into which logs and similar debug output is placed.

```console
export TEST_DRIVER_NAME=go
export TEST_DRIVER_REPO=/home/clones/neo4j/neo4j-go-driver
python3 main.py
```

## Local development


### Configuration variables

Environment variables used to control how tests are executed:
  * `TEST_NEO4J_HOST`  
    Host or ip where Neo4j server is running.
    Should normally be set to localhost.
  * `TEST_NEO4J_USER`  
    Username used to connect to Neo4j server.
    Defaults to 'neo4j'
  * `TEST_NEO4J_PASS`  
    Password used to connect to Neo4j server.
    Defaults to 'pass'
  * `TEST_NEO4J_PORT`  
    Defaults to Bolt port 7687, normally not needed.
  * `TEST_BACKEND_HOST`  
    Defaults to localhost, normally not needed.
  * `TEST_BACKEND_PORT`  
    Defaults to 9876, normally not needed.
All of these variables are normally set by the main runner.

### Running a subset of tests or configurations

When running testkit locally from the command line you can specify which test 
types you want to run. In addition the Neo4j version and edition against which 
the tests should be executed can be configured  via the `--configs` parameter:


```console
python3 main.py --tests TESTKIT_TESTS UNIT_TESTS --configs 4.0-community 4.1-enterprise
```

To see a list of available test types and configurations use:

```console
python3 main.py --help
```

The `--tests` parameter refers to a prefined set subset of all available tests.

### Running tests against a specific backend

When developing a driver or providing a testkit backend for that specific driver
it is useful to be able to run testkit against a locally running backend. That
backend will be most likely started from your IDE and making use of a non-packaged
version of your driver, thus avoiding the step of fully building both the specific
driver and its backend. Therefore such a setup does not require Docker containers.

Testkit requires some packages to do this, which can be installed via pip:

```console
python3 -m pip install -Ur requirements.txt
```

The backend can run on the same host that runs the testkit tests or on a remote 
machine.

#### Integration tests

To run integration tests you need to:
  * Provide the tests with a running Neo4j instance. This instance can be
    running locally (Jar or Docker) or on a server somewhere (be careful, the
    tests might destroy data).

    Example on how to start latest Neo4j server locally in Docker:
    ```console
    docker run --name neo4j --env NEO4J_AUTH=neo4j/pass -p7687:7687 --rm neo4j:latest
    ```

    For security reasonse there is no default setting for the Neo4j host that
    the tests are running against, as the tests will modify the databases contents.
    The environment variable `TEST_NEO4J_HOST` needs to be set to the correct location.
    In the example above that would be `localhost`.

  * Start the drivers testkit backend.
    testkit tries to connect to the backend on port 9876 on localhost by default.
    If the backend is running on another host or port the environment variables 
    `TEST_BACKEND_HOST` and `TEST_BACKEND_PORT` needs to be set in the
    environment where the tests are invoked.

  * Run the integration tests using standard Python unittest syntax. The 
    integration tests are all prefixed with `tests.neo4j.XXX`, where XXX can be a
    single Python file (without the .py), a class in the single Python file or a
    single test.
    For non-Python people: All tests are stored under `tests`, folder names will
    become package or module names according the above definition.

    To run a single named test using a local Neo4j database:
    ```console
    export TEST_NEO4J_HOST=localhost
    python3 -m unittest tests.neo4j.datatypes.TestDataTypes.test_should_echo_back
    ```
#### Stub tests

Running stub tests locally is simpler than running the integration tests as they
don't need a running Neo4j instance (hence stub tests, using a scripted stub).

  * Start the drivers testkit backend, see above.
  * Run the stub tests same way as the integration tests but they are rooted at
    tests.stub instead of tests.neo4j

#### Orchestrate backend from testkit

Alternatively, it's possible to use the option `--tests RUN_SELECTED_TESTS`
to build the driver backend and run the tested in the `TEST_SELECTOR`
environment variable. This will start all dependencies needed (such as neo4j
or tls servers). It's especially useful during the development of new tests 
when used in combination with `run_all.py` enabling to run one specific test
against all known drivers.
* The command-line param `--run-only-selected <test_selector>` is a shortcut
  for setting the `TEST_SELECTOR` environment variable and running the 
  command with `--tests RUN_SELECTED_TESTS`.


## Running all test suites for all known drivers within docker containers 

This test runner will clone and run the tests for each known driver repository. 

Requirements on host:
  * Python >= 3.7
  * Docker >= 19.03

Environment variables:
  * `TEST_DRIVER_BRANCH`  
    Branch to be tested in all drivers. Default: 4.3
  * `TEST_RUN_ALL_DRIVERS`  
    Set to `true` to make sure all drivers are tested even if some fail. The
    program will still exit with a non-zero exit code if any test failed.

```console
python3 run_all.py
```

This test runs the `main.py` overriding the enviroment variables 
`TEST_DRIVER_NAME` and `TEST_DRIVER_REPO` with correct values for each driver. 
The others enviroment variables will be used by `main.py` as usual.

## Running stress test suite against a running Neo4j instance

This test runner will build the driver and its testkit backend, setup the 
environment and invoke the driver native stress test suite.

Environment variables:
  * `TEST_NEO4J_URI`  
    Full URI for connecting to running Neo4j instance, for example:
      neo4j+s://somewhere.com:7687
  * `TEST_NEO4J_USER`  
    Username used to connect, defaults to neo4j
  * `TEST_NEO4J_PASS`  
    Password used to connect
