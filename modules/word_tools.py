import requests
from datetime import datetime

def run():
    try:
        print("\nRetrieving today's word...")

        word, definition, part_of_speech, example = get_word_of_the_day()

        print("\nWord of the Day:")
        print(f"  Word           : {word}")
        print(f"  Part of Speech : {part_of_speech}")
        print(f"  Definition     : {definition}")
        if example:
            print(f"  Example        : {example}")

        print("\nDate:", datetime.now().strftime("%A, %B %d, %Y"))

    except Exception as e:
        print(f"Error fetching word of the day: {e}")

def get_word_of_the_day():
    # This uses Wordnik's public API (you'll need to replace 'YOUR_API_KEY')
    api_key = "YOUR_API_KEY"
    url = f"https://api.wordnik.com/v4/words.json/wordOfTheDay?api_key={api_key}"

    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    word = data.get("word", "(unknown)")
    definitions = data.get("definitions", [])
    examples = data.get("examples", [])

    definition = definitions[0].get("text", "No definition available.") if definitions else "No definition available."
    part = definitions[0].get("partOfSpeech", "unknown") if definitions else "unknown"
    example = examples[0].get("text", "") if examples else ""

    return word, definition, part, example
