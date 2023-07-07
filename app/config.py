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
class CommandConfig:
    name: str
    description: str
    path: str
    match: Dict

@dataclass
class Config:
    telegram: TelegramConfig
    router_os: RouterOSConfig
    commands: List[CommandConfig]

def make_command(name, description, path_str) -> CommandConfig:
    path_split = path_str.split('/')

    path = '/'.join(path_split[:-1])

    entry_match_expr = path_split[-1]
    if entry_match_expr.startswith('{') == False or entry_match_expr.endswith('}') == False:
        raise Exception('invalid path match expression')

    match = {}
    for entry in entry_match_expr[1:-1].split(','):
        key, value = entry.split('=', maxsplit=1)
        match[key] = value

    return CommandConfig(name=name, description=description, path=path, match=match)

def load_config() -> Config:
    parser = ConfigParser()
    parser.read(args.config)

    commands = []
    for section in parser.sections():
        if not section.startswith('command '):
            continue
        command = make_command(section[len('command '):], parser[section].get('description'), parser[section].get('path'))
        commands.append(command)

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
        commands = commands
    )

    return config

config = load_config()
