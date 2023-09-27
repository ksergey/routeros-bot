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
    router: str
    description: str
    path: str
    match: Dict

@dataclass
class Config:
    telegram: TelegramConfig
    routers: Dict[str,RouterOSConfig]
    commands: Dict[str,CommandConfig]

def make_command(description, path_str) -> CommandConfig:
    path_split = path_str.split('/')

    path = '/'.join(path_split[1:-1])

    router_name = path_split[0]
    if router_name.startswith('{') == False or router_name.endswith('}') == False:
        raise Exception('invalid router name expression')

    entry_match_expr = path_split[-1]
    if entry_match_expr.startswith('{') == False or entry_match_expr.endswith('}') == False:
        raise Exception('invalid path match expression')

    match = {}
    for entry in entry_match_expr[1:-1].split(','):
        key, value = entry.split('=', maxsplit=1)
        match[key] = value

    return CommandConfig(router=router_name[1:-1], description=description, path=path, match=match)

def load_config() -> Config:
    parser = ConfigParser()
    parser.read(args.config)

    routers = {}
    for section in parser.sections():
        if not section.startswith('router '):
            continue
        router = RouterOSConfig(
            host = parser[section].get('host'),
            user = parser[section].get('user'),
            password = parser[section].get('password')
        )
        name = section[len('router '):]
        routers[name] = router

    commands = {}
    for section in parser.sections():
        if not section.startswith('command '):
            continue
        command = make_command(parser[section].get('description'), parser[section].get('path'))
        name = section[len('command '):]
        commands[name] = command

    for _, command in commands.items():
        if not command.router in routers:
            raise Exception(f'router "{command.router}" not found')

    config = Config(
        telegram = TelegramConfig(
            token = parser.get('telegram', 'token'),
            chat_id = parser.get('telegram', 'chat_id')
        ),
        routers = routers,
        commands = commands
    )

    return config

config = load_config()
