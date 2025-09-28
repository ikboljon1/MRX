# brain/memory_manager.py
import json
import os
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_FILE = os.path.join(_PROJECT_ROOT, 'mrx_memory.json')

def _load_memory():
    """Загружает все заметки из файла."""
    if not os.path.exists(MEMORY_FILE):
        return {'notes': []}
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_memory(data):
    """Сохраняет все заметки в файл."""
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_note(note_text, due_date=None):
    """Добавляет новую заметку."""
    memory = _load_memory()
    new_note = {
        'id': int(datetime.now().timestamp()),
        'text': note_text,
        'created_at': datetime.now().isoformat(),
        'due_date': due_date # Дата напоминания в формате ISO (YYYY-MM-DD)
    }
    memory['notes'].append(new_note)
    _save_memory(memory)
    print(f"Память: Добавлена заметка - {new_note}")

def get_upcoming_notes():
    """Возвращает заметки, о которых нужно напомнить сегодня."""
    memory = _load_memory()
    today = datetime.now().date().isoformat()
    upcoming = [note for note in memory['notes'] if note.get('due_date') == today]
    return upcoming