## NOTE FROM ROAD
настройка интервала между сообщениями:

файл app/discord_heartbeat.py
```python
heartbeat = DiscordHeartbeat(
            account=account,
            ai_handler=ai_handler,
            heartbeat_interval=(300, 600)  # Настройте интервал по вашему усмотрению 300 == 5 минут
        )
```

# Discord AI Spammer

![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Description

**Discord AI Spammer** automates conversations in Discord chats using OpenAI's AI. It integrates AI to generate responses, allowing your Discord accounts to interact automatically in server chats.

## Technologies

- **Language:** Python
- **Dependencies:** Listed in `requirements.txt`

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/ENbanned/discord_ai.git
    cd discord_ai
    ```

2. **Install dependencies:**
    ```bash
    python -m venv venv
    venv\scripts\activate
    pip install -r requirements.txt
    ```

## Configuration

1. **Configure `config.py`:**
    ```python
    openai_api_key = "YOUR_OPENAI_API_KEY"
    openai_model = "gpt-3.5-turbo"

    proxy_for_openai_api = "None"  # Use format: http://username:password@ip:port or "None"

    interval_time_from = 60  # Minimum time between messages (seconds)
    interval_time_to = 240   # Maximum time between messages (seconds)
    ```

2. **Set up `accounts.json` (Remove proxy = {} if proxies are not needed for this account.):**
    ```json
    {
        "accounts": [
            {
                "token": "YOUR-DISCORD-TOKEN",
                "user_id": "YOUR-USER-ID",
                "channel_id": "YOUR-CHAT-ID",
                "headers": {
                    "authority": "discord.com",
                    "accept": "*/*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/json",
                    "origin": "https://discord.com",
                    "referer": "https://discord.com/channels/YOUR-CHANNEL-ID/YOUR-CHAT-ID",
                    "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": "\"macOS\"",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "user-agent": "YOUR-USER-AGENT",
                    "x-debug-options": "bugReporterEnabled",
                    "x-discord-locale": "en-US",
                    "x-discord-timezone": "America/New_York"
                },
                "proxy": {
                    "host": "ip",
                    "port": 8000,
                    "username": "username",
                    "password": "password",
                    "protocol": "http"
                }
            },
            {
                "token": "...",
                "headers": {
                    "..."
                }

            }

        ]
    }
    ```

## Usage

1. **Run the bot:**
    ```bash
    python main.py
    ```

2. **Ensure `config.py` and `accounts.json` are properly configured.** The bot will monitor the specified Discord channels and send AI-generated messages automatically.

## Project Structure

- `ai_handler.py` – Handles OpenAI API interactions.
- `db_manager.py` – Manages SQLite database for messages and logs.
- `dialog_manager.py` – Classifies and selects messages to respond to.
- `discord_client.py` – Interacts with Discord API for fetching and sending messages.
- `logger_module.py` – Sets up logging using loguru.
- `models.py` – Defines data models.
- `accounts.json` – Discord accounts configuration.
- `config.py` – Project settings.
- `main.py` – Entry point to run the bot.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contact

Telegram: [@enbanned](https://t.me/enbanned)


