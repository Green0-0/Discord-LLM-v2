from libs import params
import json
import socket
import ssl
import logging
import http.client

# Points to a LLM model on neuroengine 
class Model:
    name : str
    context_length : int

    def __init__(self, name = str, context_length = int):
        self.name = name
        self.context_length = context_length

    def get_completion(self, text : str, p : params.Params):
        # Create a JSON message with the parameters
        command = {
            'message': text,
            'temperature': p.temperature,
            'top_p': p.top_p,
            'top_k': p.top_k,
            'min_p': p.min_p,
            'repetition_penalty': p.repetition_penalty,
            'max_new_len': p.max_new_tokens,
            'seed': 0,
            'raw' : "True"
        }
        # Attempt to get AI response
        responded = True
        tries = 3
        try:
            count=0
            while(count<tries):
                count+=1
                response=self.send(command)
                if int(response["errorcode"])==0:
                    break
        except:
            raise Exception("Connection error.")
        return response["reply"]

    def send(self,command):
        json_data = json.dumps(command)
        # Create an HTTP connection
        socket.setdefaulttimeout(180)
        connection = http.client.HTTPSConnection("api.neuroengine.ai", "443")

        # Send a POST request with the JSON message
        headers = {'Content-Type': 'application/json'}
        connection.request('POST', f'/{self.name}', json_data, headers)

        # Get the response from the server
        response = connection.getresponse().read().decode()
        connection.close()
        response = json.loads(response)
        return response