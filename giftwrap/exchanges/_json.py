try:
    import ujson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json
from ..exchange import Exchange


class JsonExchange(Exchange):
    headers = { 'Content-Type':'application/json', 'Accept':'application/json' }

    def process_response(self, response): 
        data = None
        if response.encoding is None:
            response.encoding = "utf-8"
        text = (response.text or '').strip()
        if text:
            data = json.loads(text)
        return self.process_data(data, response)

    def process_data(self, data, response): return NotImplementedError()

    def data(self): 
        _data = self.python_data()
        if _data is None: return None
        return json.dumps(self.python_data())
        
    def python_data(self): return None

