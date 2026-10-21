"""Русские строки для нативного слоя Electron (app.asar).

Каждый патч — точная замена, которая должна встретиться ровно один раз.
Якоря проверены на Reasonix Studio 2.47.1.
"""

UILANG_OLD = r'''  if (want === "zh" || want === "en") return want;
  return isChinese(machineLocale) ? "zh" : "en";'''

UILANG_NEW = r'''  if (want === "zh" || want === "en" || want === "ru") return want;
  if (isRussian(machineLocale)) return "ru";
  return isChinese(machineLocale) ? "zh" : "en";'''

UILANG_ADD_OLD = r'''module.exports = { uiLanguage };'''

UILANG_ADD_NEW = r'''function isRussian(tag) {
  return String(tag ?? "").toLowerCase().startsWith("ru");
}

module.exports = { uiLanguage };'''

STARTING_OLD = r'''  en: ["Reasonix Studio is starting", "Waiting for the local service to be ready. This window will close automatically."],'''

STARTING_NEW = STARTING_OLD + "\n" + r'''  ru: ["Reasonix Studio запускается", "Ожидание готовности локальной службы. Это окно закроется автоматически."],'''

STARTING_PICK_OLD = r'''  const [title, note] = String(locale).toLowerCase().startsWith("zh") ? TEXT.zh : TEXT.en;'''

STARTING_PICK_NEW = r'''  const loc = String(locale).toLowerCase();
  const [title, note] = loc.startsWith("zh") ? TEXT.zh : loc.startsWith("ru") ? TEXT.ru : TEXT.en;'''

EDITMENU_OLD = r'''  en: {
    edit: "Edit",'''

EDITMENU_NEW = r'''  ru: {
    edit: "Правка",
    undo: "Отменить",
    redo: "Повторить",
    cut: "Вырезать",
    copy: "Копировать",
    paste: "Вставить",
    selectAll: "Выделить всё",
    pasteAndMatchStyle: "Вставить и подстроить стиль",
    delete: "Удалить",
    substitutions: "Замены",
    showSubstitutions: "Показать замены",
    smartQuotes: "Умные кавычки",
    smartDashes: "Умные тире",
    textReplacement: "Замена текста",
    speech: "Диктовка",
    startSpeaking: "Начать диктовку",
    stopSpeaking: "Остановить диктовку",
  },
  en: {
    edit: "Edit",'''

HOSTEXIT_OLD = r'''  return {
    message: "The kernel exited unexpectedly last time",'''

HOSTEXIT_NEW = r'''  if (String(locale).toLowerCase().startsWith("ru")) {
    return {
      message: "В прошлый раз ядро неожиданно завершилось",
      ok: "ОК",
      detail: `Процесс ядра остановился во время прошлой сессии (${how}). Ваши сессии не затронуты. Чтобы сообщить о проблеме, приложите shell.log, host.log и папку crash из:\n\n${logsDir}`,
    };
  }
  return {
    message: "The kernel exited unexpectedly last time",'''

SHELLLOG_OLD = r'''const HINTS = {
  timeout: [
    "The kernel started but did not finish starting in time. Security software scanning a new or updated install is a common cause; starting Studio again usually works.",
    "内核已启动，但没有在限定时间内完成启动。安全软件扫描新安装或刚更新的程序是常见原因；再次启动通常可以。",
  ],
  exited: [
    "The kernel process stopped before it was ready. Anything it printed is above; host.log has the rest.",
    "内核进程在就绪前就停止了。它输出过的内容在上面，host.log 里有更多。",
  ],
  spawn: [
    "The kernel program could not be run. Security software blocking or locking it is a common cause.",
    "无法运行内核程序。安全软件拦截或占用它是常见原因。",
  ],
};'''

SHELLLOG_NEW = r'''const HINTS = {
  timeout: [
    "The kernel started but did not finish starting in time. Security software scanning a new or updated install is a common cause; starting Studio again usually works.",
    "内核已启动，但没有在限定时间内完成启动。安全软件扫描新安装或刚更新的程序是常见原因；再次启动通常可以。",
    "Ядро запустилось, но не успело завершить запуск. Обычно причина — антивирус, сканирующий новую или обновлённую установку; повторный запуск Studio обычно помогает.",
  ],
  exited: [
    "The kernel process stopped before it was ready. Anything it printed is above; host.log has the rest.",
    "内核进程在就绪前就停止了。它输出过的内容在上面，host.log 里有更多。",
    "Процесс ядра остановился до готовности. Всё, что он вывел, показано выше; остальное — в host.log.",
  ],
  spawn: [
    "The kernel program could not be run. Security software blocking or locking it is a common cause.",
    "无法运行内核程序。安全软件拦截或占用它是常见原因。",
    "Не удалось запустить программу ядра. Обычно причина — антивирус, блокирующий или удерживающий её.",
  ],
};'''

