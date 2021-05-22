# Telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, Filters, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from db import *
from pybot import BASE_AMOUNT

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
    elif callback_data == 'factoryreset':
        context.bot.edit_message_text('Please wait momentarily...', chat_id, message_id)
        try:
            resetdb()
            context.bot.edit_message_text('Reset everything!', chat_id, message_id)
        except Exception as e:
            context.bot.edit_message_text(f'Failed to reset - {e}', chat_id, message_id)
    elif callback_data.startswith('disp'):
        context.bot.edit_message_text('Loading... Please wait.', chat_id, message_id)
        txt = '<u>Amount of SOCCash</u>'
        mode = callback_data[4:]
        pointslist = getPoints(mode = mode)
        if mode == 'house':
            maxes = []
            for i in range(6):
                for j in range(6):
                    if pointslist[6 * i + j][1] == max([points[1] for points in pointslist[6 * i : 6 * i + 6]]) and pointslist[6 * i + j][1] > BASE_AMOUNT:
                        maxes.append(6 * i + j)
        for counter, og in enumerate(pointslist):
            og_id = og[0]
            house =  og[2]
            points = og[1]
            if counter % 6 == 0:
                if mode == 'house':
                    txt += f'\n\n<u>{house} Total: {sum([i[1] for i in pointslist[counter:counter + 6]])}</u>'
                else:
                    txt += '\n'
            if mode == 'house' and counter in maxes:
                txt += '<b>'
            txt += f'\n{house} {og_id}: ${points}'
            if mode == 'house' and counter in maxes:
                txt += f' (Top {house} contributor!)</b>'
        context.bot.edit_message_text(txt, chat_id, message_id, parse_mode = ParseMode.HTML)
    elif callback_data.startswith('add'):
        msg = context.bot.edit_message_text('Adding, please hold on...', chat_id, message_id)
        id = int(callback_data.split('.')[1])
        addUser(id)
        msg.edit_text(f'Done! @{context.bot.getChat(id).username} is now an admin!')
    elif callback_data.startswith('revoke'):
        msg = context.bot.edit_message_text('Revoking, please hold on...', chat_id, message_id)
        id = callback_data.split('.')[1]
        revokeAdmin([id])
        msg.edit_text(f'Done! @{context.bot.getChat(id).username} is no longer an admin!')

def start(update, context):
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat.id
    if legitUser(user_id):
        context.bot.sendMessage(chat_id, f'Hi, {full_name(user)}. You are an authorized user. To add others as admin, you can forward their message to me or use the /addadmin command. View /help for more.')
    else:
        context.bot.sendMessage(chat_id, 'Welcome to the SOCCash bot! To be added as an admin, type /me to get your user id and then send that to an existing admin, or you can get an exiting admin to forward a message by you to me.')

def me(update, context):
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat.id
    context.bot.sendMessage(chat_id, f'{full_name(user)}, your user id is {user_id}')

