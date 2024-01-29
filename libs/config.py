# No idea what this does
import asyncio
from functools import partial, wraps
def to_thread(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        callback = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, callback)
    return wrapper

from libs import model, format, params, validator, chat, character
import re
import sentencepiece

# A configuration allows you to make neuroengine requests using a chat
# Automatically formats the chat using the given format, sends it to the model with parameters, applies validators
# Retries if fails
class Config:
    name : str
    model : model.Model
    format : format.Format
    params : params.Params
    validators : list[validator.Validator]

    def __init__(self, name : str, model : model.Model, format : format.Format, params : params.Params, validators : list[validator.Validator]):
        self.name = name
        self.model = model
        self.format = format
        self.params = params
        self.validators = validators

    @to_thread
    def queue(self, chat : chat.Chat, character : character.Character, other_name, tokenizer : sentencepiece.SentencePieceProcessor) -> str:
        prompt = self.format.build_prompt(character, other_name, chat, self.model.context_length, tokenizer)
        n = 0
        while n < 3:
            response = ""
            n += 1
            try:
                response = self.model.get_completion(prompt, self.params)
                response = response[len(prompt):]
                for stopper in self.format.get_stop_criteria(character.name, other_name):
                    if "<Regex>" in stopper:
                        stopper = stopper[stopper.find("<REGEX>"):]
                        if stopper.startswith(" "):
                            stopper = stopper[1:]
                        # use stopper as regex to check if response matches, and if so, remove the match and everything that comes after
                        regex = re.compile(stopper)
                        if regex.search(response):
                            response = response[:regex.search(response).span()[1]]
                    elif stopper in response:
                        response = response[:response.find(stopper)]
                        break
                response = response.strip()
                for v in self.validators:
                    if not v.Validate(response, chat):
                        response = ""
                        raise Exception("Validator " + v.name + " failed on response: " + response)
                n = 3
            except Exception as e:
                response = ""
                print ("!!! ERROR !!!")
                print (e)
                print ("-------------")
        if response == "":
            raise Exception("Failed to generate response.")
            return "(error)"
        return response