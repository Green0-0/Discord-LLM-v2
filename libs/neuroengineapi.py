"""
#### 2-Clause BSD licence:

Copyright 2023 Alfredo Ortega @ortegaalfredo

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import socket
import select
import time
import json
import http.client
import ssl
import sys

# Client class
class Neuroengine:
    #__init__(): Initializes a new instance of the neuroengine class.
    #Parameters:
    #   server_address: A string representing the server address.
    #   server_port: An integer representing the server port.
    #   service_name: A string representing the name of the service.
    #   name (optional): A string representing an optional name (not required).
    #   verify_ssl (optional): A boolean indicating whether to verify SSL certificates or not.

    def __init__(self, service_name, server_address="api.neuroengine.ai",server_port=443,name="",verify_ssl=True):
        self.server_address=server_address
        self.server_port=server_port
        self.service_name=service_name
        self.name=name
        self.verify_ssl=verify_ssl

    #getmodel(): Return a list of active LLM models in the server

    def getModels(self):
        command = {'command': 'getmodels' }
        response=self.send(command)
        return response

    def request(self, prompt,temperature=1,top_p=0.8,top_k=20,repetition_penalty=0.5,max_new_len=3000,seed=0,raw=True,tries=5):
        """ request(): Sends a request to the server and returns the response.
        Parameters:
        - prompt (str): The text prompt that will be used to generate the response.
        - temperature (float): Controls the randomness of the output. Higher values (e.g., 1.0) make the output more random, while lower values (e.g., 0.2) make it more deterministic. Default is 1.0.
        - top_p (float): Determines the cumulative probability threshold for generating the output. Tokens with cumulative probability higher than this value are considered for sampling. Default is 0.9.
        - top_k (int): Controls the number of top tokens to consider for generating the output. Only the top-k tokens are used for sampling. Default is 40.
        - repetition_penalty (float): Controls the penalty applied to repeated tokens in the output. Higher values (e.g., 1.2) discourage repeating tokens, while lower values (e.g., 0.8) encourage repetition. Default is 1.2.
        - max_new_len (int): Controls the maximum length of the generated response. The response will be truncated if its length exceeds this value. Default is 128.
        - seed (int): The random seed for generating the response. Use this to control the reproducibility of the output. Default is 0.
        - raw (bool): If True, the response will be returned as raw JSON string; if False, the reply content will be extracted from the JSON. Default is False.
        - tries (int): The number of attempts to send the request in case of errors before giving up. Default is 5.
    Returns:
        - str: The generated response or an error message, depending on the success of the request. """
        if (prompt is None):
            return("")
        # Create a JSON message
        command = {
            'message': prompt,
            'temperature': temperature,
            'top_p':top_p,
            'top_k':top_k,
            'repetition_penalty':repetition_penalty,
            'max_new_len':max_new_len,
            'seed':seed,
            'raw' :str(raw)
        }
        try:
            count=0
            while(count<tries):
                count+=1
                response=self.send(command)
                if int(response["errorcode"])==0:
                        break
        except:
            response={}
            response["reply"]="Connection error. Try in a few seconds."
        return response["reply"]

    def send(self,command):
        json_data = json.dumps(command)
        # Create an HTTP connection
        socket.setdefaulttimeout(180)
        if (self.verify_ssl):
            connection = http.client.HTTPSConnection(self.server_address, self.server_port)
        else:
            connection = http.client.HTTPSConnection(self.server_address, self.server_port, context = ssl._create_unverified_context())

        # Send a POST request with the JSON message
        headers = {'Content-Type': 'application/json'}
        connection.request('POST', f'/{self.service_name}', json_data, headers)

        # Get the response from the server
        response = connection.getresponse()
        response = response.read().decode()

        connection.close()
        response = json.loads(response)
        return response
n = Neuroengine(service_name="Neuroengine-Large")
print(n.getModels())