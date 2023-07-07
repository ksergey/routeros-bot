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

COMMANDS = [
    BotCommand('list', 'list available rules'),
    BotCommand('help', 'show help message')
]

async def startup(dp: Dispatcher):
    await bot.set_my_commands(commands=COMMANDS)
    await bot.send_message(config.telegram.chat_id, 'hello', reply_markup=ReplyKeyboardRemove())

async def shutdown(dp: Dispatcher):
    pass

def router_os_api():
    return connect(username=config.router_os.user, password=config.router_os.password, host=config.router_os.host)

def make_rules_keyboard(connection=None):
    key_id = Key('.id')
    key_disabled = Key('disabled')

    keyboard = InlineKeyboardMarkup()

    if connection:
        api = connection
    else:
        api = router_os_api()

    for command in config.commands:
        match_expr = [ Key(key) == command.match[key] for key in command.match ]
        data = api.path(command.path).select(Key('.id'), Key('disabled')).where(*match_expr)
        data = tuple(data)[0]

        value_id = data['.id']
        value_state = 'off' if data['disabled'] == True else 'on'
        value_next_state = 'on' if data['disabled'] == True else 'off'

        keyboard.row(
            InlineKeyboardButton(command.description, callback_data=f'{command.path},{value_id},none'),
            InlineKeyboardButton(value_state, callback_data=f'{command.path},{value_id},{value_next_state}')
        )

    if not connection:
        api.close()

    return keyboard

@dp.message_handler(commands=['help'], chat_id=config.telegram.chat_id)
async def command_help(message: Message):
    help_message = ''.join(f'/{command.command} - {command.description}\n' for command in COMMANDS)
    await message.answer(help_message)

@dp.message_handler(commands=['list'], chat_id=config.telegram.chat_id)
async def command_list_rules(message: Message):
    await message.answer(text='rules list', reply_markup=make_rules_keyboard())

@dp.callback_query_handler(chat_id=config.telegram.chat_id)
async def callback_handler(query: CallbackQuery):
    path, value_id, value_next_state = query.data.split(',')

    if value_next_state == 'none':
        return

    api = router_os_api()

    if value_next_state == 'on':
        api.path(path).update(**{ 'disabled': False, '.id': value_id })

    if value_next_state == 'off':
        api.path(path).update(**{ 'disabled': True, '.id': value_id })


    await query.answer('done')
    await bot.send_message(text='rules list', reply_markup=make_rules_keyboard(api), chat_id=config.telegram.chat_id)

    api.close()

if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=startup, on_shutdown=shutdown)
    except (KeyboardInterrupt, SystemExit):
        logger.error("bot stopped!")
