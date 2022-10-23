import logging

from librouteros import connect
from librouteros.login import token

logger = logging.getLogger(__name__)

class RouterOS:
    def __init__(self, host: str, user: str, password: str, loop=None) -> None:
        self._host = host
        self._user = user
        self._password = password
        logger.info(f'RouterOS (host="{self._host}", user="{self._user}", password="{self._password}")')

    def path(self, *args, **kwargs):
        return connect(
            username=self._user,
            password=self._password,
            host=self._host
        ).path(*args, **kwargs)
