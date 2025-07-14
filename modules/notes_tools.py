# modules/notes_tools.py

import os

NOTES_DIR = "data/notes"

def run():
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)

    print("\n Notes Module Commands Available:")
    print("  note add <title>       - Create a new note")
    print("  note list              - List all saved notes")
    print("  note read <title>      - Read a specific note")
    print("  note delete <title>    - Delete a specific note")
    print("Type your command directly from NetAssist CLI.\n")

def add_note(title):
    note_filename = os.path.join(NOTES_DIR, f"{title}.txt")

    if os.path.exists(note_filename):
        print("\n A note with this title already exists.")
        return

    print("\nType your note content (single line). Press Enter to save.")
    content = input("> ")

    with open(note_filename, "w") as f:
        f.write(content)

    print("\n Note saved successfully.")

def list_notes():
    print("\n Saved Notes:")
    notes = os.listdir(NOTES_DIR)

    if not notes:
        print("  No notes found.")
    else:
        for note in notes:
            print(f"  - {note.replace('.txt', '')}")

def read_note(title):
    note_filename = os.path.join(NOTES_DIR, f"{title}.txt")

    if not os.path.exists(note_filename):
        print("\n Note not found.")
        return

    with open(note_filename, "r") as f:
        content = f.read()

    print("\n Note Content:")
    print("---------------------------------")
    print(content)
    print("---------------------------------")

def delete_note(title):
    note_filename = os.path.join(NOTES_DIR, f"{title}.txt")

    if not os.path.exists(note_filename):
        print("\n Note not found.")
        return

    confirm = input("\n Are you sure you want to delete this note? (y/n): ").strip().lower()

    if confirm == "y":
        os.remove(note_filename)
        print("\n Note deleted successfully.")
    else:
        print("\nAborted deletion.")
