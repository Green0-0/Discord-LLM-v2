# No idea what this does
import asyncio
import logging
from functools import partial, wraps
import time
import traceback
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
    deep_logging = False
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
        if Config.deep_logging:
            logging.info ("++ RECEIVED PROMPT ++")
            logging.info (prompt)
            logging.info ("+++++++++++++++++++++")

        n = 0
        while n < 3:
            response = ""
            error = ""
            n += 1
            try:
                response = self.model.get_completion(prompt, self.params)
                if Config.deep_logging:
                    logging.info ("++ RECEIVED RESPONSE ++")
                    logging.info (response)
                    logging.info ("+++++++++++++++++++++")
                if "llm error" in response.lower():
                    raise Exception("LLM Error in response: " + response)
                response = response[len(prompt):]
                for stopper in self.format.get_stop_criteria(character.name, other_name):
                    if "REGEX" in stopper:
                        stopper = stopper[stopper.index("REGEX") + 5:]
                        if stopper.startswith(" "):
                            stopper = stopper[1:]
                        # use stopper as regex to check if response matches, and if so, remove the match and everything that comes after
                        regex = re.compile(stopper)
                        if regex.search(response):
                            response = response[:regex.search(response).span()[0]]
                    elif stopper in response:
                        response = response[:response.find(stopper)]
                response = response.strip()
                if response[0] == response[-1] and response[0] == "\"":
                    response = response[1:-1]
                for v in self.validators:
                    if not v.Validate(response, chat):
                        response = ""
                        error = "Validator " + v.name + " failed on response: " + response
                        raise Exception(error)
                n = 3
            except Exception as e:
                response = ""
                error = str(e)
                tb = traceback.format_exc()
                logging.info("!!! ERROR !!!")
                logging.error(tb)
                logging.info("-------------")
                time.sleep(2)
        if response == "":
            raise Exception("Failed to generate response because of error:\n'" + error + "'")
            return "(error)"
        return response