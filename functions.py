# Telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, Filters, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from db import *

def button(update, context):
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id
    message_id = update.callback_query['message']['message_id']
    if not legitUser(user_id):
        return
    callback_data = update.callback_query['data']
    if callback_data == 'cancel':
        context.bot.delete_message(chat_id, message_id)
    if callback_data == 'factoryreset':
        context.bot.edit_message_text('Please wait momentarily...', chat_id, message_id)
        try:
            resetdb()
            context.bot.edit_message_text('Reset everything!', chat_id, message_id)
        except Exception as e:
            context.bot.edit_message_text(f'Failed to reset - {e}', chat_id, message_id)
    if callback_data.startswith('disp'):
        context.bot.edit_message_text('Loading... Please wait.', chat_id, message_id)
        txt = '<u>Amount of SOCCash</u>'
        mode = callback_data[4:]
        pointslist = getPoints(mode = mode)
        for counter, og in enumerate(pointslist):
            if counter % 6 == 0:
                txt += '\n'
            og_id = og[0]
            house =  og[2]
            points = og[1]
            txt += f'\n{house} {og_id}: ${points}'
        context.bot.edit_message_text(txt, chat_id, message_id, parse_mode = ParseMode.HTML)

def start(update, context):
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat.id
    if legitUser(user_id):
        context.bot.sendMessage(chat_id, f'Hi, {full_name(user)}. You are an authorized user.')
    else:
        context.bot.sendMessage(chat_id, 'Welcome to the SOCCash bot! To be added as an admin, type /me to get your user id and then send that to an existing admin.')

def me(update, context):
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat.id
    context.bot.sendMessage(chat_id, f'{full_name(user)}, your user id is {user_id}')

def reset(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        context.bot.sendMessage(chat_id, 'You are not an authorized user!')
        return
    msg = context.bot.sendMessage(chat_id, 'Please wait a moment...')
    try:
        resetpoints()
        msg.edit_text('Successfully reset points!')
    except Exception as e:
        msg.edit_text(f'Failed to reset - {e}')

def addadmin(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        context.bot.sendMessage(chat_id, 'You are not an authorized user!')
        return
    toAdd = update.message.text.split(' ')
    added = []
    for user in toAdd[1:]:
        try:
            adduser(int(user))
            added.append(int(user))
        except:
            pass
    if added:
        context.bot.sendMessage(chat_id, f'Added @{" ,".join([context.bot.getChat(user).username for user in added])} successfully!')
    else:
        context.bot.sendMessage(chat_id, 'Failed to add anyone.')

def factoryreset(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        context.bot.sendMessage(chat_id, 'You are not an authorized user!')
        return
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Yes', callback_data = 'factoryreset'),
            InlineKeyboardButton('No', callback_data = 'cancel')
        ]
    ])
    context.bot.sendMessage(chat_id, 'Are you sure you want to reset all SOCCash amounts to 0 and remove all authorized users?', reply_markup = markup)

def display(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        context.bot.sendMessage(chat_id, 'You are not an authorized user!')
        return
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('By house', callback_data = 'disphouse'),
                InlineKeyboardButton('In descending order', callback_data = 'dispdsc')
            ]
        ]
    )
    context.bot.sendMessage(chat_id, 'How would you like to display?', reply_markup = markup)

def add(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        context.bot.sendMessage(chat_id, 'You are not an authorized user!')
        return
    args = update.message.text.strip().split(' ')[1:]
    if len(args) < 2 or not args[-1].isnumeric():
        context.bot.sendMessage(chat_id, 'Invalid format! If you want to add $10 to Aikon 3 and Barg 2, type /add A3 B2 10. Upper/Lowercase does not matter.')
        return
    msg = context.bot.sendMessage(chat_id, 'Please hold on...')
    amt = int(args[-1])
    ogs = args[:-1]
    invalid = []
    valid = []
    for og in ogs:
        if len(og) != 2 or og[0] not in getHouses() or og[1] not in '123456':
            invalid.append(og)
            continue
        valid.append(og)
    res = addPoints(valid, amt)
    og_list = [f'{i[1]} {i[0]}' for i in res]
    points = [i[2] for i in res]
    txt = f'Done! Added ${amt} to {", ".join(og_list)}. Run /display to see the scoreboard.'
    for i, p in enumerate(points):
        txt += f'\n{og_list[i]}: ${p}'
    if invalid:
        txt += '\nInvalid OGs: ' + ', '.join(invalid)
    msg.edit_text(txt)

def massadd(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        context.bot.sendMessage(chat_id, 'You are not an authorized user!')
        return
    args = update.message.text.strip().split(' ')[1:]
    if len(args) != 1 or not args[0].isnumeric():
        context.bot.sendMessage(chat_id, 'Invalid format! If you want to give every OG $10, do /massadd 10')
        return
    amt = int(args[0])
    addAll(amt)
    context.bot.sendMessage(chat_id, f'Succeessfully added ${amt} to every OG!')

def help(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        context.bot.sendMessage(chat_id, 'You are not an authorized user! Please type /me and send your user id to any admin so they can add you.')
        return
    txt = '/me - Sends you your user id. Required to add as admin\n\n'
    txt += '/addadmin <u>userid</u> - Adds the following user as an admin\n\n'
    txt += '/add <u>OG(s)</u> <u>amount</u> - Adds the specified amount of SOCCash to the OG(s) specified. Works for one or more OGs at a time.\n'
    txt += 'e.g. If you want to add $10 to Aikon 3 and Barg 2, type /add A3 B2 10. Upper/Lowercase does not matter.\n\n'
    txt += '/massadd <u>amount</u> - Adds the specified amount of SOCCash to all OGs\n\n'
    txt += '/display - Displays the scoreboard\n\n'
    txt += '/reset - Resets the SOCCash amount to 0 for ALL OGs. USE WITH CAUTION!\n\n'
    txt += '/factoryreset - Resets the SOCCash amount to 0 for ALL OGs and removes all admins. USE WITH CAUTION!\n\n'
    context.bot.sendMessage(chat_id, txt, parse_mode = ParseMode.HTML)

def testfn(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    context.bot.sendMessage(chat_id, getHouses())

def full_name(effective_user):
    first_name = effective_user.first_name
    last_name = effective_user.last_name
    if not (first_name and last_name):
        return first_name or last_name
    return ' '.join([first_name, last_name])
