import logging
import asyncio
import ipaddress

from aiogram.types import ParseMode, Message, BotCommand, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram import Bot, Dispatcher

from librouteros import connect
from librouteros.query import Key

from app.config import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram.token, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

def get_commands():
    commands = []
    for name, command in config.commands.items():
        commands.append(BotCommand(name, command.description))
    commands.append(BotCommand('help', 'print help'))
    return commands

def register_commands(dp: Dispatcher):
    for name, command in config.commands.items():
        router = config.routers[command.router]

        async def handler(message: Message):
            notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
            try:
                # connect
                api = connect(username=router.user, password=router.password, host=router.host, timeout=15)

                match_expr = [ Key(key) == command.match[key] for key in command.match ]

                # match record
                data = api.path(command.path).select(Key('.id'), Key('disabled')).where(*match_expr)
                data = tuple(data)[0]
                # state
                state = data['disabled']

                # update
                api.path(command.path).update(**{ 'disabled': not state, '.id': data['.id'] })

                # disconnect
                api.close()

                if state:
                    text = f'rule "{name}" state changed from OFF to ON'
                else:
                    text = f'rule "{name}" state changed from ON to OFF'

                await message.reply(text)
            except Exception as ex:
                await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
            finally:
                await notification_message.delete()

        dp.register_message_handler(handler, commands=[name], chat_id=config.telegram.chat_id)

async def startup(dp: Dispatcher):
    register_commands(dp)
    await bot.set_my_commands(commands=get_commands())
    await bot.send_message(config.telegram.chat_id, 'hello', reply_markup=ReplyKeyboardRemove())

async def shutdown(dp: Dispatcher):
    pass

@dp.message_handler(commands=['help'], chat_id=config.telegram.chat_id)
async def command_help(message: Message):
    help_message = ''.join(f'/{command.command} - {command.description}\n' for command in get_commands())
    await message.answer(help_message)

if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=startup, on_shutdown=shutdown)
    except (KeyboardInterrupt, SystemExit):
        logger.error("bot stopped!")
