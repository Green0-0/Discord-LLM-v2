from libs import chat

# Checks for a phrase in the output, if found, forces the output to be regenerated
# Special names: 
# _LEN_<x -> Checks if the length of the output is less than x
# _REPETITION_ -> Checks if the phrase is repeated in past messages
class Validator():
    name : str
    def __init__(self, name : str):
        self.name = name

    def Validate(self, text : str, chat : chat.Chat) -> bool:
        if "_LEN_<" in self.name:
            try:
                i = int(self.name.split("<")[1].strip())
                return len(text) > i
            except Exception:
                raise
        if self.name == "_REPETITION_":
            whole_history = ""
            for message in chat.get_messages(4000):
                whole_history += message.text
            sec_1 = text[:int(len(text) / 3)]
            sec_2 = text[int(len(text) / 3) : int(2 * len(text) / 3)]
            sec_3 = text[int(2 * len(text) / 3) :]
            return sec_1 not in whole_history and sec_2 not in whole_history and sec_3 not in whole_history
        return self.name.lower() not in text.lower()
    
    def __str__(self):
        return self.name