aiohttp_session_couchdb
===============
.. image:: https://travis-ci.org/alexpantyukhin/aiohttp-session-mongo.svg?branch=master
    :target: https://travis-ci.org/alexpantyukhin/aiohttp-session-mongo
.. image:: https://codecov.io/github/alexpantyukhin/aiohttp-session-mongo/coverage.svg?branch=master
    :target: https://codecov.io/github/alexpantyukhin/aiohttp-session-mongo

The library provides couchdb sessions store for `aiohttp.web`__.

.. _aiohttp_web: https://aiohttp.readthedocs.io/en/latest/web.html

__ aiohttp_web_

Usage
-----

A trivial usage example:

.. code:: python

    import time
    import base64
    from cryptography import fernet
    from aiohttp import web
    from aiohttp_session import setup, get_session
    from aiohttp_session_couchdb import CouchDBStorage


    async def handler(request):
        session = await get_session(request)
        last_visit = session['last_visit'] if 'last_visit' in session else None
        session['last_visit'] = time.time()
        text = 'Last visited: {}'.format(last_visit)
        return web.Response(text=text)


    def make_app():
        app = web.Application()

        setup(app, CouchDBStorage(couch_db,
                                max_age=max_age,
                                key_factory=lambda: uuid.uuid4().hex)
                                )

        app.router.add_get('/', handler)
        return app


    web.run_app(make_app())

