import logging
import asyncio

from aiogram.types import ParseMode,Message,BotCommand,CallbackQuery,ReplyKeyboardRemove,ReplyKeyboardMarkup,KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram import Bot, Dispatcher

from app.config import config
from app.router_os import RouterOS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

bot = Bot(token=config.telegram.token, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

api = RouterOS(host=config.router_os.host, user=config.router_os.user, password=config.router_os.password)

COMMANDS = [
    BotCommand('enable', 'enable rule on router os'),
    BotCommand('disable', 'disable rule on router os'),
    BotCommand('help', 'show help message')
]

class CommandState(StatesGroup):
    enable_rule = State()
    disable_rule = State()

async def startup(dp: Dispatcher):
    await bot.set_my_commands(commands=COMMANDS)
    await bot.send_message(config.telegram.chat_id, 'hello', reply_markup=ReplyKeyboardRemove())

async def shutdown(dp: Dispatcher):
    pass

def firewall_rules():
    return api.path('ip', 'firewall', 'filter')

def rules_keyboard(action: str):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for rule in firewall_rules():
        comment = rule.get('comment')
        if comment in config.rules.match_comment:
            id = rule.get('.id')
            keyboard.add(KeyboardButton(text=comment))
    return keyboard

@dp.message_handler(commands=['help'], chat_id=config.telegram.chat_id)
async def command_help(message: Message):
    help_message = ''.join(f'/{command.command} - {command.description}\n' for command in COMMANDS)
    await message.answer(help_message)

@dp.message_handler(commands=['enable'], chat_id=config.telegram.chat_id)
async def command_enable(message: Message):
    await message.answer('enable firewall rule', reply_markup=rules_keyboard('enable'))
    await CommandState.enable_rule.set()

@dp.message_handler(commands=['disable'], chat_id=config.telegram.chat_id)
async def command_disable(message: Message):
    await message.reply('disable firewall rule', reply_markup=rules_keyboard('disable'))
    await CommandState.disable_rule.set()

@dp.message_handler(state=CommandState.disable_rule)
async def command_reply_enable(message: Message, state: FSMContext):
    comment = message.text.strip()
    rules = firewall_rules()
    ids = [ rule.get('.id') for rule in rules if rule.get('comment') == comment ]
    for id in ids:
        rules.update(**{ 'disabled': False, '.id': id })
    await message.answer(f'done')
    await state.finish()

@dp.message_handler(state=CommandState.enable_rule)
async def command_reply_disable(message: Message, state: FSMContext):
    comment = message.text.strip()
    rules = firewall_rules()
    ids = [ rule.get('.id') for rule in rules if rule.get('comment') == comment ]
    for id in ids:
        rules.update(**{ 'disabled': True, '.id': id })
    await message.answer(f'done')
    await state.finish()

if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=startup, on_shutdown=shutdown)
    except (KeyboardInterrupt, SystemExit):
        logger.error("bot stopped!")
