import json
import requests
import requests.async
from utils.property import cached_property
from utils.dict import merge
from utils.list import first_not_none, first_truthy
from . import error


#TODO: implement good logging (or any logging to start)-- 



class Auth(object):
    def __init__(self):
        super(Auth, self).__init__()
        self.params = {}
        self.headers = {}


"""
This class encompasses a single api exchange.  It is the base class that all api exchanges must 
derive from.  It is structured in a way that enables it serve both synchronous and asynchronous calls.
There are many pieces that can and/or must be overridden for your specific api calls.
"""

DEFAULTS = dict(method='GET', protocol='https', timeout=20, max_retries=0)

class Exchange(object):
    method = DEFAULTS['method']
    protocol = DEFAULTS['protocol']
    domain = None
    base_path = None
    sub_path = None
    params = {}  # additive
    headers = {}  # additive
    data = None
    timeout = DEFAULTS['timeout']
    max_retries = DEFAULTS['max_retries']

    def __init__(self, auth, **kwargs):
        super(Exchange, self).__init__()
        self.auth = auth
        self.failures = []
        self.calc_pieces(**kwargs)

    #override these for instance specific reasoning
    def _method(self): return None
    def _protocol(self): return None
    def _domain(self): return None
    def _base_path(self): return None
    def _sub_path(self): return None
    def _params(self): return {}  # additive
    def _headers(self): return {}  # additive
    def _data(self): return None
    def _timeout(self): return None
    def _max_retries(self): return None

    def truthy_attr(self, attr, init_kwargs, fallback=None, add_auth=False):
        return first_truthy( (init_kwargs.get(attr), add_auth and getattr(self.auth, attr, None) or None, getattr(self,'_%s'%attr)(), getattr(self.__class__,attr), fallback) )
    def not_none_attr(self, attr, init_kwargs, fallback=None, add_auth=False): 
        return first_not_none( (init_kwargs.get(attr), add_auth and getattr(self.auth, attr, None) or None, getattr(self,'_%s'%attr)(), getattr(self.__class__,attr), fallback) )
    def added_attr(self, attr, init_kwargs, add_auth=False): 
        return merge({}, add_auth and getattr(self.auth, attr, {}) or {}, getattr(self.__class__,attr) or {}, getattr(self,'_%s'%attr)() or {}, init_kwargs.get(attr,{}) or {})

    def calc_pieces(self, **init_kwargs):
        self.method = self.truthy_attr('method', init_kwargs, DEFAULTS['method']).upper()
        self.protocol = self.truthy_attr('protocol', init_kwargs, DEFAULTS['protocol']).lower()
        self.domain = self.truthy_attr('domain', init_kwargs).strip('/').lower()
        self.base_path = self.not_none_attr('base_path', init_kwargs, '').strip('/')
        self.sub_path = self.not_none_attr('sub_path', init_kwargs, '').strip('/')
        self.params = self.added_attr('params', init_kwargs, add_auth=True)
        self.headers = self.added_attr('headers', init_kwargs, add_auth=True)
        self.data = self.not_none_attr('data', init_kwargs)
        self.timeout = self.truthy_attr('timeout', init_kwargs, DEFAULTS['timeout'])
        self.max_retries = self.not_none_attr('max_retries', init_kwargs, DEFAULTS['max_retries'])

    @cached_property
    def url(self): return '/'.join(('%s:/'%self.protocol.split('://')[0], self.domain, self.base_path, self.sub_path))

    def _requests_call(self, requests_obj):
        return getattr(requests_obj,self.method.lower())(self.url, params=self.params, data=self.data, headers=self.headers, timeout=self.timeout)
    @cached_property
    def response(self): 
        response = self._requests_call(requests)
        self.request = response.request
        return response
    @cached_property
    def request(self): return self._requests_call(requests.async)

    @cached_property
    def result(self):
        return self._process_response()

    # force a synchronous retry if we're not over the limit
    # TODO: allow retries to be asynchronous as well -- would need to do this in the batch method somehow
    def _retry_or_fail(self, wrapped_err): 
        self.failures.append(wrapped_err)
        if len(self.failures) > self.max_retries: 
            wrapped_err._raise()
        del self.response
        return self._process_response()

    def _process_response(self):
            try:
                self.response.raise_for_status()
            except requests.exceptions.Timeout as err:
                return self._retry_or_fail(error.TimeoutError(err=err, exchange=self))
            except requests.exceptions.RequestException as err:
                return self._retry_or_fail(error.RequestError(err=err, exchange=self))
            if not self.response.status_code or self.response.status_code < 200 or self.response.status_code >= 300:
                return self._retry_or_fail(error.ResponseError(err=err, exchange=self))
            return self.process_response(self.response)

    def process_response(self,response): raise NotImplementedError()

    @classmethod
    def bulk_exchange(self, exchanges, async=True):
        if async:
            for exchange,response in zip(exchanges, requests.async.map([e.request for e in exchanges])):
                exchange.response = response
        else:
            for exchange in exchanges:
                exchange.response
        return exchanges


class EnvironmentalExchange(Exchange):
    def _build_domain(self, kls_domain=None): 
        return kls_domain or self.__class__.domains[getattr(self,'env',None) or getattr(self.auth,'env','prod')]

class JsonExchange(Exchange):
    headers = {'Content-type': 'application/json'}

    def process_response(self, response): 
        return self.process_json(json.loads(response.content), response)

    def process_data(self, data, response): return NotImplementedError()


#class HubSpotApiExchange(EnvironmentalApiExchange):
    #domains = dict(qa='api.hubapiqa.com', prod='api.hubapi.com')

#class InternalHubSpotApiExchange(ApiExchange):
    #domains = dict(qa='internal.hubapiqa.com', prod='internal.hubapi.com')

#class TaskQueueExchange(InternalHubSpotApiExchange):
    #base_path = 'taskqueues/v1'

