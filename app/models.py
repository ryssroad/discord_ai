from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class DiscordProxyConfig:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"

    @property
    def url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"


@dataclass
class DiscordAccount:
    token: str
    user_id: str
    channel_id: str
    headers: Dict[str, str]
    proxy: Optional[DiscordProxyConfig] = None
    
    
@dataclass
class ProxyConfig:
    host: str
    port: str
    username: str
    password: str
    proxy_type: str


@dataclass
class AIConfig:
    api_key: str
    model: str = "gpt-3.5-turbo"
    proxy: Optional[ProxyConfig] = None


@dataclass
class DialogMessage:
    id: str
    content: str
    author_id: str
    timestamp: str
    referenced_message_id: Optional[str] = None


@dataclass
class DialogContext:
    user_id: str
    messages: List[DialogMessage] = field(default_factory=list)
