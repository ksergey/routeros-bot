import logging
import asyncio

from aiogram.types import ParseMode, Message, BotCommand, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram import Bot, Dispatcher

from app.config import config
from app.router_os import RouterOS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram.token, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

api = RouterOS(host=config.router_os.host, user=config.router_os.user, password=config.router_os.password)

COMMANDS = [
    BotCommand('list', 'list available rules'),
    BotCommand('help', 'show help message')
]

async def startup(dp: Dispatcher):
    await bot.set_my_commands(commands=COMMANDS)
    await bot.send_message(config.telegram.chat_id, 'hello', reply_markup=ReplyKeyboardRemove())

async def shutdown(dp: Dispatcher):
    pass

def firewall_rules():
    return api.path('ip', 'firewall', 'filter')

def make_rules_keyboard():
    keyboard = InlineKeyboardMarkup()
    for rule in firewall_rules():
        comment = rule.get('comment')
        if comment in config.rules.match_comment:
            id = rule.get('.id')
            state = 'OFF' if rule.get('disabled') == True else 'ON'
            next_state = 'enable' if rule.get('disabled') == True else 'disable'
            keyboard.row(
                InlineKeyboardButton(f'blocking {comment}', callback_data=f'{id},none'),
                InlineKeyboardButton(state, callback_data=f'{id},{next_state}')
            )
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
    id, action = query.data.split(',')
    if action == 'none':
        return

    if action == 'enable':
        firewall_rules().update(**{ 'disabled': False, '.id': id })
    if action == 'disable':
        firewall_rules().update(**{ 'disabled': True, '.id': id })
    await query.answer('done')
    await bot.send_message(text='rules list', reply_markup=make_rules_keyboard(), chat_id=config.telegram.chat_id)

if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=startup, on_shutdown=shutdown)
    except (KeyboardInterrupt, SystemExit):
        logger.error("bot stopped!")
