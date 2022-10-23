__all__ = ("config")

from configparser import ConfigParser
from dataclasses import dataclass
from typing import List, Dict

from .args import args

@dataclass
class TelegramConfig:
    token: str
    chat_id: int

@dataclass
class RouterOSConfig:
    host: str
    user: str
    password: str

@dataclass
class RulesConfig:
    match_comment: List[str]

@dataclass
class Config:
    telegram: TelegramConfig
    router_os: RouterOSConfig
    rules: RulesConfig

def parse_list(value: str) -> List[str]:
    if str is None:
        return None
    return [item for item in value.split(', ')]

def load_config() -> Config:
    parser = ConfigParser()
    parser.read(args.config)

    config = Config(
        telegram = TelegramConfig(
            token = parser.get('telegram', 'token'),
            chat_id = parser.get('telegram', 'chat_id')
        ),
        router_os = RouterOSConfig(
            host = parser.get('router_os', 'host'),
            user = parser.get('router_os', 'user'),
            password = parser.get('router_os', 'password')
        ),
        rules = RulesConfig(
            match_comment = parse_list(parser.get('rules', 'match_comment'))
        )
    )

    return config

config = load_config()
