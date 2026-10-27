"""Перевод каталога интерфейса (китайский → русский) через DeepSeek API.

Читает work/source.json, пишет части в work/ru_parts/*.json.
Каждая часть — объект {"<китайский ключ>": "<русский текст>"}.
Скрипт можно останавливать и запускать снова: готовые части пропускаются,
недостающие строки досчитываются.

Ключ берётся из переменной DEEPSEEK_API_KEY или из %APPDATA%\\reasonix\\.env.

Примеры:
  py scripts/translate_api.py --limit 10 --batch 5 --workers 1
  py scripts/translate_api.py --workers 4
  py scripts/translate_api.py --model deepseek-flash --workers 6
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths

API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-pro"
TARGET_LANGUAGE = "Russian"
PARTS = paths.PARTS
CJK = re.compile(r"[\u4e00-\u9fff]")
FULLWIDTH = re.compile(r"[（）「」『』、，。：；！？…—·]")

GLOSSARY = """
Reasonix, Reasonix Studio, DeepSeek, Claude, Gemini, OpenAI, GitHub, VS Code, Windows, macOS, Linux — do not translate.
kernel = ядро; host = хост; workspace = рабочая область; workbench = верстак; session = сессия; chat = чат;
conversation = беседа; message = сообщение; agent = агент; subagent = субагент; tool = инструмент;
trajectory = траектория; checkpoint = контрольная точка; compaction = сжатие; context = контекст;
prompt = запрос; token = токен; model = модель; provider = провайдер; queue = очередь; job = задача;
schedule = расписание; permission = разрешение; approval = подтверждение; sandbox = песочница;
memory = память; knowledge = знания; marketplace = маркетплейс; extension = расширение; skill = навык;
persona = персона; inbox = входящие; notice = уведомление; usage = использование; storage = хранилище;
metrics = метрики; graph = граф; reasoning = рассуждение; thinking = размышление; streaming = потоковая передача;
fallback = резервный вариант; override = переопределить; toggle = переключатель; checkbox = флажок;
dropdown = раскрывающийся список; sidebar = боковая панель; toolbar = панель инструментов; tab = вкладка;
tray = трей; notification = уведомление; attachment = вложение; voice input = голосовой ввод; dictation = диктовка;
workspace lease = резервирование рабочей области; surface = интерфейс; composition = композиция;
branch = ветка; commit = коммит; merge = слияние; repository = репозиторий; build = сборка; release = выпуск;
proxy = прокси; gateway = шлюз; endpoint = эндпоинт; relay = ретранслятор; vendor = производитель;
subscription = подписка; plan = тариф; quota = квота; balance = баланс; invoice = счёт; trial = пробный период;
shortcut = сочетание клавиш; hotkey = горячая клавиша; clipboard = буфер обмена; tooltip = подсказка;
modal = модальное окно; dialog = диалог; context menu = контекстное меню; status bar = строка состояния;
placeholder = подсказка; badge = значок; header = заголовок; filter = фильтр; sort = сортировка;
query = запрос; result = результат; highlight = выделение; archive = архивировать; pin = закрепить;
favorite = избранное; share = поделиться; export = экспорт; import = импорт; download = скачать;
upload = загрузить; sync = синхронизировать; refresh = обновить; reload = перезагрузить; restart = перезапустить;
retry = повторить; skip = пропустить; approve = одобрить; deny = отклонить; allow = разрешить;
block = заблокировать; enable = включить; disable = отключить; install = установить; uninstall = удалить;
upgrade = обновить; downgrade = откатить; restore = восстановить; backup = резервная копия; trash = корзина.
""".strip()

SYSTEM = f"""You are a professional localizer of desktop software. Translate interface strings from Chinese into Russian.

For every numbered item you receive the Chinese source and, when available, an English reference. Translate the meaning, not the English wording. The English reference is there to disambiguate short Chinese labels.

