import requests
import requests.async
from .utils import reraise, cached_property, dmerge
from . import error
import json


class ApiExchangeAuth(object):
    @property 
    def params(self): return {}
    @property 
    def headers(self): return {}



"""
This class encompasses a single api exchange.  It is the base class that all api exchanges must 
derive from.  It is structured in a way that enables it serve both synchronous and asynchronous calls.
There are many pieces that can and/or must be overridden for your specific api calls.
"""
class ApiExchange(object):
    protocol = 'https'
    timeout = 30

    def __init__(self, auth):
        self.auth = auth
        super(ApiExchange, self).__init__()


    def _build_method(self, kls_method=None): return kls_method
    def _build_domain(self, kls_domain=None): return kls_domain
    def _build_base_path(self, kls_base_path=None): return kls_base_path
    def _build_sub_path(self, kls_sub_path=None): return kls_sub_path
    def _build_params(self, kls_params=None): return kls_params
    def _build_headers(self, kls_headers=None): return kls_headers
    def _build_data(self, kls_data=None): return kls_data
    def _build_timeout(self, kls_timeout=None): return kls_timeout

    @cached_property
    def method(self): return self._build_method(getattr(self.__class__,'method', 'GET')).upper()
    @cached_property
    def domain(self): return self._build_domain(getattr(self.__class__,'domain', '')).strip('/')
    @cached_property
    def base_path(self): return self._build_base_path(getattr(self.__class__,'base_path', '')).strip('/')
    @cached_property
    def sub_path(self): return self._build_sub_path(getattr(self.__class__,'sub_path', '')).strip('/')
    @cached_property
    def params(self): return dmerge({}, self._build_params(getattr(self.__class__,'params', {})), self.auth.params)
    @cached_property
    def headers(self): return dmerge({}, self._build_headers(getattr(self.__class__,'headers', {})), self.auth.headers)
    @cached_property
    def data(self): return self._build_data(getattr(self.__class__,'data', None))
    @cached_property
    def timeout(self): return self._build_timeout(getattr(self.__class__,'timeout', None))
    @cached_property
    def url(self): return '/'.join(filter(None,['%s:/'%self.__class__.protocol.split('://')[0], self.domain, self.base_path, self.sub_path]))

    def _requests_call(self, requests_obj):
        return requests_obj.get_attribute(self.method.lower())(self.url, params=self.params, data=self.data, headers=self.headers, timeout=self.timeout)
    @cached_property
    def response(self): return self._requests_call(requests)
    @cached_property
    def async_request(self): return self._requests_call(requests.async)

    @cached_property
    def result(self): return self._process_response()

    # force a synchronous retry if we're not over the limit
    # TODO: allow retries to be asynchronous as well -- would need to do this in the batch method somehow
    def _retry_or_fail(self, err): 
        self.failures.append(err)
        if len(self.failures) > self.max_retries: 
            reraise(err)
        del self.response
        return self._process_response()

    def _process_response(self):
        try:
            self.response.raise_for_status()
        except requests.exceptions.Timeout as err:
            return self._retry_or_fail(error.TimeoutError(self.request, err=err))
        except requests.exceptions.RequestException as err:
            if self.response is None or self.response.status_code==0:
                return self._retry_or_fail(error.RequestError(self.request, 'unknown error', err=err))
            else:
                return self._retry_or_fail(error.ResponseError(self.response, err=err))
        if not self.response.status_code or self.response.status_code < 200 or self.response.status_code >= 300:
            return self._retry_or_fail(error.ResponseError(self.response, err=err))
        return self.process_content(self.response.content, self.response)
            
    def process_content(self, content, response): return NotImplementedError()

    @classmethod
    def bulk_exchange(self, exchanges, async=True):
        if async:
            for exchange,response in zip(exchanges, requests.async([e.async_request for e in exchanges])):
                exchange.response = response
        else:
            for exchange in exchanges:
                exchange.response
        return exchanges


class EnvironmentalApiExchange(ApiExchange):
    def _build_domain(self, kls_domain=None): 
        return kls_domain or self.__class__.domains[getattr(self,'env',None) or getattr(self.auth,'env','prod')]

class JsonApiExchange(ApiExchange):
    def process_response(self, content, response): 
        return self.process_json(json.loads(response.content), response)

    def process_json(self, json, response): return NotImplementedError()


#class HubSpotApiExchange(EnvironmentalApiExchange):
    #domains = dict(qa='api.hubapiqa.com', prod='api.hubapi.com')

#class InternalHubSpotApiExchange(ApiExchange):
    #domains = dict(qa='internal.hubapiqa.com', prod='internal.hubapi.com')

#class TaskQueueExchange(InternalHubSpotApiExchange):
    #base_path = 'taskqueues/v1'

