"""
Точка входа J.A.R.V.I.S. Запускать именно этот файл: python main.py

Все остальные файлы (config.py, tts.py, ai.py, presentations.py, commands.py, gui.py и т.д.)
должны лежать в ТОЙ ЖЕ папке, что и этот main.py.
"""
import sys
import runtime_state
import memory_store
import updater

if __name__ == "__main__":
    new_version = updater.check_for_update()
    if new_version:
        print(f"[Автообновление] Найдена новая версия: {new_version} (текущая: {updater.CURRENT_VERSION}).")
        print("[Автообновление] Скачиваю обновлённые файлы...")
        if updater.download_update():
            print("[Автообновление] Готово! Перезапустите программу (python main.py), чтобы применить изменения.")
            sys.exit(0)
        else:
            print("[Автообновление] Не удалось завершить обновление, запускаю текущую версию.")

    memory_store.load_memory()
    from gui import JARVISApp
    runtime_state.app_instance = JARVISApp()
    runtime_state.app_instance.root.mainloop()