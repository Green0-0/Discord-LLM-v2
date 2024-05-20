import sentencepiece

# Represents a single message
class Message:
    # parts
    # character
    name : str
    text : str
    len : int

    def __init__(self, name : str, text : str, len : int, parts = None, character = None):
        self.name = name
        self.text = text
        self.len = len
        self.parts = parts
        self.character = character

    def __init__(self, name : str, text : str, tokenizer : sentencepiece.SentencePieceProcessor, parts = None, character = None):
        self.name = name
        self.text = text
        self.len = len(tokenizer.EncodeAsIds(text))
        self.parts = parts
        self.character = character

# Contains a conversation between two or more characters
class Chat:
    messages : list

    def __init__(self, message : str = "", tokenizer : sentencepiece.SentencePieceProcessor = None):
        if message == "":
            self.messages = []
        else:
            self.messages = [Message("", message, tokenizer)]

    def append(self, message : str):
        self.messages.append(message)
        if len(self.messages) > 100:
            self.messages.pop(0)
    
    def get_messages(self, max_tokens : int, extra_msg : str = "", tokenizer : sentencepiece.SentencePieceProcessor = None, min_messages = 2) -> list[Message]:
        new_messages = []
        token_count = 0
        if tokenizer is not None and extra_msg != "":
            token_count = len(tokenizer.EncodeAsIds(extra_msg))
        for message in self.messages[::-1]:
            new_messages.insert(0, message)
            token_count += message.len
            if token_count > max_tokens and min_messages <= len(new_messages):
                return new_messages
        return new_messages