// Извлекает словари {zh, en} из минифицированного бандла i18n-*.js.
//
// В 2.47.x словарь назывался `v`, в 2.52.x — `b`. Переменная может быть
// объявлена через var/let/const, поэтому после выполнения модуля мы явно
// присваиваем её globalThis.__DICT__ и читаем уже оттуда.
//
// Использование:
//   node extract_bundle.mjs <i18n-*.js> <out.json>

import fs from 'node:fs';
import vm from 'node:vm';

const [bundlePath, outPath] = process.argv.slice(2);
if (!bundlePath || !outPath) {
  console.error('usage: node extract_bundle.mjs <i18n-*.js> <out.json>');
  process.exit(2);
}

const source = fs.readFileSync(bundlePath, 'utf8');
let body = source.replace(/export\{[\s\S]*?\};?/, '');

let dictName = null;
if (/\bb=\{zh:\{\},en:/.test(body)) {
  dictName = 'b';
} else if (/\bv=\{zh:/.test(body)) {
  dictName = 'v';
}
if (!dictName) {
  console.error('не удалось найти объект словаря (b/v) в бандле');
  process.exit(1);
}

body += `\n;globalThis.__DICT__=${dictName};\n`;

const context = {
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  document: { documentElement: {} },
  navigator: { languages: ['en'], language: 'en' },
  location: { reload: () => {} },
  console,
};

vm.createContext(context);
try {
  vm.runInContext(body, context, { timeout: 15000, filename: bundlePath });
} catch (error) {
  console.error('не удалось выполнить бандл: ' + error.message);
  process.exit(1);
}

const dict = context.__DICT__;
if (!dict || typeof dict !== 'object') {
  console.error('объект словаря не получен');
  process.exit(1);
}

const en = dict.en && typeof dict.en === 'object' ? dict.en : {};
const zh = dict.zh && typeof dict.zh === 'object' ? dict.zh : {};

fs.writeFileSync(
  outPath,
  JSON.stringify({ source: bundlePath, dictionary: dictName, en, zh }, null, 0),
  'utf8',
);

console.error(`словарь: ${dictName}, ${Object.keys(en).length} en, ${Object.keys(zh).length} zh`);
