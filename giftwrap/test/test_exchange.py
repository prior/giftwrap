import unittest
from multiprocessing import Process
import requests
import json
import time


from ..exchange import Exchange
from ..config import DefaultConfig
from ..auth import Auth
from ..error import TimeoutError,ResponseError
from grabbag.list import first_not_none
from grabbag.dict import merge


TEST_METHODS = ('GET','POST','PUT','DELETE')
TEST_DATAS = ('','{"json":true}','<html></html>')
TEST_PARAMS = ({'a':'1'},{'a':'z'},{},{'c':'3'})
TEST_HEADERS = ({'a':'1'},{'a':'z'},{},{'c':'3'})

class TestAuth(Auth): pass
class TestExchange(Exchange):
    protocol = 'http'
    domain = 'localhost:8087'
    base_path = '/blah/v1'
    sub_path = 'mirror/create'
    def process_response(self, response): return json.loads(response.content)

class TestExchange2(Exchange): pass


def webserver():
    from bottle import route, run, request, error

    @route('/blah/v1/mirror/:extra', method='GET')
    def get(extra): return mirror(extra)
    @route('/blah/v1/mirror/:extra', method='POST')
    def post(extra): return mirror(extra)
    @route('/blah/v1/mirror/:extra', method='PUT')
    def putextra(extra): return mirror(extra)
    @route('/blah/v1/mirror/:extra', method='DELETE')
    def delete(extra): return mirror(extra)

    @error(404)
    def bad(code): return 'bad'

    @route('/sleep/:ms', method='GET')
    def sleep(ms):
        time.sleep(int(ms)/1000.0)
        return json.dumps( {'sleep': ms} )

    def mirror(extra):
        return json.dumps( dict(
            method = request.method,
            protocol = request.urlparts[0],
            domain = request.urlparts[1],
            path = request.urlparts[2],
            body = request.body.getvalue(),
            params = dict((k,request.query.getall(k)) for k in request.query.keys()),
            headers = dict((k,request.headers.get(k)) for k in request.headers.keys())))
    run(host='localhost', port=8087)



