// Загружает пропатченный ESM-бандл i18n и проверяет, что русский язык
// действительно работает: выбор языка, перевод, fallback и плейсхолдеры.
//
//   node verify_bundle.mjs <bundle.js> <key> <expected-ru> [placeholder-key]

import { pathToFileURL } from 'node:url';

const [bundlePath, key, expected, placeholderKey] = process.argv.slice(2);
if (!bundlePath || !key || expected === undefined) {
  console.error('usage: node verify_bundle.mjs <bundle.js> <key> <expected-ru> [placeholder-key]');
  process.exit(2);
}

let stored = 'ru';
globalThis.localStorage = {
  getItem: (name) => (name === 'rx-lang' ? stored : null),
  setItem: () => {},
  removeItem: () => {},
};
globalThis.document = { documentElement: {} };
Object.defineProperty(globalThis, 'navigator', {
  value: { languages: ['ru-RU', 'ru'], language: 'ru-RU' },
  configurable: true,
  writable: true,
});
globalThis.location = { reload: () => {} };

const mod = await import(pathToFileURL(bundlePath).href);

const result = {};

// 1. Русский выбор языка.
stored = 'ru';
const langRu = mod.r();
result.ruLang = langRu;
result.ruText = mod.o(key);

// 2. Английский выбор языка (словарь en должен остаться рабочим).
stored = 'en';
const langEn = mod.r();
result.enLang = langEn;
result.enText = mod.o(key);

// 3. Китайский fallback: ключ возвращается как есть.
stored = 'zh';
const langZh = mod.r();
result.zhLang = langZh;
result.zhText = mod.o(key);

// 4. Плейсхолдеры подставляются.
if (placeholderKey) {
  result.placeholder = mod.o(placeholderKey, { text: 'ПРИВЕТ' });
}

console.log(JSON.stringify(result, null, 1));

const problems = [];
if (result.ruLang !== 'ru') problems.push('язык не переключился на ru: ' + result.ruLang);
if (result.ruText !== expected) problems.push('ru-перевод не совпал: ' + result.ruText);
if (result.enLang !== 'en') problems.push('язык не переключился на en: ' + result.enLang);
if (!result.enText || result.enText === expected) problems.push('английский словарь сломан: ' + result.enText);
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
