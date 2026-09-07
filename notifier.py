import argparse
import json
import sys
from pathlib import Path
import urllib.request
import urllib.error

from epic_notifier import epic

STATE_FILE = Path.home() / ".epic_notifier_state.json"

def load_notified():
    if not STATE_FILE.exists():
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("notified_ids", []))
    except (json.JSONDecodeError, OSError):
        return set()

def save_notified(notified_ids):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"notified_ids": list(notified_ids)}, f, indent=2)
    except OSError as e:
        print(f"warning: failed to write state file: {e}", file=sys.stderr)

def send_discord(discordUrl, games):
    embeds = []
    for g in games:
        embeds.append({
            "title": f"FREE: {g['title']}",
            "description": g.get("description", "No description available."),
            "url": g["url"],
            "color": 3447003,
            "fields": [
                {"name": "Original Price", "value": g.get("original_price", "N/A"), "inline": True},
                {"name": "Ends", "value": g.get("end_date", "N/A"), "inline": True}
            ]
        })

    payload = {
        "content": "🎮 **New free games on Epic Games Store!**",
        "embeds": embeds
    }

    # print(f"Sending payload: {json.dumps(payload)}")  # debug payload structure

    req = urllib.request.Request(
        discordUrl,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "epic-notifier/1.1"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status not in (200, 204):
                print(f"Discord returned status {resp.status}", file=sys.stderr)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"Discord API error: {e.code} - {e.read().decode('utf-8')}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Failed to reach Discord: {e.reason}", file=sys.stderr)
        sys.exit(1)

def send_telegram(telegram_token, chat_id, games):
    # TODO: Telegram markdownv2 requires escaping some characters, check if we need to escape dots/dashes
    text_lines = ["*New free games on Epic Games Store\!*\n"]
    for g in games:
        title = g["title"].replace("-", "\\-").replace(".", "\\.").replace("!", "\\")
        url = g["url"]
        text_lines.append(f"• [{title}]({url})")

    payload = {
        "chat_id": chat_id,
        "text": "\n".join(text_lines),
        "parse_mode": "MarkdownV2"
    }

    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "epic-notifier/1.1"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                print(f"Telegram returned status {resp.status}", file=sys.stderr)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"Telegram API error: {e.code} - {e.read().decode('utf-8')}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Failed to reach Telegram: {e.reason}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Fetch free Epic Games Store games and post to Discord or Telegram.",
        epilog="Example: notifier.py --discord https://discord.com/api/webhooks/..."
    )
    parser.add_argument("--discord", help="Discord Webhook URL to post announcements")
    parser.add_argument("--telegram-token", help="Telegram Bot Token")
    parser.add_argument("--telegram-chat", help="Telegram Chat ID")
    parser.add_argument("--force", action="store_true", help="Send notification even if already sent before")

    args = parser.parse_args()

    if not args.discord and not (args.telegram_token and args.telegram_chat):
        print("Error: must provide either --discord or both --telegram-token and --telegram-chat", file=sys.stderr)
        sys.exit(1)

    try:
        games = epic.get_free_games()
    except urllib.error.URLError as e:
        print(f"Error fetching games from Epic: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error parsing Epic Store API response: {e}", file=sys.stderr)
        sys.exit(1)

    if not games:
        return

    notified_ids = load_notified()
    new_games = []

    for game in games:
        gameId = game["id"]  # Style break: gameId variable
        if args.force or gameId not in notified_ids:
            new_games.append(game)

    if not new_games:
        return

    if args.discord:
        send_discord(args.discord, new_games)

    if args.telegram_token and args.telegram_chat:
        send_telegram(args.telegram_token, args.telegram_chat, new_games)

    for game in new_games:
        notified_ids.add(game["id"])
    save_notified(notified_ids)

if __name__ == "__main__":
    main()
