import os
import re
import uuid

# -----------------------------
# ТРЕБОВАНИЕ: в имени файла только A-Z a-z 0-9 и "_"
# Расширение сохраняем (например .wav)
# Режим: рекурсивно + безопасно (2 прохода) + уникализация при коллизиях
# -----------------------------

# Словарь транслитерации RU -> EN
translit_dict = {
    'А':'A','а':'a','Б':'B','б':'b','В':'V','в':'v','Г':'G','г':'g',
    'Д':'D','д':'d','Е':'E','е':'e','Ё':'E','ё':'e','Ж':'Zh','ж':'zh',
    'З':'Z','з':'z','И':'I','и':'i','Й':'I','й':'i','К':'K','к':'k',
    'Л':'L','л':'l','М':'M','м':'m','Н':'N','н':'n','О':'O','о':'o',
    'П':'P','п':'p','Р':'R','р':'r','С':'S','с':'s','Т':'T','т':'t',
    'У':'U','у':'u','Ф':'F','ф':'f','Х':'Kh','х':'kh','Ц':'Ts','ц':'ts',
    'Ч':'Ch','ч':'ch','Ш':'Sh','ш':'sh','Щ':'Shch','щ':'shch',
    'Ы':'Y','ы':'y','Э':'E','э':'e','Ю':'Yu','ю':'yu','Я':'Ya','я':'ya',
    'Ь':'','ь':'','Ъ':'','ъ':''
}

def translit_and_rough_clean(s: str) -> str:
    """
    Транслит RU->EN + любое "непонятное" превращаем в "_".
    """
    out = []
    for ch in s:
        if ch in translit_dict:
            out.append(translit_dict[ch])
        elif ch.isalnum():
            # латиница/цифры оставляем как есть
            out.append(ch)
        elif ch in (" ", "-", ".", ","):
            out.append("_")
        else:
            # любой мусор (ღ, эмодзи, спецсимволы) -> "_"
            out.append("_")
    return "".join(out)

def sanitize_filename(filename: str) -> str:
    """
    Делает имя файла строго: base=[A-Za-z0-9_]+, расширение сохраняем.
    """
    base, ext = os.path.splitext(filename)

    # 1) транслит + грубая очистка
    base = translit_and_rough_clean(base)

    # 2) оставить строго только [A-Za-z0-9_]
    base = re.sub(r"[^A-Za-z0-9_]", "_", base)

    # 3) схлопнуть "__" в "_" и обрезать "_" по краям
    base = re.sub(r"_+", "_", base).strip("_")

    if not base:
        base = "file"

    # на всякий случай чистим расширение (обычно .wav)
    ext = re.sub(r"[^A-Za-z0-9.]", "", ext)
    if ext and not ext.startswith("."):
        ext = "." + ext

    return base + ext

def make_unique_path(path: str) -> str:
    """
    Если целевое имя уже существует — добавляем _1, _2, ...
    """
    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{base}_{i}{ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1

def iter_files_recursive(root: str):
    """
    Рекурсивно выдаёт (dirpath, filename) для всех файлов.
    """
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            yield dirpath, fn

def main():
    # Папка с файлами (Windows: лучше raw string)
    folder_path = r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\Похожие_на_позитив_Афина_слова_НЕГАТИВЫ"
    folder_path = os.path.abspath(folder_path)

    # 1) Составляем план переименований
    plan = []
    for dirpath, filename in iter_files_recursive(folder_path):
        old_path = os.path.join(dirpath, filename)

        new_name = sanitize_filename(filename)
        new_path = os.path.join(dirpath, new_name)

        if old_path != new_path:
            plan.append((old_path, new_path, filename, new_name))

    if not plan:
        print("Нет файлов для переименования.")
        return

    # 2) Переименование в временные имена (избавляет от цепных конфликтов)
    tmp_map = []
    for old_path, new_path, old_name, new_name in plan:
        tmp_path = old_path + f".__tmp__{uuid.uuid4().hex}"
        try:
            os.rename(old_path, tmp_path)
            tmp_map.append((tmp_path, new_path, old_name, new_name))
        except FileNotFoundError:
            print(f"Файл не найден, пропущен: {old_path}")
        except PermissionError:
            print(f"Нет доступа (возможно файл открыт), пропущен: {old_path}")
        except OSError as e:
            print(f"Ошибка при временном переименовании {old_path}: {e}")

    # 3) Финальное переименование + уникализация при коллизиях
    for tmp_path, final_path, old_name, new_name in tmp_map:
        safe_final = make_unique_path(final_path)
        try:
            os.rename(tmp_path, safe_final)
            print(f"{old_name} -> {os.path.basename(safe_final)}")
            if safe_final != final_path:
                print(f"  (коллизия: {os.path.basename(final_path)} уже существовал, сохранил как {os.path.basename(safe_final)})")
        except PermissionError:
            print(f"Нет доступа (возможно файл открыт), пропущен: {tmp_path}")
        except OSError as e:
            print(f"Ошибка при финальном переименовании {tmp_path} -> {safe_final}: {e}")

if __name__ == "__main__":
    main()
