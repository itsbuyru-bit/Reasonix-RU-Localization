// Обёртка над @electron/asar: extract / pack / list.
// Модуль передаётся абсолютным путём, чтобы не зависеть от NODE_PATH.
//
//   node asar_tool.mjs <asar.js> extract <archive> <dir>
//   node asar_tool.mjs <asar.js> pack <dir> <archive>
//   node asar_tool.mjs <asar.js> list <archive>

import { pathToFileURL } from 'node:url';

const [modulePath, action, ...args] = process.argv.slice(2);
if (!modulePath || !action) {
  console.error('usage: node asar_tool.mjs <asar.js> extract|pack|list ...');
  process.exit(2);
}

const asar = await import(pathToFileURL(modulePath).href);

if (action === 'extract') {
  const [archive, dir] = args;
  if (!archive || !dir) {
    console.error('extract: нужны archive и dir');
    process.exit(2);
  }
  asar.extractAll(archive, dir);
} else if (action === 'pack') {
  const [dir, archive] = args;
  if (!dir || !archive) {
    console.error('pack: нужны dir и archive');
    process.exit(2);
  }
  await asar.createPackage(dir, archive);
} else if (action === 'list') {
  const [archive] = args;
  if (!archive) {
    console.error('list: нужен archive');
    process.exit(2);
  }
  console.log(asar.listPackage(archive).join('\n'));
} else {
  console.error('неизвестное действие: ' + action);
  process.exit(2);
}
