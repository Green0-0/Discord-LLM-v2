import discord
import requests
from io import StringIO
import logging
from libs import character, config, format, model, params, validator, chat
import sentencepiece
import json

# Should only be called once
def init(Log_stream : StringIO):  
    # Get token and guild from file
    global TOKEN

    # Tokenizer file
    global tokenizer
    tokenizer = sentencepiece.SentencePieceProcessor(model_file='tokenizer.model')

    with open("token.txt", "r") as f:
        TOKEN = f.read()

    # Store which webhooks each character uses
    global webhookChannels
    webhookChannels = {}

    # Stores all chats
    global chats
    chats = {}

    # Stores a list of admins who have permission to manage the bot
    # Adds me as an admin
    global admins
    admins = ["320920450714828800"]

    # Store extensions, that is, command groups to be loaded into the bot
    global extensions
    extensions = ["cogs.messaging", "cogs.configuration_viewing", "cogs.configuration_editing", "cogs.characters"]
    global skip
    skip = []
    
    global log_stream
    log_stream = Log_stream

    global formats
    alpaca_chat = format.Format("Alpaca-Chat", json.loads(open("formats/alpaca_chat.json", "r").read()))
    alpaca_instruct_chat = format.Format("Alpaca-Instruct-Chat", json.loads(open("formats/alpaca_instruct_chat.json", "r").read()))
    chatml_chat = format.Format("ChatML", json.loads(open("formats/chatml_chat.json", "r").read()))
    llama_3_chat = format.Format("Llama-3-Chat", json.loads(open("formats/llama_3_chat.json", "r").read()))
    llama_3_rp = format.Format("Llama-3-RP", json.loads(open("formats/llama_3_rp.json", "r").read()))
    mistral_chat = format.Format("Mistral-Chat", json.loads(open("formats/mistral_chat.json", "r").read()))
    vicuna_chat = format.Format("Vicuna-Chat", json.loads(open("formats/vicuna_chat.json", "r").read()))
    simple = format.Format("Simple", json.loads(open("formats/simple.json", "r").read()))
    completion = format.Format("Completion", json.loads(open("formats/completion.json", "r").read()))
    
    formats = [alpaca_chat, alpaca_instruct_chat, chatml_chat, llama_3_chat, llama_3_rp, mistral_chat, vicuna_chat, simple, completion]

    global validators
    rep_test = validator.Validator("_REPETITION_")
    len_test = validator.Validator("_LEN_<3")
    refusal_test = validator.Validator("as a large")
    refusal_test_2 = validator.Validator("i am unable to")
    refusal_test_3 = validator.Validator("i cannot help")
    validators = [rep_test, len_test, refusal_test, refusal_test_2, refusal_test_3]

    global models
    neuroengine_large = model.Model("Neuroengine-Large", 6000)
    neuroengine_medium = model.Model("Neuroengine-Medium", 6000)
    neuroengine_fast = model.Model("Neuroengine-Fast", 8000)
    models = [neuroengine_medium, neuroengine_large, neuroengine_fast]

    global paramss
    stable = params.Params("Stable", temperature = 0.5, max_new_tokens = 2000)
    standard = params.Params("Standard")
    creative = params.Params("Creative", temperature = 1.5, max_new_tokens = 1000)
    creative_rp = params.Params("Creative-RP", temperature = 2.3, max_new_tokens=500)
    analysis = params.Params("Analysis", temperature = 0.3, repetition_penalty = 0, max_new_tokens = 20)
    schizo1 = params.Params("Schizo1", temperature = 3.8, min_p = 0.25, max_new_tokens = 500)
    schizo2 = params.Params("Schizo2", temperature = 5, min_p = 0.35, max_new_tokens = 500)
    paramss = [stable, standard, creative, creative_rp, analysis, schizo1, schizo2]

    global configs
    large_stable = config.Config("Large-Stable", neuroengine_large, llama_3_chat, stable, [len_test])
    large_rp = config.Config("Large-RP", neuroengine_large, llama_3_chat, creative_rp, [len_test])
    medium_stable = config.Config("Medium-Stable", neuroengine_medium, mistral_chat, stable, [len_test])
    medium_rp = config.Config("Medium-RP", neuroengine_medium, mistral_chat, creative_rp, [len_test])
    fast_stable = config.Config("Fast-Stable", neuroengine_fast, llama_3_chat, stable, [len_test])
    fast_rp = config.Config("Fast-RP", neuroengine_fast, llama_3_chat, creative_rp, [len_test])
    configs = [large_rp, large_stable, medium_rp, medium_stable, fast_rp, fast_stable]
    
    global analysis_config
    analysis_config = config.Config("Analysis-Config", neuroengine_medium, completion, analysis, [])
    global analysis_format
    analysis_format = llama_3_chat

    global characters
    trump = character.Character(large_rp, 
                                "Donald Trump", 
                                "https://upload.wikimedia.org/wikipedia/en/c/c5/Donald_Trump_mug_shot.jpg", 
                                """Donald Trump is a Republican and the 45th president of the United States. 

Dialogue Examples (Do not repeat): 
- "FAKE NEWS! This guy, Biden, doesn't know what he's talking about! ICE CREAM? Who cares about ICE CREAM?! I care about WINNING, believe me! Nobody knows more about winning than I do!"
- "I would've won that war so BIGLY, so STRONGLY. It would've been YUGE. And those communists? They're losers, folks."

Personality:
- Strongly christian, possibly racist/sexist
- Obsessed with the "fake news media" and how "the election was stolen"
- Easily gets offended (especially when people mention the election, how hes fat, how hes failed, etc) and strongly angered
- Not very sensible
- Really likes to eat mcdonalds and other fast food"""
)
    
    biden = character.Character(large_rp, 
                                "Joe Biden", 
                                "https://www.aljazeera.com/wp-content/uploads/2023/03/2023-03-13T131806Z_1163339626_RC20TZ9FUXJK_RTRMADP_3_GLOBAL-BANKS-SVB-BIDEN.jpg",
                                """Joe Biden is a Democrat and the 46th president of the United States. 

Dialogue Examples (Do not repeat):
- "Sometimes when I look at myself in the mirror, I swear I see antennas growing out of my head! Hahaha... oh wait, did I say that out loud?"
- "Say, have you seen my pills? I could've sworn I left them right here on my desk..."

Personality:
- Old age makes him forgetful, slow and easily confused
- Mixes and makes up information/names
- Forgets to take/loses his pills that are meant to help his condition
- Likes ice cream and children"""
)
    
    obama = character.Character(large_rp, 
                                "Barack Obama", 
                                "https://hips.hearstapps.com/hmg-prod/images/barack-obama-white-house-portrait-644fccf590557.jpg", 
                                """Barack Obama is a Democrat and the 44th President of the United States.

Dialogue Examples (Do not repeat): 
- "You know, if I were still playing college basketball today, I bet I could give some of these young whippersnappers a run for their money!"
- "No need to bring my race into this, Trump. Remember when I called a drone strike on that school in Afghanistan? Yeah, I can do that again." 

Personality
- Proud (maybe too proud) self-made African American 
- Eloquent with professional speech/manners
- Secretly believes everyone around him is racist and has an agenda against him as the only black president
- Loves KFC and watermelon but gets offended when someone mentions it
- Quick to violence; known for drone striking schools in the middle east"""
                                )
    
    freud = character.Character(large_rp, 
                                "Sigmund Freud", 
                                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Sigmund_Freud%2C_by_Max_Halberstadt_%28cropped%29.jpg/1200px-Sigmund_Freud%2C_by_Max_Halberstadt_%28cropped%29.jpg", 
                                """Sigmund Freud is the slightly-insane slightly-genius founder of psychoanalysis in the 1900s. 

Dialogue Examples (Do not repeat): 
- "If a man has been his mother's undisputed darling, he retains throughout life triumphant feelings… This is altogether the most perfect, the most free from ambivalence of all human relationships."
- "The great question that has never been answered, and which I have not yet been able to answer, despite my thirty years of research into the feminine soul, is 'What does a woman want?'"
- "The repressed merges into the id as well, and is merely a part of it."

Personality:
- Exotic/incomprehensible behavior like asking people about their relationship with their mother
- Obsessed with the unconscious mind and sexual desired, frequently talks about ID, ego, superego, dreams
- Occasionally perverted and creepy, even insane
- Takes drugs"""
                                )
    characters = [trump, biden, obama, freud]

# Gets a webhook to send model messages through. If none is found, then create a new one
# This should NOT be called in dms, it will break
async def get_webhook(channel, character : character.Character) -> discord.Webhook:
    if isinstance(channel, discord.Thread):
        channel = channel.parent
    global webhookChannels
    if channel not in webhookChannels:
        webhookChannels[channel] = {}

    key = (character.name + character.icon)
    if key in webhookChannels[channel]:
        return webhookChannels[channel][key]
    else:
        logging.info(f"<Log> Generated new webhook for character \"{character.name}\" in channel \"{channel.name}\"")
        avatar = requests.get(character.icon).content
        # If there isn't enough space for the new webhook (discord has a webhook limit), delete one from the cache
        if len(webhookChannels[channel]) > 9:
            toDelete = webhookChannels[channel].popitem()
            logging.info(f"<Log> Deleted webhook \"{toDelete[1].name}\" to make space for new one.")
            await toDelete[1].delete()
        w = await channel.create_webhook(name=character.name, avatar=avatar)
        webhookChannels[channel][key] = w 
        return w

# Gets a chat
def get_chat(channel) -> chat.Chat:
    if channel in chats:
        return chats[channel]
    else:
        c = chat.Chat()
        chats[channel] = c
        return c
