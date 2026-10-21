# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 1.x | ✅ |
| < 1.0 | ❌ |

The toolchain targets Reasonix Studio **2.47.x**. A different build is checked
by anchors, not by the version number; see `README.md`.

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Use GitHub Security
Advisories:

https://github.com/itsbuyru-bit/Reasonix-RU-Localization/security/advisories/new

Include:

- affected version and Windows version;
- steps to reproduce;
- impact;
- relevant logs with secrets removed.

## What is in scope

- the Python patchers and menu;
- the web/`app.asar` backup and restore logic;
- unintended file writes or path traversal;
- accidental exposure of API keys or personal data;
- unsafe handling of `app.asar` or downloaded dependencies.

## What is out of scope

- vulnerabilities in Reasonix Studio itself (report them to its maintainers);
- the hosted Web Studio at `reasonix.io`;
- the DeepSeek API service;
- issues caused by adding an API key to a public place.

## Safe handling of data

- The project never needs your API key to be committed; it reads
  `DEEPSEEK_API_KEY` from `%APPDATA%\reasonix\.env` only for translation.
- Backups are local and live under `work/backup/`; they are gitignored.
- Do not attach `app.asar`, session logs, keys, or private code to issues.
- The patcher only modifies files under the Reasonix Studio installation it
  detects, plus its own `work/` directory.
