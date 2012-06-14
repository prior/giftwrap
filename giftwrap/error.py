from grabbag.exception import Error as BaseError
from grabbag.property import is_cached

class Error(BaseError): pass

class ExchangeError(Error):
    def __init__(self, msg=None, err=None, exchange=None):
        super(ExchangeError, self).__init__(msg, err)
        self.exchange = exchange

    def __unicode__(self):
        url = '?'
        try: 
            url = self.exchange.url
        except: pass
        return u'%s (url=%s ) %s' % (self.msg, url, self.wrapped_error_str)
    def __repr__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__, repr(self.msg), repr(self.err), repr(self.exchange))

class RequestError(ExchangeError):
    pass

class TimeoutError(ExchangeError): 
    def __unicode__(self):
        url = '?'
        timeout = '?'
        try: 
            url = self.exchange.url
            timeout = self.exchange.timeout
        except: pass
        return u'%s (url=%s timeout=%s ) %s' % (self.msg, url, timeout, self.wrapped_error_str)

class ResponseError(ExchangeError):
    def __unicode__(self):
        url = '?'
        status_code = '?'
        text = '?'
        try: 
            url = self.exchange.url
            status_code = self.exchange.response.status_code
            text = self.exchange.response.content
        except: pass
        return u'%s (%s url=%s %s ) %s' % (self.msg, status_code, url, text, self.wrapped_error_str)

class JsonParseError(ResponseError): 
    def __unicode__(self):
        content = '???'
        try: 
            content = self.exchange.response.content
        except: pass
        return u'%s\n=== content ===\n%s\n===============\n' % (super(JsonParseError, self).__unicode__(), content)

class XmlParseError(ResponseError):
    def __unicode__(self):
        content = '???'
        try: 
            content = self.exchange.response.content
        except: pass
        return u'%s\n=== content ===\n%s\n===============\n' % (super(XmlParseError, self).__unicode__(), content)


