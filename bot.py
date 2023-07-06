# imports from local files
from handlers import get_dua_or_hadith_text, get_link_of_ayah_or_hadith_of_the_day, \
    prettify_text, set_ayah_pointer_in_img, get_all_duas_links
from database.db import *
from CONSTANTS import *

# imports for telegram bot
from aiogram import Bot, Dispatcher, types
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

# rest imports
from json import load
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# read local variables from config file
with open(ROOT_PATH + "config.json", 'rt') as file:
    _config = load(file)

TOKEN = _config["token"]
ADMIN_ID = _config["admin_id"]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# initialize scheduler class
scheduler = AsyncIOScheduler()

# initialize inline buttons (const)
btn_admin = InlineKeyboardButton('Связаться с администратором', url='https://t.me/feedbackbott')
btn_sub_mailing = InlineKeyboardButton('Подписаться на рассылку', callback_data="mailing")
btn_unsub_mailing = InlineKeyboardButton('Отписаться от рассылки', callback_data="mailing")


@dp.message_handler(commands=["start"])
async def greeting(message: types.Message):
    """
    This function greets on /start command
    :param message:
    :return:
    """
    user_id = message.from_user.id

    # get user's full name
    user_name = message.from_user.full_name

    # check if it is new user
    if user_id not in get_all_users():
        add_new_user(user_id)

    # check if this user has subscribed for mailing or not. then show corresponding inline button
    if get_mailing_status_of_user(user_id):
        btn_mailing = btn_unsub_mailing
    else:
        btn_mailing = btn_sub_mailing

    greeting_kb = InlineKeyboardMarkup().add(btn_admin, btn_mailing)

    await bot.send_message(user_id,
                           f"""Ас-саляму алейкум (اَلسَّلَامُ عَلَيْكُمُ), {user_name}

Данный бот поможет вам:
▫️ укрепить иман
▫️ узнать подробнее про религию 
▫️ не сходить с верного пути

С помощью этого бота вы сможете получать ежедневную рассылку с хадисами и дуа""",
                           reply_markup=greeting_kb)


@dp.message_handler(commands=["change_mailing_status"])
@dp.callback_query_handler(lambda x: x.data == "mailing")
async def change_mailing_status_from_button(query_or_message):
    """
    This function changes user's mailing status after /change_mailing_status command or after pressing inline button
    :param query_or_message: message if user typed the command; query if he pressed the button
    :return:
    """
    user_id = query_or_message.from_user.id

    change_mailing_status_of_user(user_id)
    curr_status = get_mailing_status_of_user(user_id)

    if not curr_status:
        btn_mailing = btn_sub_mailing
        message_text = "Вы отписались от рассылки"

    else:
        btn_mailing = btn_unsub_mailing
        message_text = "Вы подписались на рассылку"

    if type(query_or_message) == types.CallbackQuery:
        await bot.answer_callback_query(query_or_message.id)

        greeting_kb = InlineKeyboardMarkup().add(btn_admin, btn_mailing)

        # edit greeting message where user clicked subscribe/unsubscribe button (rather change button's text)
        await bot.edit_message_text(
            chat_id=query_or_message.message.chat.id,
            message_id=query_or_message.message.message_id,
            text=query_or_message.message.text,
            reply_markup=greeting_kb
        )
    await bot.send_message(user_id,
                           message_text)


async def start_mailing(text='', img=None, data_from_admin=None):
    """
    This function start mailing process. If data_from_admin is not None, bot just copies admin's message and sends it
    to all user who had subscribed on mailing. Else bot makes message itself.
    :param text: text of message (if it is not admin's message)
    :param img: path to image for message (if it is not admin's message)
    :param data_from_admin: it is None, when bot sends message, not ADMIN. If admin wants to post something
    for all users, this parameter will be list with ADMIN_ID and his forwarded message id [admin_id, message_id]
    :return:
    """
    if data_from_admin is not None:
        for user_id in get_all_users():
            await bot.copy_message(user_id,
                                   data_from_admin[0],
                                   data_from_admin[1])
    else:
        # get all users who had subscribed on mailing
        for user_id in get_all_users(mailing=True):
            if img is not None:
                # if here are an image in message, we use `send_photo` method and its caption has 1024 characters limit.
                # so we just send the image and the text using different messages, if we exceed the limit
                if len(text) > 1024:
                    await bot.send_photo(user_id,
                                         types.InputFile(img))
                    await bot.send_message(user_id,
                                           text,
                                           parse_mode='Markdown')
                else:
                    await bot.send_photo(user_id,
                                         types.InputFile(img),
                                         caption=text,
                                         parse_mode='Markdown')
            else:
                await bot.send_message(user_id,
                                       text,
                                       parse_mode='Markdown')


@dp.message_handler(lambda x: x.from_user.id == ADMIN_ID and
                              not any(i in x.text for i in ('start', 'change_mailing_status')),
                    content_types=['photo', 'text', 'video', 'document', 'sticker', 'voice'])
async def send_post_from_admin(message: types.Message):
    """
    This function call start_mailing function if user has ADMIN_ID (so it is admin writes) and his message
    is not just a command.
    :param message:
    :return:
    """
    await start_mailing(data_from_admin=[ADMIN_ID,
                                         message.message_id])


async def prepare_mailing(tp: str) -> None:
    # if tp (type of content) is ayah or hadith, we get the link of ayah or hadith of the day
    if tp in ("ayah", "hadith"):
        url = get_link_of_ayah_or_hadith_of_the_day(_type=tp)
    # if tp (type of content) is dua, we get the link of dua in different way
    else:
        # get links of all duas
        all_duas_links = await get_all_duas_links()
        # to avoid repetitions the dua, we firstly discard posted dua links from common set (using set difference)
        # and get one dua link
        url = (all_duas_links - get_posted_duas()).pop()

        # add to database current url of dua
        add_to_posted_duas(url)

    content_text = get_dua_or_hadith_text(url, _type=tp)

    if tp == "ayah":
        pointer, content = content_text
        set_ayah_pointer_in_img(pointer)

        img = ROOT_PATH + "img/ayah_day.png"
    elif tp == 'hadith':
        img = ROOT_PATH + "img/hadith.jpg"
    else:
        header, content = content_text

        # check if it is dua from Qur'an. The image depends on it
        img = ROOT_PATH + "img/dua_quran.jpg" if "св. коран" in content.lower() else ROOT_PATH + "img/dua.png"

    content_text = prettify_text(
        content_text,
        _type=tp)

    await start_mailing(text=content_text, img=img)

