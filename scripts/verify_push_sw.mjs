// Проверяет русские push-уведомления в service worker.
// Загружает push-sw.js в vm с минимальным mock self и дергает обработчик push.
//
//   node verify_push_sw.mjs <push-sw.js>

import fs from 'node:fs';
import vm from 'node:vm';

const [file] = process.argv.slice(2);
if (!file) {
  console.error('usage: node verify_push_sw.mjs <push-sw.js>');
  process.exit(2);
}

const code = fs.readFileSync(file, 'utf8');

function load(language, languages) {
  const listeners = {};
  const shown = [];
  const self = {
    navigator: { language, languages },
    addEventListener: (name, handler) => {
      listeners[name] = handler;
    },
    registration: {
      scope: 'https://example/',
      showNotification: (title, options) => {
        shown.push({ title, ...options });
        return Promise.resolve();
      },
    },
    clients: {
      matchAll: async () => [],
      openWindow: async () => {},
    },
  };
  const context = { self, console };
  vm.createContext(context);
  vm.runInContext(code, context, { timeout: 5000 });
  if (!listeners.push) throw new Error('обработчик push не зарегистрирован');
  return { listeners, shown };
}

function fire(loaded, payload) {
  let waited = null;
  loaded.listeners.push({
    data: { json: () => payload },
    waitUntil: (promise) => {
      waited = promise;
    },
  });
  return loaded.shown[0];
}

const cases = [
  ['ru-RU', ['ru-RU', 'ru'], { v: 1, type: 'approval', count: 2 }, 'Действие требует'],
  ['en-US', ['en-US', 'en'], { v: 1, type: 'input' }, 'The model is waiting'],
  ['zh-CN', ['zh-CN', 'zh'], { v: 1, type: 'error' }, '一轮'],
  ['de-DE', ['de-DE', 'ru-RU'], { v: 1, type: 'other' }, 'На вашем компьютере'],
  ['en-US', ['en-US', 'ru-RU'], { v: 1, type: 'approval' }, 'An action needs'],
];

let ok = true;
for (const [language, languages, payload, expected] of cases) {
  const loaded = load(language, languages);
  const notification = fire(loaded, payload);
  const text = notification ? `${notification.title} | ${notification.body}` : 'НЕТ УВЕДОМЛЕНИЯ';
  const good = Boolean(notification) && text.includes(expected);
  console.log(`${good ? 'OK  ' : 'FAIL'} ${language} ${JSON.stringify(languages)} -> ${text}`);
  if (!good) ok = false;
}

const counted = fire(load('ru-RU', ['ru-RU']), { v: 1, type: 'approval', count: 3 });
if (!counted || !counted.title.endsWith('(3)')) {
  console.log('FAIL счётчик в заголовке:', counted);
  ok = false;
}

const unknown = fire(load('ru-RU', ['ru-RU']), { v: 1, type: 'неизвестно' });
if (!unknown || !unknown.body.includes('На вашем компьютере')) {
  console.log('FAIL fallback для неизвестного типа:', unknown);
  ok = false;
}

if (!ok) process.exit(1);
console.log('\nPASS');
