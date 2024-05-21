import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pysrt
import json
import requests
import sys
import os

# Global variables
translateEngine = "gpt"
blocks_to_translate = 10
original_subtitles = None
input_file_path = None  # Initialize input_file_path as None
api_keys = {}

# Configuration file path
config_file_name = 'secrets.config'
application_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(application_path, config_file_name)

def import_file():
    global original_subtitles, input_file_path  # Declare original_subtitles and input_file_path as global
    file_path = filedialog.askopenfilename(filetypes=[("Subtitle files", "*.srt")])
    if file_path:
        try:
            subtitles = parse_srt(file_path)
            original_subtitles = subtitles  # Store the original subtitles
            input_file_path = file_path  # Store the input file path
            display_subtitles(subtitles, file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load subtitles: {e}")
    else:
        messagebox.showerror("Error", "No file selected")

def parse_srt(file_path):
    return pysrt.open(file_path)

def display_subtitles(subtitles, file_path):
    status_text.delete("1.0", tk.END)  # Clear the output section
    status_text.insert(tk.END, f"Imported file: {file_path}\n\n")
    status_text.insert(tk.END, "Subtitles loaded successfully.\n\n")

def load_api_keys():
    global api_keys
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                for line in file:
                    key, value = line.strip().split(':')
                    api_keys[key] = value
                    #status_text.insert(tk.END, f"{key} API key loaded: {value}\n")
        else:
            if getattr(sys, 'frozen', False):
                # Running as a packaged executable
                prompt_for_config()
            else:
                messagebox.showerror("Error", f"Configuration file {config_file_name} not found.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load API keys: {e}")

def read_specific_api_key(service_name):
    return api_keys.get(service_name, None)

def prompt_for_config():
    config_content = simpledialog.askstring("Input Required", "Please paste the content of your secrets.config file:")
    if config_content:
        with open(config_path, 'w') as file:
            file.write(config_content)
        load_api_keys()
    else:
        messagebox.showerror("Error", "No content provided for configuration.")

def reset_subtitles():
    global subtitles, input_file_path
    if input_file_path:
        try:
            subtitles = parse_srt(input_file_path)
            display_subtitles(subtitles, input_file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset subtitles: {e}")
    else:
        messagebox.showerror("Error", "No file loaded to reset.")

def translate_srt():
    reset_subtitles()
    engine = translateEngine_var.get()
    if engine == "gpt":
        translate_gpt_api()
    elif engine == "google":
        translate_google_api()
    else:
        messagebox.showerror("Error", f"Unsupported translation engine: {engine}")

def save_srt_file(subtitles, engine):
    base_name = os.path.basename(input_file_path)
    dir_name = os.path.dirname(input_file_path)
    output_file_name = f"output_{engine}_{base_name}"
    output_file_path = os.path.join(dir_name, output_file_name)
    
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for subtitle in subtitles:
            f.write(str(subtitle) + "\n")
    
    messagebox.showinfo("Info", f"Translation saved to {output_file_path}")

def translate_google_api():
    api_key = read_specific_api_key('google')
    if not api_key:
        messagebox.showerror("Error", "API key for Google Translate not found.")
        return

    from_lang = from_var.get()
    to_lang = to_var.get()

    if 'subtitles' not in globals():
        messagebox.showerror("Error", "No subtitles loaded.")
        return
    
    merge_texts = merge_checkbox_var.get()
    from_on_top = from_on_top_checkbox_var.get()
    translated_subtitles = []

    for subtitle in subtitles:
        try:
            response = requests.post(
                url='https://translation.googleapis.com/language/translate/v2',
                params={
                    'key': api_key,
                    'q': subtitle.text,
                    'source': from_lang,
                    'target': to_lang,
                    'format': 'text'
                }
            )
            result = response.json()
            translation = result['data']['translations'][0]['translatedText']
            if merge_texts:
                if from_on_top:
                    subtitle.text = subtitle.text + "\n" + translation
                else:
                    subtitle.text = translation + "\n" + subtitle.text
            else:
                subtitle.text = translation
            translated_subtitles.append(subtitle)
        except Exception as e:
            error_message = str(e)
            status_text.insert(tk.END, f"\nError during translation request:\n{error_message}\n")
            messagebox.showerror("Error", f"Translation request failed: {e}")
            break

    final_translation = "\n".join(str(subtitle) for subtitle in translated_subtitles)
    save_srt_file(translated_subtitles, 'google')

def translate_gpt_api():
    api_key = read_specific_api_key('gpt')
    if not api_key:
        messagebox.showerror("Error", "API key for GPT not found.")
        return

    from_lang = from_var.get()
    to_lang = to_var.get()

    additional_prompt = additional_prompt_entry.get()

    merge_texts = merge_checkbox_var.get()
    from_on_top = from_on_top_checkbox_var.get()

    if 'subtitles' not in globals():
        messagebox.showerror("Error", "No subtitles loaded.")
        return

    client = OpenAI(api_key=api_key)
    translated_subtitles = []

    for i in range(0, len(subtitles), blocks_to_translate):
        subtitle_blocks = subtitles[i:i+blocks_to_translate]

        prompt = f"Please translate the text of this subtitle file from {from_lang} to {to_lang}. Keep the same file structure and keep in mind that you shouldn't just translate line by line, sometimes you need the whole context to translate. {additional_prompt}\n\n"
        status_text.insert(tk.END, f"\nThe prompt is :\n{prompt}\n")
        prompt += "\n".join(str(subtitle) for subtitle in subtitle_blocks)

        try:
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a translator."},
                    {"role": "user", "content": prompt}
                ]
            )
            translation = completion.choices[0].message.content.strip()
            translated_subtitles.extend(pysrt.from_string(translation))
        except Exception as e:
            error_message = str(e)
            status_text.insert(tk.END, f"\nError during translation request:\n{error_message}\n")
            messagebox.showerror("Error", f"Translation request failed: {e}")
            break

    if merge_texts:
        for i, translated_subtitle in enumerate(translated_subtitles):
            original_text = subtitles[i].text
            if from_on_top:
                translated_subtitle.text = original_text + "\n" + translated_subtitle.text
            else:
                translated_subtitle.text = translated_subtitle.text + "\n" + original_text

    save_srt_file(translated_subtitles, 'gpt')

