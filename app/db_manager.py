import sqlite3
from .models import DialogMessage, DialogContext
from .logger_module import logger


class DBManager:
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_tables()


    def _init_tables(self):
        logger.debug("DBManager: Initializing tables if not exist.")
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT,
                    account_id TEXT,
                    author_id TEXT,
                    content TEXT,
                    timestamp TEXT,
                    referenced_message_id TEXT,
                    is_bot INTEGER,
                    PRIMARY KEY (id, account_id)
                )
                """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    log_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()


    def save_message(self, account_id: str, message: DialogMessage, is_bot: bool):
        logger.debug(f"DBManager.save_message: account_id={account_id}, message_id={message.id}, is_bot={is_bot}")
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT OR REPLACE INTO messages
                (id, account_id, author_id, content, timestamp, referenced_message_id, is_bot)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    account_id,
                    message.author_id,
                    message.content,
                    message.timestamp,
                    message.referenced_message_id,
                    1 if is_bot else 0,
                ),
            )
            conn.commit()


    def get_user_dialog_context(self, account_id: str, user_id: str, limit: int = 10) -> DialogContext:
        logger.debug(f"DBManager.get_user_dialog_context: account_id={account_id}, user_id={user_id}, limit={limit}")
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            rows = c.execute(
                """
                SELECT id, author_id, content, timestamp, referenced_message_id, is_bot
                FROM messages
                WHERE account_id = ?
                  AND (author_id = ? OR author_id = ?)
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (account_id, user_id, account_id, limit)
            ).fetchall()

            messages = []
            for row in reversed(rows):
                msg_id, author, content, ts, ref_id, is_bot = row
                dm = DialogMessage(
                    id=msg_id,
                    content=content,
                    author_id=author,
                    timestamp=ts,
                    referenced_message_id=ref_id
                )
                messages.append(dm)

            return DialogContext(
                user_id=user_id,
                messages=messages
            )


    def save_log(self, account_id: str, text: str):
        logger.debug(f"DBManager.save_log: account_id={account_id}, text={text}")
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO logs (account_id, log_text) VALUES (?, ?)",
                (account_id, text)
            )
            conn.commit()
