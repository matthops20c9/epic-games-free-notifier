# epic-games-free-notifier

A lightweight CLI utility that checks the Epic Games Store for currently active free games and sends alerts to a Discord channel or Telegram chat. It tracks notified games locally to ensure you only get pinged once per game.

Designed to run as a scheduled task on Windows (e.g., via Task Scheduler) without requiring docker, external database engines, or complex pip dependency trees.

## Setup

No installation required. Just download the files and ensure you have Python 3.8+ installed.

```cmd
git clone https://github.com/username/epic-games-free-notifier.git
cd epic-games-free-notifier
```

## Usage

Run the script directly using Python. You must provide either a Discord Webhook URL or a Telegram Bot Token/Chat ID combination.

### Discord

```cmd
python notifier.py --discord "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
```

### Telegram

```cmd
python notifier.py --telegram-token "123456:ABC-DEF1234ghIkl-zyx" --telegram-chat "-100123456789"
```

### Optional Arguments

* `--state-file`: Custom path for the state tracking file (defaults to `~/.epic_notified.json`)
* `--verbose`: Output step-by-step logs to stderr for debugging scheduled tasks

<!-- refreshed: 2026-09-14 -->
