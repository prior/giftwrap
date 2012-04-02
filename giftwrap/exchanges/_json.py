import json
from ..exchange import Exchange


class JsonExchange(Exchange):
    headers = { 'Content-Type':'application/json', 'Accept':'application/json' }

    def process_response(self, response): 
        data = json.loads(response.content)
        return self.process_data(data, response)

    def process_data(self, data, response): return NotImplementedError()
