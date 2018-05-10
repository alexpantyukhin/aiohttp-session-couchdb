from aiohttp_session import AbstractStorage, Session
import uuid

__version__ = '0.0.1'


class CouchDBStorage(AbstractStorage):
    def __init__(self, db, *, cookie_name="AIOHTTP_SESSION",
                 domain=None, max_age=None, path='/',
                 secure=None, httponly=True,
                 key_factory=lambda: uuid.uuid4().hex,
                 encoder=lambda x: x, decoder=lambda x: x):
        super().__init__(cookie_name=cookie_name, domain=domain,
                         max_age=max_age, path=path, secure=secure,
                         httponly=httponly,
                         encoder=encoder, decoder=decoder)

        self._db = db
        self._key_factory = key_factory

    async def load_session(self, request):
        cookie = self.load_cookie(request)
        if cookie is None:
            return Session(None, data=None, new=True, max_age=self.max_age)
        else:
            key = str(cookie)
            stored_key = (self.cookie_name + '_' + key).encode('utf-8')
            data_row = await self._db.doc(stored_key)
            if not data_row.exists():
                return Session(None, data=None,
                               new=True, max_age=self.max_age)

            try:
                data = self._decoder(data_row['data'])
            except ValueError:
                data = None
            return Session(key, data=data, new=False, max_age=self.max_age)

    async def save_session(self, request, response, session):
        key = session.identity
        if key is None:
            key = self._key_factory()
            self.save_cookie(response, key,
                             max_age=session.max_age)
        else:
            if session.empty:
                self.save_cookie(response, '',
                                 max_age=session.max_age)
            else:
                key = str(key)
                self.save_cookie(response, key,
                                 max_age=session.max_age)

        data = self._encoder(self._get_session_data(session))
        max_age = session.max_age
        expire = max_age if max_age is not None else 0
        stored_key = (self.cookie_name + '_' + key).encode('utf-8')
        await self._db.update(
                              {
                                {
                                  '_id': stored_key,
                                  'data': data,
                                  'expire': expire
                                }
                              })
