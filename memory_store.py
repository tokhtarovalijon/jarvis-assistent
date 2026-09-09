"""
Постоянная память между сессиями: история учебных вопросов и решённых задач,
сохраняется в JSON-файл и восстанавливается при следующем запуске программы.

ВАЖНО: другие модули должны делать `import memory_store` и обращаться через
`memory_store.study_history`, `memory_store.last_saved_question` и т.д. — а не
`from memory_store import study_history`, иначе изменения не будут видны между модулями.
"""
import os
import json

# --- ПАМЯТЬ ДИАЛОГА ДЛЯ РЕЖИМА УЧЁБЫ ---
study_history = []
problem_history = []
last_saved_question = ""
last_saved_answer = ""

MEMORY_FILE = "память_джарвиса.json"


def load_memory():
    """Загружает историю учёбы и решения задач из файла при запуске программы."""
    global study_history, problem_history
    if not os.path.exists(MEMORY_FILE):
        return
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        study_history[:] = data.get("study_history", [])
        problem_history[:] = data.get("problem_history", [])
        print(f"[Память] Загружено {len(study_history)} записей учёбы, {len(problem_history)} записей задач.")
    except Exception as e:
        print(f"[Ошибка загрузки памяти] {e}")


def save_memory():
    """Сохраняет текущую историю учёбы и решения задач в файл."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"study_history": study_history, "problem_history": problem_history},
                f, ensure_ascii=False, indent=2,
            )
    except Exception as e:
        print(f"[Ошибка сохранения памяти] {e}")