SHELLLOG_PICK_OLD = r'''  const zh = String(locale).toLowerCase().startsWith("zh");
  const hint = HINTS[code]?.[zh ? 1 : 0];
  const body = hint ? `${reason}\n\n${hint}` : reason;
  if (zh) {
    return { title: "Reasonix Studio 无法启动", detail: `${body}\n\n日志位于：\n${logDir}` };
  }'''

SHELLLOG_PICK_NEW = r'''  const loc = String(locale).toLowerCase();
  const zh = loc.startsWith("zh");
  const ru = loc.startsWith("ru");
  const hint = HINTS[code]?.[zh ? 1 : ru ? 2 : 0];
  const body = hint ? `${reason}\n\n${hint}` : reason;
  if (zh) {
    return { title: "Reasonix Studio 无法启动", detail: `${body}\n\n日志位于：\n${logDir}` };
  }
  if (ru) {
    return { title: "Reasonix Studio не удалось запустить", detail: `${body}\n\nЖурналы находятся в:\n${logDir}` };
  }'''

PACKAGEGRANTS_OLD = r'''  return {
    title: "Reasonix Studio could not open its window",'''

PACKAGEGRANTS_NEW = r'''  if (String(locale).toLowerCase().startsWith("ru")) {
    return {
      title: "Reasonix Studio не удалось открыть окно",
      detail:
        "Файлы, загружаемые Reasonix Studio, содержат записи доступа, привязывающие их к конкретному пакету приложения Windows (AppContainer), " +
        "и изолированные процессы Chromium завершаются при загрузке такого файла. Studio попыталась удалить их, но получила отказ для:\n\n" +
        shown + (more > 0 ? `\n…и ещё ${more}` : "") +
        "\n\nЗапустите Reasonix Studio один раз от имени администратора — она удалит их сама.",
    };
  }
  return {
    title: "Reasonix Studio could not open its window",'''

MAIN_OLD = r'''        buttons: ["移到废纸篓", "先留着"],
        defaultId: 0,
        cancelId: 1,
        message: "找到一个旧版本的 Reasonix Studio",
        detail: `${bundle}\n\n它和当前这个共用同一份数据，所以两个图标打开的是同一个窗口。移到废纸篓不会动你的会话和设置。`,'''

MAIN_NEW = r'''        buttons: String(app.getLocale()).toLowerCase().startsWith("ru") ? ["Переместить в корзину", "Оставить"] : ["移到废纸篓", "先留着"],
        defaultId: 0,
        cancelId: 1,
        message: String(app.getLocale()).toLowerCase().startsWith("ru") ? "Найдена старая версия Reasonix Studio" : "找到一个旧版本的 Reasonix Studio",
        detail: String(app.getLocale()).toLowerCase().startsWith("ru") ? `${bundle}\n\nОна использует те же данные, что и текущая, поэтому оба значка открывают одно и то же окно. Перемещение в корзину не затронет ваши сессии и настройки.` : `${bundle}\n\n它和当前这个共用同一份数据，所以两个图标打开的是同一个窗口。移到废纸篓不会动你的会话和设置。`,'''

TRAY_OLD = r'''    const line = state.fold?.line ?? "";
    const words = state.fold?.labels ?? {};'''

TRAY_NEW = r'''    const fold = state.fold ?? {};
    const bits = [];
    if (fold.attention > 0) bits.push(`${fold.attention} в ожидании`);
    if (fold.working > 0) bits.push(`${fold.working} в работе`);
    if (fold.jobs > 0) bits.push(`${fold.jobs} в фоне`);
    const line = bits.length ? bits.join(" · ") : "Ничего не выполняется";
    const words = {
      open: "Открыть Reasonix Studio",
      closeToTray: "Продолжать в фоне при закрытии",
      quit: "Выйти из Reasonix",
    };'''

PATCHES = [
    {
        "file": "uilang.js",
        "reps": [
            ("lang", UILANG_OLD, UILANG_NEW),
            ("isRussian", UILANG_ADD_OLD, UILANG_ADD_NEW),
        ],
    },
    {
        "file": "starting.js",
        "reps": [
            ("text", STARTING_OLD, STARTING_NEW),
            ("pick", STARTING_PICK_OLD, STARTING_PICK_NEW),
        ],
    },
    {
        "file": "editmenu.js",
        "reps": [("ru-block", EDITMENU_OLD, EDITMENU_NEW)],
    },
    {
        "file": "hostexit.js",
        "reps": [("ru", HOSTEXIT_OLD, HOSTEXIT_NEW)],
    },
    {
        "file": "shelllog.js",
        "reps": [
            ("hints", SHELLLOG_OLD, SHELLLOG_NEW),
            ("pick", SHELLLOG_PICK_OLD, SHELLLOG_PICK_NEW),
        ],
    },
    {
        "file": "packagegrants.js",
        "reps": [("ru", PACKAGEGRANTS_OLD, PACKAGEGRANTS_NEW)],
    },
    {
        "file": "main.js",
        "reps": [("legacy", MAIN_OLD, MAIN_NEW)],
    },
    {
        "file": "tray.js",
        "reps": [("ru-labels", TRAY_OLD, TRAY_NEW)],
    },
]