def update_blocks_to_translate(value):
    global blocks_to_translate
    blocks_to_translate = int(value)
    status_text.insert(tk.END, f"Blocks to translate updated to: {blocks_to_translate}\n")

def enable_disable_gpt_options(*args):
    if translateEngine_var.get() == "gpt":
        blocks_menu.config(state="normal")
        additional_prompt_entry.config(state="normal")
    else:
        blocks_menu.config(state="disabled")
        additional_prompt_entry.config(state="disabled")

def createUI(root):
    file_button = tk.Button(root, text="Import .srt File", command=import_file)
    file_button.pack(pady=10)

    options_frame = tk.Frame(root)
    options_frame.pack(pady=10)

    from_label = tk.Label(options_frame, text="From:", anchor='w', width=10)
    from_label.grid(row=0, column=0, padx=5, pady=5)
    global from_var
    from_var = tk.StringVar(value="en")
    from_menu = tk.OptionMenu(options_frame, from_var, "en", "zh-Hant-TW", "fr", "sw")
    from_menu.config(width=10)
    from_menu.grid(row=0, column=1, padx=5, pady=5)

    to_label = tk.Label(options_frame, text="To:", anchor='w', width=10)
    to_label.grid(row=1, column=0, padx=5, pady=5)
    global to_var
    to_var = tk.StringVar(value="zh-Hant-TW")
    to_menu = tk.OptionMenu(options_frame, to_var, "en", "zh-Hant-TW", "fr", "sw")
    to_menu.config(width=10)
    to_menu.grid(row=1, column=1, padx=5, pady=5)

    global merge_checkbox_var
    merge_checkbox_var = tk.BooleanVar(value=True)
    merge_checkbox = tk.Checkbutton(options_frame, text="Merge both languages in output SRT", variable=merge_checkbox_var)
    merge_checkbox.grid(row=2, column=0, padx=5, pady=5)

    global from_on_top_checkbox_var
    from_on_top_checkbox_var = tk.BooleanVar(value=False)
    from_on_top_checkbox = tk.Checkbutton(options_frame, text="'From' on top", variable=from_on_top_checkbox_var)
    from_on_top_checkbox.grid(row=2, column=1, padx=5, pady=5)

    global translateEngine_var
    translateEngine_var = tk.StringVar(value="gpt")
    
    engine_label = tk.Label(options_frame, text="Translation Engine:", anchor='w', width=15)
    engine_label.grid(row=3, column=0, padx=5, pady=5)
    
    google_radio = tk.Radiobutton(options_frame, text="Google Translate API", variable=translateEngine_var, value="google")
    google_radio.grid(row=3, column=1, padx=5, pady=5)
    
    gpt_radio = tk.Radiobutton(options_frame, text="GPT-4", variable=translateEngine_var, value="gpt")
    gpt_radio.grid(row=3, column=2, padx=5, pady=5)

    translateEngine_var.trace("w", enable_disable_gpt_options)

    blocks_label = tk.Label(root, text="[GPT options] Blocks to translate:")
    blocks_label.pack(pady=5)
    
    global blocks_menu
    blocks_menu = tk.OptionMenu(root, tk.StringVar(value=str(blocks_to_translate)), "5", "10", "20", "40", command=update_blocks_to_translate)
    blocks_menu.pack(pady=5)

    additional_prompt_label = tk.Label(root, text="Additional Prompt:")
    additional_prompt_label.pack(pady=5)

    global additional_prompt_entry
    additional_prompt_entry = tk.Entry(root, width=50)
    additional_prompt_entry.pack(pady=5)

    enable_disable_gpt_options()

    translate_button = tk.Button(root, text="Translate", command=translate_srt)
    translate_button.pack(pady=20)

    status_label = tk.Label(root, text="Status:")
    status_label.pack(pady=5)
    global status_text
    status_text = tk.Text(root, height=12, width=80)
    status_text.pack(pady=10)

root = tk.Tk()
root.title("Subtitle Translator")
createUI(root)
load_api_keys()
root.mainloop()