def reset(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if accessDenied(update, context):
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
    if accessDenied(update, context):
        return
    toAdd = update.message.text.split(' ')
    added = []
    for user in toAdd[1:]:
        print
        if context.bot.getChat(int(user)).get_member(int(user)).user.is_bot:
            continue
        if addUser(int(user)):
            added.append(int(user))
    if added:
        added = [f'@{user}' for user in added]
        context.bot.sendMessage(chat_id, f'Added @{", ".join([context.bot.getChat(user).username for user in added])} as admin successfully!')
    else:
        context.bot.sendMessage(chat_id, 'Failed to add anyone. Are they already admin?')

def factoryreset(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if accessDenied(update, context):
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
    if accessDenied(update, context):
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
    if accessDenied(update, context):
        return
    args = update.message.text.strip().upper().split(' ')[1:]
    if len(args) < 2 or not args[-1].isnumeric():
        context.bot.sendMessage(chat_id, 'Invalid format! If you want to add $10 to Aikon 3 and Barg 2, type /add A3 B2 10. Upper/Lowercase does not matter.')
        return
    msg = context.bot.sendMessage(chat_id, 'Please hold on...')
    amt = int(args[-1])
    ogs = args[:-1]
    invalid = []
    valid = []
    houses = getHouses()
    for og in ogs:
        if len(og) != 2 or og[0] not in houses or og[1] not in '123456':
            invalid.append(og)
            continue
        valid.append(og)
    if not valid:
        msg.edit_text('Failed to add to any OG. Please check your format.')
        return
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
    if accessDenied(update, context):
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
    if accessDenied(update, context):
        return
    txt = 'Forward a message from a user to add/remove them as admin\n\n'
    txt += '/me - Sends you your user id. Required to add as admin\n\n'
    txt += '/addadmin <u>userid(s)</u> - Adds the following user(s) as an admin. Separate user ids with a space\n\n'
    txt += '/revoke <u>usernames/user ids</u> - Revokes admin privilegs from the following people. Unlike /addadmin, this works with usernames'
    txt += '/add <u>OG(s)</u> <u>amount</u> - Adds the specified amount of SOCCash to the OG(s) specified. Works for one or more OGs at a time.\n'
    txt += 'e.g. If you want to add $10 to Aikon 3 and Barg 2, type /add A3 B2 10. Upper/Lowercase does not matter.\n\n'
    txt += '/massadd <u>amount</u> - Adds the specified amount of SOCCash to all OGs\n\n'
    txt += '/display - Displays the scoreboard\n\n'
    txt += '/admins - Displays all admins\n\n'
    txt += '/reset - Resets the SOCCash amount to 0 for ALL OGs. USE WITH CAUTION!\n\n'
    txt += '/factoryreset - Resets the SOCCash amount to 0 for ALL OGs and removes all admins. USE WITH CAUTION!\n\n'
    context.bot.sendMessage(chat_id, txt, parse_mode = ParseMode.HTML)

def accessDenied(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        context.bot.sendMessage(chat_id, 'You are not an authorized user! To get added as an admin, please type /me and send your user id to any admin so they can add you.')
        return True
    return False

def forwarded(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if not legitUser(user_id):
        return
    if update.message.forward_from is None:
        context.bot.sendMessage(chat_id, f'Due to {update.message.forward_sender_name}\'s privacy settings, I cannot add them. Get them to PM me /me and send you their user id!')
        return
    if update.message.forward_from == context.bot.get_me():
        context.bot.sendMessage(chat_id, 'You cannot make me an admin!')
        return
    if update.message.forward_from.is_bot:
        context.bot.sendMessage(chat_id, 'You can only make humans admins!')
        return
    forwardedFrom = update.message.forward_from
    legit = legitUser(forwardedFrom.id)
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Yes', callback_data = f'revoke.{forwardedFrom.id}' if legit else f'add.{forwardedFrom.id}'),
            InlineKeyboardButton('Cancel', callback_data = 'cancel')
        ]
    ])
    if legit:
        txt = f'@{forwardedFrom.username} is already an admin. Do  you want to revoke their admin privileges?'
    else:
        txt = f'Do you want to add @{forwardedFrom.username} as admin?'
    context.bot.sendMessage(chat_id, txt, reply_markup = markup)

def revoke(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if accessDenied(update, context):
        return
    args = update.message.text.strip().split(' ')[1:]
    idList = getAdmins()
    userList = {context.bot.getChat(user).username: user for user in idList}
    valid = []
    for user in args:
        if user.isnumeric() and int(user) in idList:
            valid.append(user)
        elif user in userList.keys():
            valid.append(userList[user])
    removed = revokeAdmin(valid)
    if removed:
        r = ', '.join(['@' + context.bot.getChat(user).username for user in removed])
        txt = f'Successfully removed {r}.'
    else:
        txt = 'Did not remove anyone! I accept usernames, user ids or forwarded messages.'
    context.bot.sendMessage(chat_id, txt)

def admins(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    if accessDenied(update, context):
        return
    idList = getAdmins()
    userList = [('@' + context.bot.getChat(user).username) for user in idList]
    txt = ', '.join(userList)
    context.bot.sendMessage(chat_id, f'The admins are {txt}')

def full_name(effective_user):
    first_name = effective_user.first_name
    last_name = effective_user.last_name
    if not (first_name and last_name):
        return first_name or last_name
    return ' '.join([first_name, last_name])
