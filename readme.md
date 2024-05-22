# How to use the app:
- Select the SRT file
- Select if you want both languages to be in the output SRT file or not
- If you want both languages to be in the output SRT, you can choose which language is on top
- Select the preferred API for translation (supports Google Translate and GPT4)
- Google Translate has no additional options
- GPT4 has 2 options: 
   - how many batches of subtitle blocks to process (I suggest 40 because it works faster, and it has proven to be stable from my testing)
   - an additional prompt to be given to the app.
   - Note, the base prompt is the following: "role": "system", "content": "You are a translator." and then each instructions is "Please translate the text of this subtitle file from {from_lang} to {to_lang}. Keep the same file structure and keep in mind that you shouldn't just translate line by line, sometimes you need the whole context to translate. {additional_prompt}"

# API Keys
You have a config file secrets.config where you can put your api keys (example provided as secrets_example.config).

# Build (optional)
To build an app:
pyinstaller --onefile --windowed translate.py

If you build an app, it can't read the api keys from secrets.config. Instead, it will ask you to copy/paste the content of the secrets.config once, during startup. As long as you keep the app open, it won't ask again.
