from telegram.ext import MessageHandler, Filters
from telegram_util import log_on_fail, splitCommand, tryDelete
from common import debug_group
import dbase
from ssearch import searchText, searchChannel, getHtmlReply, getMarkdownReply
import time

def sendResult(msg, result):
	if not result:
		return
	try:
		return msg.reply_text('\n'.join(getHtmlReply(result)), 
				disable_web_page_preview = True, parse_mode = 'html')
	except:
		print(result)
		return msg.reply_text('\n'.join(getMarkdownReply(result)), 
			disable_web_page_preview = True, parse_mode = 'markdown')

def forwardDebug(msg):
	if msg.from_user and msg.from_user.id == debug_group.id:
		return
	if msg.chat.id == debug_group.id:
		return
	msg.forward(debug_group.id)

def search(msg, text, method):
	reply1 = msg.reply_text('searching')
	start = time.time()
	result = method(text, searchCore=True)
	reply2 = sendResult(msg, result)
	if reply2:
		forwardDebug(reply2)
	forwardDebug(msg)
	result = method(text)
	reply3 = sendResult(msg, result)
	if reply2:
		tryDelete(reply2)
	if not reply3: 
		reply3 = msg.reply_text('no result')
	tryDelete(reply1)
	forwardDebug(reply3)
	debug_group.send_message('time elapse: ' + str(time.time() - start))
	

with open('help.md') as f:
	HELP_MESSAGE = f.read()

@log_on_fail(debug_group)
def handleCommand(update, context):
	msg = update.message # Do not support command in channel
	if not msg or not msg.text:
		return
	command, text = splitCommand(msg.text)
	if not text and command != '/start':
		if command.startswith('/sc'):
			command, text = '/sc', command[3:]
		elif command.startswith('/s'):
			command, text = '/s', command[2:]
	if 'channel' in command or command == '/sc':
		search(msg, text, searchChannel)
		return
	if 'start' in command:
		msg.reply_text(HELP_MESSAGE, disable_web_page_preview=True)
		return
	if 'search' in command or command == '/s':
		search(msg, text, searchText)
		return
	if msg.from_user and msg.from_user.id == debug_group.id:
		if command == '/sb':
			dbase.setBadWord(text)
			msg.reply_text('success')
			return
		if command in ['/ss']:
			dbase.setChannelScore(text)
			msg.reply_text('success')
			return
	if msg.chat_id > 0:
		msg.reply_text(HELP_MESSAGE, disable_web_page_preview=True)
		return

@log_on_fail(debug_group)
def handleSearch(update, context):
	msg = update.message
	text = msg.text.strip()
	print('here1')
	search(msg, text, searchText)

@log_on_fail(debug_group)
def handleGroup(update, context):
	msg = update.effective_message
	if not msg.chat.username:
		return
	post_link = '%s/%s' % (msg.chat.username, msg.message_id)
	text = msg.text or msg.caption or (
		msg.document and msg.document.file_name)
	if not text:
		return
	text = ' '.join(text.split())
	prefix = 'hasFile ' if msg.document else ''
	dbase.updateIndex(post_link, prefix + text, msg.chat.username)
	dbase.updateMaintext(post_link, text[:20])
	dbase.updateTime(post_link, int(time.time()))

def setupCommand(dp):
	dp.add_handler(MessageHandler(Filters.command, handleCommand))
	dp.add_handler(MessageHandler(~Filters.command & Filters.private, handleSearch))
	dp.add_handler(MessageHandler(~Filters.command & ~Filters.private, handleGroup))