# Telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, Filters, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext

# Bot Functions
from functions import *

# Random Stuff
import os, logging
import psycopg2 as psql

# Defer
from contextlib import ExitStack
from functools import partial

test = 'config.py' in os.listdir()
BASE_AMOUNT = 0

if test:
	from config import *
else:
	TOKEN = os.environ['TELEGRAM_TOKEN']
	DB_URL = os.environ['DATABASE_URL']
	PORT = int(os.environ.get('PORT', 8443))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# database things
con = psql.connect(DB_URL, sslmode='prefer' if test else 'require')
cur = con.cursor()

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
	updater = Updater(TOKEN, request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
	dp = updater.dispatcher

    # Handlers
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('me', me))
	dp.add_handler(CommandHandler('addadmin', addadmin))
	dp.add_handler(CommandHandler('reset', reset))
	dp.add_handler(CommandHandler('factoryreset', factoryreset))
	dp.add_handler(CommandHandler('display', display))
	dp.add_handler(CommandHandler('add', add))
	dp.add_handler(CommandHandler('help', help))
	dp.add_handler(CommandHandler('massadd', massadd))
	dp.add_handler(CommandHandler('revoke', revoke))
	dp.add_handler(CommandHandler('admins', admins))
	dp.add_handler(MessageHandler(Filters.forwarded, forwarded))
	dp.add_handler(CallbackQueryHandler(button))
	dp.add_error_handler(error)

    # Set Webhook
	if test:
		updater.start_polling()
	else:
		updater.start_webhook(
			listen='0.0.0.0',
			port = PORT,
			url_path = TOKEN,
			webhook_url = 'https://soccash-bot.herokuapp.com/' + TOKEN
		)
	# updater.bot.sendMessage(ic1_id, 'Up and running!') # got too annoying
	with ExitStack() as stack:
		stack.callback(con.close)
		stack.callback(cur.close)
		updater.idle()

if __name__ == '__main__':
    main()
