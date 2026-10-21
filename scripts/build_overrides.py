"""Собирает translations/ru_overrides.json из текущего словаря.

Правит только те строки, где вычитка нашла системные расхождения:
  * LLM-prompt → «промпт», а не «запрос» (approval/update-prompt не трогаем);
  * сессии приложения → «сессия», но Windows/SSH-сеансы оставляем «сеанс»;
  * несколько точечных формулировок.

Запуск: py scripts/build_overrides.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import paths

OVERRIDES = os.path.join(paths.TRANSLATIONS, "ru_overrides.json")

# Точечные замены внутри строки: (что, на что).
PROMPT_REPLACEMENTS = [
    ("запрос", "промпт"),
    ("Запрос", "Промпт"),
    ("затраты на подсказки", "расход промпта"),
]

MANUAL = {
    # workbench — это не «рабочий стол»
    "工作台": "Верстак",
    # сессии приложения, а не сеансы ОС
    "工作目录与「我的」中的技能。带 / 的可以由你直接调用，其余的由模型根据任务判断是否使用。关掉一个立刻生效：从你的下一条消息起模型不再拿到它，直接点名也调不动，不用新建会话。": [
        ("новый сеанс не требуется", "новая сессия не требуется"),
    ],
    "模型自动发现已关闭：仅显式指定的技能会运行。开关立即生效，自下一条消息起，无需新建会话。": [
        ("новый сеанс не требуется", "новая сессия не требуется"),
    ],
    "下次启动时不再显示，本次仍保留": [
        ("в текущем сеансе", "в текущей сессии"),
    ],
    "给模型一个把任务交给另一个项目里会话的工具。打开就是你的总同意：派出的任务和对方的回信不再询问；新会话沿用本会话的模型和权限，不会比本会话更宽。": [
        ("сеансу", "сессии"),
        ("новый сеанс", "новая сессия"),
    ],
    "默认 0：不自动收起，打开的会话都保留。设成一个数字后，打开的会话超过它时，会收起最久没动的空闲会话；对话仍在列表里，随时可以重新打开。保留得越多，占用的内存越多。": [
        ("сеансы не сворачиваются", "сессии не сворачиваются"),
        ("все открытые сеансы сохраняются", "все открытые сессии сохраняются"),
        ("открытых сеансов", "открытых сессий"),
        ("простаивающий сеанс", "простаивающую сессию"),
        ("будет свёрнут", "будет свёрнута"),
        ("Чем больше сеансов", "Чем больше сессий"),
    ],
    "默认留空：自动。浏览器对同一个地址只开约 6 个连接，会话列表占一个，所以只让少数标签保持实时连接，其余的标签在显示时从断点接着读，运行中的后台标签每 5 秒读一次状态。调高会让更多后台标签实时更新，但开太多会让停止、发送排不上队。": [
        ("список сеансов", "список сессий"),
    ],
    # прочие точечные правки
    "请求修改设置": "Запрашивает изменение настройки",
    "每次执行操作前请求确认": "Запрашивает подтверждение перед каждым действием",
    "已记住的权限规则无法读取": "Не удалось прочитать запомненные правила разрешений",
    "该行过长，无法补全": "Эта строка слишком длинная для автодополнения",
    "两次输入的口令不一致": "Введённые пароли не совпадают",
    "思考参数": "Параметр рассуждения",
    # компактные подписи для узких элементов управления
    "进行中": "В работе",
    "置顶": "Закреп.",
    "归档": "Архив",
    "缓存命中": "Из кэша",
}


def main():
    source = common.read_json(paths.SOURCE)
    if not source:
        raise SystemExit("Нет work/source.json — сначала extract_source.py")
    ru = common.read_json(paths.RU_DICT, {})
    if not ru:
        raise SystemExit("Нет translations/ru.json — сначала merge_parts.py --write")

    overrides = {}

    # LLM-prompt: только строки, где en содержит prompt, но не approval/update.
    for row in source["rows"]:
        key = row["zh"]
        en = (row["en"] or "").lower()
        if "prompt" not in en:
            continue
        if "approval" in en or "update prompt" in en:
            continue
        value = ru.get(key, "")
        new = value
        for old, replacement in PROMPT_REPLACEMENTS:
            new = new.replace(old, replacement)
        overrides[key] = new

    for key, action in MANUAL.items():
        if isinstance(action, str):
            overrides[key] = action
            continue
        value = ru.get(key, "")
        new = value
        for old, replacement in action:
            new = new.replace(old, replacement)
        overrides[key] = new

    common.write_json(OVERRIDES, dict(sorted(overrides.items())), indent=0)
    common.log("Записано %d overrides в %s" % (len(overrides), OVERRIDES))
    for key in list(overrides)[:5]:
        common.log("  %s -> %s" % (common.short(key, 50), common.short(overrides[key], 70)))


if __name__ == "__main__":
    main()
