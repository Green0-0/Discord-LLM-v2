from libs import chat, character
import sentencepiece

# Contains the instruction format for the model
# Below are the list of replacements
# _SYSTEM_ -> The system prompt of the AI
# _NAME_ -> The name of the speaker in a message, or the user that sent the request
# _AI-NAME_ -> The name of the AI
# _HISTORY_ -> The entire chat history, formatted with ai_field_history and other_field_history
# _PROMPT_ -> The prompt sent to the model, or the speaker's message
class Format:
    # Name
    name : str

    # The overall prompt template
    # Example: _SYSTEM_\n_HISTORY_USER '_NAME_': _PROMPT_\nAI '_AI-NAME_': 
    template : str

    # Determines how the history is formatted into the template. The final message is reserved for the prompt and excluded from the history.
    # Synonymous with the user
    # Example: [INST] _NAME_: _PROMPT_ [/INST]
    other_field_history : str
    # The AI assistant
    # EXAMPLE: [AI] _AI-NAME_: _PROMPT_ [/AI]
    ai_field_history : str
    # What is used to join the history fields together
    # EXAMPLE: \n
    history_joiner : str

    # The stop criteria for the model
    # Follows the above replacements: _NAME_, _AI-NAME_
    # Mark the beginning with <REGEX> to use regex
    # EXAMPLE: [INST], </s>, [AI], USER:
    stop_criteria : list[str]

    def __init__(self, name : str, template : str, other_field_history : str, ai_field_history : str, history_joiner : str, stop_criteria : list[str]):
        self.name = name
        self.template = template
        self.ai_field_history = ai_field_history
        self.other_field_history = other_field_history
        self.history_joiner = history_joiner
        self.stop_criteria = stop_criteria

    def __init__(self, name : str, json : dict):
        self.name = name
        self.template = json["template"]
        self.ai_field_history = json["ai_field_history"]
        self.other_field_history = json["other_field_history"]
        self.history_joiner = json["history_joiner"]
        self.stop_criteria = json["stop_criteria"]

    def build_prompt(self, character : character.Character, other_name : str, context : chat.Chat, max_tokens : int, tokenizer : sentencepiece.SentencePieceProcessor, continuations : bool = False) -> str:
        history = []
        msgs = context.get_messages(max_tokens - 30, self.template + "\n" + character.system, tokenizer)
        last_speaker = other_name
        for message in msgs[:len(msgs) - 1]:
            if message.name == character.name:
                history.append(self.replaceNameContent(self.ai_field_history, character.name, other_name, message.text))
            else:
                history.append(self.replaceNameContent(self.other_field_history, character.name, message.name,  message.text))
        if msgs[len(msgs) - 1].name == character.name:
            if continuations:
                prompt = ""
                promptAI = msgs[len(msgs) - 1].text
            else:
                history.append(self.replaceNameContent(self.ai_field_history, character.name, other_name, msgs[len(msgs) - 1].text))
                prompt = ""
                promptAI = ""
        else:
            prompt = msgs[len(msgs) - 1].text
            promptAI = ""
            last_speaker = msgs[len(msgs) - 1].name
        if len(history) != 0:
            history.append("")
        realPrompt = self.replaceNameContent(self.template, character.name, last_speaker, prompt).replace("_HISTORY_", self.history_joiner.join(history)).replace("_SYSTEM_", character.system) + promptAI
        return realPrompt

    def replaceNameContent(self, target : str, ai_name : str, other_name : str, text : str) -> str:
        return target.replace("_NAME_", other_name).replace("_AI-NAME_", ai_name).replace("_PROMPT_", text)

    def get_stop_criteria(self, ai_name : str, other_name : str) -> list[str]:
        return [self.replaceNameContent(x, ai_name, other_name, "_PROMPT_") for x in self.stop_criteria]

    
