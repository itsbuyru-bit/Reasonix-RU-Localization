"""Сборка нативных патчей app.asar из языкового профиля.

Новому языку не нужно писать Python: достаточно заполнить поля `native`
в `languages/<code>.json` и выполнить `py scripts/build_native_patches.py --lang <code>`.
Готовые блоки сохраняются в профиле как `native_patches`.
"""
import json

# Исходные английские/китайские якоря Reasonix Studio. Они одинаковы для всех языков.
UILANG_OLD = r'''  if (want === "zh" || want === "en") return want;
  return isChinese(machineLocale) ? "zh" : "en";'''

UILANG_ADD_OLD = r'''module.exports = { uiLanguage };'''

STARTING_OLD = r'''  en: ["Reasonix Studio is starting", "Waiting for the local service to be ready. This window will close automatically."],'''

STARTING_PICK_OLD = r'''  const [title, note] = String(locale).toLowerCase().startsWith("zh") ? TEXT.zh : TEXT.en;'''

EDITMENU_OLD = r'''  en: {
    edit: "Edit",'''

HOSTEXIT_OLD = r'''  return {
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

SHELLLOG_PICK_OLD = r'''  const zh = String(locale).toLowerCase().startsWith("zh");
  const hint = HINTS[code]?.[zh ? 1 : 0];
  const body = hint ? `${reason}\n\n${hint}` : reason;
  if (zh) {
    return { title: "Reasonix Studio 无法启动", detail: `${body}\n\n日志位于：\n${logDir}` };
  }'''

PACKAGEGRANTS_OLD = r'''  return {
    title: "Reasonix Studio could not open its window",'''

MAIN_OLD = r'''        buttons: ["移到废纸篓", "先留着"],
        defaultId: 0,
        cancelId: 1,
        message: "找到一个旧版本的 Reasonix Studio",
        detail: `${bundle}\n\n它和当前这个共用同一份数据，所以两个图标打开的是同一个窗口。移到废纸篓不会动你的会话和设置。`,'''

TRAY_OLD = r'''    const line = state.fold?.line ?? "";
    const words = state.fold?.labels ?? {};'''

EDIT_ORDER = [
    "edit", "undo", "redo", "cut", "copy", "paste", "selectAll",
    "pasteAndMatchStyle", "delete", "substitutions", "showSubstitutions",
    "smartQuotes", "smartDashes", "textReplacement", "speech",
    "startSpeaking", "stopSpeaking",
]


def js(value):
    return json.dumps(value, ensure_ascii=False)


def tmpl(value, variables):
    """JS template literal: {name} -> ${expr}; literal backticks/newlines escaped."""
    escaped = value.replace("\\", "\\\\").replace("`", "\\`")
    escaped = escaped.replace("\n", "\\n")
    for name, expr in variables.items():
        escaped = escaped.replace("{" + name + "}", "${" + expr + "}")
    return "`" + escaped + "`"


def build(profile):
    code = profile["code"]
    native = profile["native"]
    checker = native["uilang"]["checker"]
    code_js = js(code)

    uilang_new = (
        '  if (want === "zh" || want === "en" || want === %s) return want;\n'
        '  if (%s(machineLocale)) return %s;\n'
        '  return isChinese(machineLocale) ? "zh" : "en";' % (code_js, checker, code_js)
    )
    uilang_add_new = (
        'function %s(tag) {\n'
        '  return String(tag ?? "").toLowerCase().startsWith(%s);\n'
        '}\n\n'
        'module.exports = { uiLanguage };' % (checker, code_js)
    )

    starting_new = (
        STARTING_OLD + "\n  %s: [%s, %s]," % (
            code_js, js(native["starting"]["title"]), js(native["starting"]["note"])
        )
    )
    starting_pick_new = (
        '  const loc = String(locale).toLowerCase();\n'
        '  const [title, note] = loc.startsWith("zh") ? TEXT.zh : loc.startsWith(%s) ? TEXT[%s] : TEXT.en;'
        % (code_js, code_js)
    )

    edit_lines = ["  %s: {" % code_js]
    for key in EDIT_ORDER:
        edit_lines.append("    %s: %s," % (key, js(native["edit_menu"][key])))
    edit_lines.append("  },")
    edit_lines.append(EDITMENU_OLD)
    editmenu_new = "\n".join(edit_lines)

    host = native["hostexit"]
    hostexit_new = (
        '  if (String(locale).toLowerCase().startsWith(%s)) {\n'
        '    return {\n'
        '      message: %s,\n'
        '      ok: %s,\n'
        '      detail: %s,\n'
        '    };\n'
        '  }\n'
        % (code_js, js(host["message"]), js(host["ok"]),
           tmpl(host["detail"], {"how": "how", "logsDir": "logsDir"}))
        + HOSTEXIT_OLD
    )

    shell = native["shelllog"]
    shelllog_new = (
        SHELLLOG_OLD.replace(
            '  ],\n};',
            '    %s,\n  ],\n};' % js(shell["hints"]["spawn"]),
        )
    )
    # Проще собрать HINTS заново, чтобы не зависеть от точного хвоста якоря.
    shelllog_new = """const HINTS = {
  timeout: [
    "The kernel started but did not finish starting in time. Security software scanning a new or updated install is a common cause; starting Studio again usually works.",
    "内核已启动，但没有在限定时间内完成启动。安全软件扫描新安装或刚更新的程序是常见原因；再次启动通常可以。",
    %s,
  ],
  exited: [
    "The kernel process stopped before it was ready. Anything it printed is above; host.log has the rest.",
    "内核进程在就绪前就停止了。它输出过的内容在上面，host.log 里有更多。",
    %s,
  ],
  spawn: [
    "The kernel program could not be run. Security software blocking or locking it is a common cause.",
    "无法运行内核程序。安全软件拦截或占用它是常见原因。",
    %s,
  ],
};""" % (
        js(shell["hints"]["timeout"]),
        js(shell["hints"]["exited"]),
        js(shell["hints"]["spawn"]),
    )
    shelllog_pick_new = (
        '  const loc = String(locale).toLowerCase();\n'
        '  const zh = loc.startsWith("zh");\n'
        '  const target = loc.startsWith(%s);\n'
        '  const hint = HINTS[code]?.[zh ? 1 : target ? 2 : 0];\n'
        '  const body = hint ? `${reason}\\n\\n${hint}` : reason;\n'
        '  if (zh) {\n'
        '    return { title: "Reasonix Studio 无法启动", detail: `${body}\\n\\n日志位于：\\n${logDir}` };\n'
        '  }\n'
        '  if (target) {\n'
        '    return { title: %s, detail: %s };\n'
        '  }'
        % (code_js, js(shell["title"]), tmpl(shell["detail"], {"body": "body", "logDir": "logDir"}))
    )

    grants = native["packagegrants"]
    packagegrants_new = (
        '  if (String(locale).toLowerCase().startsWith(%s)) {\n'
        '    return {\n'
        '      title: %s,\n'
        '      detail:\n'
        '        %s +\n'
        '        shown + (more > 0 ? %s : "") +\n'
        '        %s,\n'
        '    };\n'
        '  }\n'
        % (
            code_js,
            js(grants["title"]),
            js(grants["detail_before"]),
            tmpl(grants["detail_more"], {"more": "more"}),
            js(grants["detail_after"]),
        )
        + PACKAGEGRANTS_OLD
    )

    legacy = native["legacy"]
    buttons = ", ".join(js(x) for x in legacy["buttons"])
    legacy_detail = tmpl(legacy["detail"], {"bundle": "bundle"})
    main_new = (
        '        buttons: String(app.getLocale()).toLowerCase().startsWith(%s) ? [%s] : ["移到废纸篓", "先留着"],\n'
        '        defaultId: 0,\n'
        '        cancelId: 1,\n'
        '        message: String(app.getLocale()).toLowerCase().startsWith(%s) ? %s : "找到一个旧版本的 Reasonix Studio",\n'
        '        detail: String(app.getLocale()).toLowerCase().startsWith(%s) ? %s : `${bundle}\\n\\n它和当前这个共用同一份数据，所以两个图标打开的是同一个窗口。移到废纸篓不会动你的会话和设置。`,'
        % (code_js, buttons, code_js, js(legacy["message"]), code_js, legacy_detail)
    )

    tray = native["tray"]
    tray_new = (
        '    const fold = state.fold ?? {};\n'
        '    const bits = [];\n'
        '    if (fold.attention > 0) bits.push(%s);\n'
        '    if (fold.working > 0) bits.push(%s);\n'
        '    if (fold.jobs > 0) bits.push(%s);\n'
        '    const line = bits.length ? bits.join(" · ") : %s;\n'
        '    const words = {\n'
        '      open: %s,\n'
        '      closeToTray: %s,\n'
        '      quit: %s,\n'
        '    };'
        % (
            tmpl(tray["attention"], {"n": "fold.attention"}),
            tmpl(tray["working"], {"n": "fold.working"}),
            tmpl(tray["jobs"], {"n": "fold.jobs"}),
            js(tray["idle"]),
            js(tray["open"]),
            js(tray["closeToTray"]),
            js(tray["quit"]),
        )
    )

    return [
        {"file": "uilang.js", "reps": [("lang", UILANG_OLD, uilang_new),
                                       ("checker", UILANG_ADD_OLD, uilang_add_new)]},
        {"file": "starting.js", "reps": [("text", STARTING_OLD, starting_new),
                                         ("pick", STARTING_PICK_OLD, starting_pick_new)]},
        {"file": "editmenu.js", "reps": [("edit-block", EDITMENU_OLD, editmenu_new)]},
        {"file": "hostexit.js", "reps": [("ru", HOSTEXIT_OLD, hostexit_new)]},
        {"file": "shelllog.js", "reps": [("hints", SHELLLOG_OLD, shelllog_new),
                                         ("pick", SHELLLOG_PICK_OLD, shelllog_pick_new)]},
        {"file": "packagegrants.js", "reps": [("ru", PACKAGEGRANTS_OLD, packagegrants_new)]},
        {"file": "main.js", "reps": [("legacy", MAIN_OLD, main_new)]},
        {"file": "tray.js", "reps": [("ru-labels", TRAY_OLD, tray_new)]},
    ]
