// Загружает пропатченный ESM-бандл i18n и проверяет выбранный язык:
// переключение, перевод, fallback en/zh и плейсхолдеры.
//
//   node verify_bundle.mjs <bundle.js> <key> <expected> [placeholder-key] [lang]

import { pathToFileURL } from 'node:url';

const [bundlePath, key, expected, placeholderKey, lang = 'ru'] = process.argv.slice(2);
if (!bundlePath || !key || expected === undefined) {
  console.error('usage: node verify_bundle.mjs <bundle.js> <key> <expected> [placeholder-key] [lang]');
  process.exit(2);
}

let stored = lang;
globalThis.localStorage = {
  getItem: (name) => (name === 'rx-lang' ? stored : null),
  setItem: () => {},
  removeItem: () => {},
};
globalThis.document = { documentElement: {} };
Object.defineProperty(globalThis, 'navigator', {
  value: { languages: [`${lang}-${lang.toUpperCase()}`, lang], language: lang },
  configurable: true,
  writable: true,
});
globalThis.location = { reload: () => {} };

const mod = await import(pathToFileURL(bundlePath).href);

const result = {};

// 1. Выбор целевого языка.
stored = lang;
result.targetLang = mod.r();
result.targetText = mod.o(key);

// 2. Английский выбор языка (словарь en должен остаться рабочим).
stored = 'en';
result.enLang = mod.r();
result.enText = mod.o(key);

// 3. Китайский fallback: ключ возвращается как есть.
stored = 'zh';
result.zhLang = mod.r();
result.zhText = mod.o(key);

// 4. Плейсхолдеры подставляются.
if (placeholderKey) {
  result.placeholder = mod.o(placeholderKey, { text: 'ПРИВЕТ' });
}

console.log(JSON.stringify(result, null, 1));

const problems = [];
if (result.targetLang !== lang) problems.push(`язык не переключился на ${lang}: ` + result.targetLang);
if (result.targetText !== expected) problems.push(`${lang}-перевод не совпал: ` + result.targetText);
if (result.enLang !== 'en') problems.push('язык не переключился на en: ' + result.enLang);
if (!result.enText) problems.push('английский словарь пуст: ' + result.enText);
if (result.zhLang !== 'zh') problems.push('язык не переключился на zh: ' + result.zhLang);
if (result.zhText !== key) problems.push('китайский fallback сломан: ' + result.zhText);
if (placeholderKey && !String(result.placeholder).includes('ПРИВЕТ')) {
  problems.push('плейсхолдер не подставился: ' + result.placeholder);
}

if (problems.length) {
  console.error('\nFAIL:\n- ' + problems.join('\n- '));
  process.exit(1);
}
console.log('\nPASS');
