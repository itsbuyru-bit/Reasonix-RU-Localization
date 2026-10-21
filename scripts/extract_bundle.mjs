// Извлекает словари {zh, en} из минифицированного бандла i18n-*.js.
//
// Бандл — это ES-модуль, в котором словарь объявлен как
//   var v={zh:{},en:{...t,...n,...e,...}};
// Мы убираем финальный export, выполняем модуль в vm с заглушками браузера
// и читаем получившийся объект v. Ничего не запускается из сети.
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
const body = source.replace(/export\{[\s\S]*?\};?\s*$/, '');

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

if (!context.v || typeof context.v !== 'object') {
  console.error('объект словаря v не найден');
  process.exit(1);
}

const en = context.v.en && typeof context.v.en === 'object' ? context.v.en : {};
const zh = context.v.zh && typeof context.v.zh === 'object' ? context.v.zh : {};

fs.writeFileSync(
  outPath,
  JSON.stringify({ source: bundlePath, en, zh }, null, 0),
  'utf8',
);

console.error(`словарь: ${Object.keys(en).length} en, ${Object.keys(zh).length} zh`);
