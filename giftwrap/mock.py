# caveat:  right now macking of an exchange only works if there are no retries on the exchange
from grabbag.property import is_cached


class MockMixin(object):
    @classmethod
    def mockify(kls, result=None, response=None, **kwargs):
        kls._old_init = kls.__init__
        kls.__init__ = kls._mockify_init
        kls._mock_result = result
        kls._mock_response = response
        if len(kwargs): kls._mock_response = MockResponse(**kwargs)

    @classmethod
    def unmockify(kls):
        if kls.__init__ == kls._mockify_init:
            kls.__init__ = kls._old_init

    def _mockify_init(self, *args, **kwargs):
        mock_response = kwargs.pop('response',getattr(self.__class__,'_mock_response',None))
        mock_result = kwargs.pop('result',getattr(self.__class__,'_mock_result',None))
        self._old_init(*args, **kwargs)
        if mock_response: self.response = mock_response
        if mock_result: self.result = mock_result


class Mocker(object):
    def __init__(self, exchange_kls, result=None, response=None, **kwargs):
        self.exchange_kls = exchange_kls
        self.result = None
        self.response = None
        if len(kwargs): self.response = MockResponse(**kwargs)

    def mockify(self):
        self.exchange_kls.__bases__ += (MockMixin,)
        self.exchange_kls.mockify(result=self.result, response=self.response)
        return self

    def unmockify(self):
        self.exchange_kls.unmockify()
        bases = list(self.exchange_kls.__bases__)
        bases.remove(MockMixin)
        self.exchange_kls.__bases__ = tuple(bases)
        return self

    def __enter__(self): return self.mockify()
    def __exit__(self, *args): self.unmockify(); return None

mocker = Mocker


class MockResponse(object):
    def __init__(self, text=None, err=None, status_code=None):
        super(MockResponse, self).__init__()
        self.text = text
        self.err = err
        self.status_code = status_code or 200

    def raise_for_status(self):
        if self.err: raise self.err


