import asyncio
import gc
import pytest
import sys
import time
import uuid
from docker import from_env as docker_from_env
import socket
import aiocouchdb


@pytest.fixture(scope='session')
def unused_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope='session')
def loop(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(None)

    yield loop

    if not loop._closed:
        loop.call_soon(loop.stop)
        loop.run_forever()
        loop.close()
    gc.collect()
    asyncio.set_event_loop(None)


@pytest.fixture(scope='session')
def session_id():
    """Unique session identifier, random string."""
    return str(uuid.uuid4())


@pytest.fixture(scope='session')
def docker():
    client = docker_from_env(version='auto')
    return client


@pytest.fixture(scope='session')
def couchdb_server(docker, session_id, loop, request):

    image = 'couchdb:{}'.format('latest')

    if sys.platform.startswith('darwin'):
        port = unused_port()
    else:
        port = None

    container = docker.containers.run(
        image=image,
        detach=True,
        name='couchdb-test-server-{}-{}'.format('latest', session_id),
        ports={
            '5984/tcp': port,
        },
        environment={
            'http.host': '0.0.0.0',
            'transport.host': '127.0.0.1',
        },
    )

    if sys.platform.startswith('darwin'):
        host = '0.0.0.0'
    else:
        inspection = docker.api.inspect_container(container.id)
        host = inspection['NetworkSettings']['IPAddress']
        port = 5984

    delay = 0.1
    for i in range(20):
        try:
            server = aiocouchdb.Server("http://{}:{}".format(host, port))
            loop.run_until_complete(server.all_dbs())
            break
        except Exception as e:
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail("Cannot start couchdb server")

    yield {'host': host,
           'port': port,
           'container': container}

    container.kill(signal=9)
    container.remove(force=True)


@pytest.fixture
def couchdb_params(couchdb_server):
    return dict(host=couchdb_server['host'],
                port=couchdb_server['port'])


@pytest.fixture
def couch_db(loop, couchdb_params):

    server = aiocouchdb.Server("http://{}:{}"
                               .format(
                                    couchdb_params['host'],
                                    couchdb_params['port']))

    db = 'test_db'
    return server[db]
