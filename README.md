Runs a LLM using the API from https://www.neuroengine.ai/. This does NOT require signup or an API key, so the bot works out of the box as long as you pass it your token by adding a text file (token.txt) with your discord bot token.
I do not plan to add support for togetherAI/local, however, it should be fairly trivial to support these by modifying the ``get_completion`` method of ``libs/model.py``.

FEATURES:
- Deploy any number of characters (though recommended to keep it under 15) with a single discord bot that respond naturally in conversations
- Characters can be toggled on and off per channel (/toggle_character), and they can be forced to reply with /reply_as
- Retry responses with /retry_last, delete responses with /delete_last, clear memory with /clear_memory

![image](https://github.com/Green0-0/Discord-LLM-v2/assets/138409197/18240302-5ee3-4496-ba8a-74a083552e29)
![image](https://github.com/Green0-0/Discord-LLM-v2/assets/138409197/903b04b7-eaa0-4876-b720-19e72053ed88)

- Create, edit, and view character system prompts/profiles (/create_character, /edit_character, /view_character)

![image](https://github.com/Green0-0/Discord-LLM-v2/assets/138409197/886166ac-35d2-4227-977e-530ffe8ac87e)

- Modify and create new prompt formats with my own formatting markdown (/edit_format, /create_format, /view_format)

![image](https://github.com/Green0-0/Discord-LLM-v2/assets/138409197/1f90a979-ec3a-49c6-ac54-f465456f3229)

- Configure sampling presets, mix and match prompt formats, sampling presets, and neuroengine API models with configurations

![image](https://github.com/Green0-0/Discord-LLM-v2/assets/138409197/fab44ffc-02ca-4788-a55e-9ee7931477b6)

...and more!
