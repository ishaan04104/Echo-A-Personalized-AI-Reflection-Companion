import os
import json
from datetime import datetime
from TTS.api import TTS
import google.generativeai as genai

# === CONFIGURATION ===
USER_NAME = "Aryan"
HISTORY_FILE = "/path/"
NOTES_FILE = "/path/"
AUDIO_FILE = "/path/"

# Initialize TTS only once
TTS_MODEL = "tts_models/en/vctk/vits"
tts = TTS(model_name=TTS_MODEL)
DEFAULT_SPEAKER = tts.speakers[42]  # female, warm voice

# Gemini setup
genai.configure(api_key="################")  # Replace with your real key

# === UTILITIES ===
def load_user_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "goals": []}

def save_user_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def append_note(note):
    with open(NOTES_FILE, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{note}\n\n")

def get_streak(history):
    dates = sorted(set(item['date'] for item in history))
    today = datetime.now().strftime('%Y-%m-%d')
    return sum(1 for d in reversed(dates) if d <= today)

# === GEMINI PROMPT LOGIC ===
def build_prompt(user_name, history):
    if not history:
        return "User has no content history yet."

    current = history[-1]
    previous = history[-2] if len(history) > 1 else None

    title = current.get("title", "Unknown")
    genre = current.get("genre", "motivational")
    ctype = current.get("type", "audiobook")
    emotion = current.get("emotion", "inspired")
    language = current.get("language", "English")

    last_title = previous.get("title", "something else") if previous else "something else"
    last_genre = previous.get("genre", "another genre") if previous else "another genre"
    last_emotion = previous.get("emotion", "curious") if previous else "curious"

    streak = get_streak(history)
    progress_line = (
        f"{streak} Echo{'s' if streak > 1 else ''} done — keep the momentum going!"
        if streak <= 5 else f"You're on Echo #{streak} — this is becoming a habit!"
    )

    prompt = f"""
You are Kuku FM's friendly Echo voice, speaking directly to the user, Aryan.

They just finished a {genre} {ctype} titled \"{title}\" in {language} and felt {emotion} afterward.
Previously, they listened to \"{last_title}\" ({last_genre}, felt {last_emotion}).

Now, craft a short, voice-note-style Echo (2–4 sentences):
- Speak directly to Aryan, like a warm, thoughtful friend.
- Summarize the key message from this content.
- Reflect on how Aryan might be feeling.
- If possible, connect it to the previous Echo or learning.
- End with a personal note or reminder — something Aryan would want to save.

Encourage Aryan with this: {progress_line}
Your output should be only the Echo text, natural and spoken — no labels or formatting.
"""
    return prompt.strip()

# === ECHO GENERATION ===
def generate_echo(prompt):
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error generating echo: {e}"

# === TTS CONVERSION ===
def convert_to_audio(text, filename):
    tts.tts_to_file(text=text, speaker=DEFAULT_SPEAKER, file_path=filename)

# === MAIN LOGIC ===
def main():
    print("🎧 Echo Generator Terminal")
    user_data = load_user_history()

    if not user_data["history"]:
        print("❌ No history found. Please add a first entry to aryan.json.")
        return

    latest_entry = user_data["history"][-1]
    title = latest_entry.get("title", "Unknown")
    genre = latest_entry.get("genre", "motivational")
    ctype = latest_entry.get("type", "audiobook")

    print(f"\n📥 Using latest content: “{title}” ({genre}, {ctype})")

    prompt = build_prompt(USER_NAME, user_data["history"])
    echo = generate_echo(prompt)

    print("\n✨ Generated Echo:\n")
    print(echo)

    # Save audio
    convert_to_audio(echo, AUDIO_FILE)
    print(f"\n🔊 Echo saved as: {AUDIO_FILE}")

    # Optional note
    note = input("\n📝 Add your own reflection (optional, press Enter to skip): ").strip()
    if note:
        append_note(note)
        print("✅ Note saved.")

    # Save history again with date
    user_data["history"][-1]["date"] = datetime.now().strftime("%Y-%m-%d")
    save_user_history(user_data)

if __name__ == "__main__":
    main()