class ExchangeTest(unittest.TestCase):

    @classmethod
    def setUpClass(kls): 
        kls.webserver_process = Process(target=webserver)
        kls.webserver_process.start()
        working = False
        while not working:
            time.sleep(0.02)
            try:
                working = requests.get('http://localhost:8087/blah/v1/mirror/whatever').status_code == 200
            except: pass

    @classmethod
    def tearDownClass(kls): 
        kls.webserver_process.terminate()
        kls.webserver_process.join()


    def setUp(self): pass
    def tearDown(self): pass


    def _test_expected_attr(self, attr, possibles, default=None, add_none=True, final_possibles=None):
        final_possibles = list(final_possibles or possibles)
        if add_none: 
            possibles = [None] + list(possibles)
            final_possibles = [None] + list(final_possibles)
        for k,x in zip(possibles,final_possibles):
            for l in (True, False):
                for m,z in zip(possibles,final_possibles):
                    for n,w in zip(possibles, final_possibles):
                        class TestExchangeX(TestExchange2): pass
                        if l:
                            if k is not None: setattr(TestExchangeX, attr, k)
                        else:
                            if k is not None: setattr(TestExchangeX, attr, lambda self: k)
                        auth = Auth()
                        if n is not None: setattr(auth,attr,n)
                        self.assertEquals(default if n is None else n, getattr(auth,attr,None))
                        ex = TestExchangeX(auth, **{attr:m})
                        self.assertEquals(first_not_none( (z,x,w), default), getattr(ex, attr))

    def _test_additive_attr(self, attr, possibles, add_none=True):
        if add_none: 
            possibles = [None] + list(possibles)
        for k in possibles:
            for l in (True,False):
                for m in possibles:
                    for n in possibles:
                        class TestExchangeX(TestExchange): pass
                        auth = Auth()
                        setattr(auth,attr,n)
                        if l:
                            if k is not None: setattr(TestExchangeX, attr, k)
                        else:
                            if k is not None: setattr(TestExchangeX, attr, lambda self: k)
                        ex = TestExchangeX(auth, **{attr:m})
                        self.assertEquals( merge({}, n or {}, k or {}, m or {}), getattr(ex, attr))

    def test_calcs(self): 
        self._test_expected_attr('method', TEST_METHODS, DefaultConfig.method)
        self._test_expected_attr('protocol', ('http','https'), DefaultConfig.protocol)
        self._test_expected_attr('domain', ('app.localhost','app.hubspotqa.com','app.hubspot.com'), add_none=False)
        self._test_expected_attr('base_path', ('/v1/whatever/','/base/path','') , None, final_possibles=('v1/whatever','base/path',None))
        self._test_expected_attr('sub_path', ('/create','','show/'), None, final_possibles=('create',None,'show'))
        self._test_expected_attr('data', TEST_DATAS)
        self._test_expected_attr('timeout', (10,20,30), DefaultConfig.timeout)
        self._test_expected_attr('max_retries', (0,1,2), DefaultConfig.max_retries)
        
        ###TODO: make it possible to use params as they can be used (i.e. multiple values per key -- i.e. MultiDict)
        self._test_additive_attr('params', TEST_PARAMS)
        self._test_additive_attr('headers', TEST_HEADERS)


    def test_timeouts(self):
        self.assertTrue(TestExchange(TestAuth(), timeout=0.5).result)
        with self.assertRaises(TimeoutError):
            self.assertTrue(TestExchange(TestAuth(), timeout=0.00001).result)

    def test_methods(self):
        for method in TEST_METHODS:
            self.assertEquals(method, TestExchange(TestAuth(), method=method).result['method'])
        
    def test_datas(self):
        for data in TEST_DATAS:
            self.assertEquals(data, TestExchange(TestAuth(), data=data).result['body'])

    def test_sub_paths(self):
        for sub_path in ('create','show','list'):
            self.assertEquals("/blah/v1/mirror/%s"%sub_path, TestExchange(TestAuth(), base_path='blah/v1/mirror', sub_path=sub_path).result['path'])

    def test_params(self):
        for params in TEST_PARAMS:
            self.assertEquals(dict((k,[v]) for k,v in params.iteritems()), TestExchange(TestAuth(), params=params).result['params'])

    def test_headers(self):
        for headers in TEST_HEADERS:
            self.assertEquals(dict((k.upper(),v) for k,v in headers.iteritems()), dict((k.upper(),v) for k,v in TestExchange(TestAuth(), headers=headers).result['headers'].iteritems() if k.lower() in headers.keys()))

    def test_max_retries(self):
        for max_retries in (0,1,2):
            try:
                self.assertTrue(TestExchange(TestAuth(), timeout=0.00001, max_retries=max_retries).result)
            except TimeoutError as err:
                self.assertEquals(max_retries+1, len(err.exchange.failures))
                for f in err.exchange.failures:
                    self.assertTrue(isinstance(f, TimeoutError))
                continue
            except:
                self.fail("should not get to here")
            self.fail("should not get to here")

    def test_bulk_exchange(self):
        count = 5
        for async in (True,False):
            exs = [TestExchange(TestAuth(), params={'i':str(i), 'async':str(async)}) for i in xrange(count)]
            for ex,i in zip(Exchange.async_exchange(exs), xrange(count)):
                self.assertEquals([str(i)],ex.result['params']['i'])
                self.assertEquals([str(async)],ex.result['params']['async'])

    def test_different_auth(self):
        class TestAuth1(Auth):
            def params(self): return {'key1':'value1'}
        class TestAuth2(Auth):
            def params(self): return {'key2':'value2'}
        class TestExchange1(Exchange): pass
        class TestExchange2(Exchange): pass
        self.assertEquals({'key1':'value1'},TestExchange1(TestAuth1()).params)
        self.assertEquals({'key2':'value2'},TestExchange1(TestAuth2()).params)



    def test_bad_url(self):
        class TestExchange(Exchange):
            protocol = 'http'
            domain = 'localhost:8087'
            base_path = 'bad'
            ok404 = True
            def process_error(self, error, response): 
                if response is not None:
                    if response.status_code==404:
                        return self.ok404
                return False
            def process_response(self, response): return response.text
        self.assertEquals('bad',TestExchange(TestAuth()).result)
        TestExchange.ok404=False
        with self.assertRaises(ResponseError):
            self.assertTrue(TestExchange(TestAuth()).result)