STRICT RULES
1. Output natural, concise Russian suitable for a desktop application UI.
2. Keep every placeholder exactly as written: {{n}}, {{name}}, {{model}}, {{count}}, {{text}} and so on. Do not rename, translate, remove, or add braces.
3. Keep product names, protocol names, code identifiers, file names, paths, URLs, keyboard keys (Ctrl, Esc, Tab, Enter), and shortcuts unchanged.
4. Use Russian quotation marks « ». Keep the source's trailing punctuation style. Use … when the source uses an ellipsis.
5. Buttons and menu items: infinitive or noun, no trailing period. Sentences: neutral tone, lowercase «вы», avoid gendered forms where possible.
6. Do not add explanations, comments, numbering, or extra strings. Do not merge or split items.
7. If an item is only a symbol or a product name, return it unchanged.
8. Return ONLY a JSON object {{"t": ["...", "..."]}} with exactly one translation per input item, in the same order.

GLOSSARY
{GLOSSARY}
"""


def system_for(target, glossary):
    return SYSTEM.replace("into Russian", "into %s" % target).replace(GLOSSARY, glossary)



def load_key():
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    env_file = os.path.join(
        os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming"),
        "reasonix",
        ".env",
    )
    if os.path.isfile(env_file):
        for line in open(env_file, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY"):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        raise SystemExit(
            "Не найден ключ DeepSeek. Задайте DEEPSEEK_API_KEY или добавьте его в "
            + env_file
        )
    return key


def needs_translation(row):
    return common.needs_translation(row["zh"])


def prompt_line(index, row):
    def one(value):
        return (value or "").replace("\r", " ").replace("\n", "\\n")

    line = "%d. zh=%s" % (index, one(row["zh"]))
    if row.get("en"):
        line += "  |  en=%s" % one(row["en"])
    elif row.get("fr"):
        line += "  |  fr=%s" % one(row["fr"])
    return line


def parse_response(content, expected):
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    obj = json.loads(text)
    if isinstance(obj, list):
        items = obj
    elif isinstance(obj, dict):
        items = None
        for key in ("t", "translations", "ru", "items", "data"):
            value = obj.get(key)
            if isinstance(value, list):
                items = value
                break
        if items is None:
            # {"1": "...", "2": "..."}
            numbered = [(k, v) for k, v in obj.items() if str(k).isdigit() and isinstance(v, str)]
            if len(numbered) == expected:
                numbered.sort(key=lambda kv: int(kv[0]))
                items = [v for _, v in numbered]
    else:
        items = None
    if not isinstance(items, list) or len(items) != expected:
        raise ValueError(
            "ожидался массив из %d переводов, получено %s"
            % (expected, len(items) if isinstance(items, list) else type(items).__name__)
        )
    return [str(x) for x in items]


def call_api(key, model, rows, timeout=180):
    lines = [prompt_line(i, row) for i, row in enumerate(rows, 1)]
    user = "Translate these %d interface strings into %s:\n%s" % (len(rows), TARGET_LANGUAGE, "\n".join(lines))
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"},
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        payload = json.load(response)
    content = payload["choices"][0]["message"]["content"]
    usage = payload.get("usage", {}) or {}
    return parse_response(content, len(rows)), usage


def translate_rows(key, model, rows, attempts=4):
    """Возвращает список переводов; None — если строку перевести не удалось."""
    if not rows:
        return []
    last_error = None
    for attempt in range(attempts):
        try:
            result, usage = call_api(key, model, rows)
            # Плейсхолдеры обязаны совпасть; иначе просим модель ещё раз.
            broken = []
            for row, translated in zip(rows, result):
                problems = common.placeholder_problems(row["zh"], translated)
                if problems:
                    broken.append((row["zh"], translated, problems))
            if not broken:
                return result, usage
            last_error = ValueError(
                "плейсхолдеры не совпали: "
                + "; ".join(common.short(z) + " -> " + ", ".join(p) for z, _, p in broken[:3])
            )
        except Exception as error:  # noqa: BLE001
            last_error = error
        if attempt + 1 < attempts:
            time.sleep(1.5 * (attempt + 1))
    if len(rows) > 1:
        middle = len(rows) // 2
        left, u1 = translate_rows(key, model, rows[:middle], attempts)
        right, u2 = translate_rows(key, model, rows[middle:], attempts)
        return left + right, _merge_usage(u1, u2)
    common.log("  !! строка не переведена: %s (%s)" % (common.short(rows[0]["zh"], 70), last_error))
    return [None], {}


def _merge_usage(a, b):
    a = a or {}
    b = b or {}
    return {
        "prompt_tokens": a.get("prompt_tokens", 0) + b.get("prompt_tokens", 0),
        "completion_tokens": a.get("completion_tokens", 0) + b.get("completion_tokens", 0),
    }


def load_done():
    done = {}
    if not os.path.isdir(PARTS):
        return done
    for name in sorted(os.listdir(PARTS)):
        if not name.startswith("part_") or not name.endswith(".json"):
            continue
        data = common.read_json(os.path.join(PARTS, name), {})
        if isinstance(data, dict):
            for zh, ru in data.items():
                if isinstance(ru, str) and ru:
                    done[zh] = ru
    return done


def write_part(start, mapping):
    if not mapping:
        return
    path = os.path.join(PARTS, "part_%05d.json" % start)
    existing = common.read_json(path, {})
    if not isinstance(existing, dict):
        existing = {}
    existing.update(mapping)
    common.write_json(path, dict(sorted(existing.items())), indent=0)


def main(argv=None):
    global SYSTEM, PARTS, TARGET_LANGUAGE
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="ru", help="код языка из languages/<code>.json")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch", type=int, default=25)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0, help="перевести не более N строк (для проверки)")
    args = parser.parse_args(argv)

    paths.ensure_work()
    profile = paths.load_profile(args.lang)
    TARGET_LANGUAGE = profile.get("target_language") or "Russian"
    glossary = profile.get("glossary") or "Keep product names, code identifiers and placeholders unchanged."
    SYSTEM = system_for(TARGET_LANGUAGE, glossary)
    PARTS = paths.parts_dir(profile["code"])
    os.makedirs(PARTS, exist_ok=True)
    common.log("Язык: %s (%s)" % (profile["display"], profile["code"]))
    data = common.read_json(paths.SOURCE)
    if not data:
        raise SystemExit("Нет %s — сначала запустите scripts/extract_source.py" % paths.SOURCE)
    rows = data["rows"]

    key = load_key()
    done = load_done()

    # Строки без китайского текста и без полноширинной пунктуации переводить
    # не нужно: это латиница, идентификаторы и символы.
    passthrough = {}
    pending = []
    for row in rows:
        if not needs_translation(row):
            passthrough[row["zh"]] = row["zh"]
        elif row["zh"] not in done:
            pending.append(row)

    common.log("Модель: %s" % args.model)
    common.log("Всего строк: %d" % len(rows))
    common.log("Уже переведено: %d" % len([r for r in rows if r["zh"] in done]))
    common.log("Без перевода (латиница/символы): %d" % len(passthrough))
    common.log("Осталось перевести: %d" % len(pending))
    if args.limit:
        pending = pending[: args.limit]
        common.log("Ограничение: %d" % len(pending))
    if not pending:
        common.log("Нечего переводить.")
        return

    batches = []
    for start in range(0, len(pending), args.batch):
        batches.append((start, pending[start : start + args.batch]))

    lock = threading.Lock()
    stats = {"done": 0, "failed": 0, "in": 0, "out": 0, "batches": 0}
    started = time.time()

    def worker(item):
        start, chunk = item
        # Часть могла быть дополнена другим запуском.
        missing = [row for row in chunk if row["zh"] not in done]
        if not missing:
            return
        result, usage = translate_rows(key, args.model, missing)
        mapping = {}
        for row, translated in zip(missing, result):
            if translated is not None and translated != "":
                mapping[row["zh"]] = translated
        if mapping:
            write_part(start, mapping)
        with lock:
            stats["done"] += len(mapping)
            stats["failed"] += len(missing) - len(mapping)
            stats["in"] += (usage or {}).get("prompt_tokens", 0)
            stats["out"] += (usage or {}).get("completion_tokens", 0)
            stats["batches"] += 1
            if stats["batches"] % 5 == 0 or stats["done"] + stats["failed"] >= len(pending):
                elapsed = time.time() - started
                common.log(
                    "  %d/%d строк, ошибок %d, ~%.0f с, токены %d/%d"
                    % (
                        stats["done"],
                        len(pending),
                        stats["failed"],
                        elapsed,
                        stats["in"],
                        stats["out"],
                    )
                )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        list(pool.map(worker, batches))

    common.log("")
    common.log("Готово. Переведено: %d, ошибок: %d" % (stats["done"], stats["failed"]))
    common.log("Токены: вход %d, выход %d" % (stats["in"], stats["out"]))
    if stats["failed"]:
        common.log("Повторите запуск, чтобы досчитать неудачные строки.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
