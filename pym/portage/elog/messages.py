# elog/messages.py - elog core functions
# Copyright 2006-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

from portage.output import colorize
from portage.const import EBUILD_PHASES
from portage.util import writemsg

import os
import sys

def collect_ebuild_messages(path):
	""" Collect elog messages generated by the bash logging function stored 
		at 'path'.
	"""
	mylogfiles = None
	try:
		mylogfiles = os.listdir(path)
	except OSError:
		pass
	# shortcut for packages without any messages
	if not mylogfiles:
		return {}
	# exploit listdir() file order so we process log entries in chronological order
	mylogfiles.reverse()
	logentries = {}
	for msgfunction in mylogfiles:
		filename = os.path.join(path, msgfunction)
		if msgfunction not in EBUILD_PHASES:
			writemsg("!!! can't process invalid log file: %s\n" % filename,
				noiselevel=-1)
			continue
		if not msgfunction in logentries:
			logentries[msgfunction] = []
		lastmsgtype = None
		msgcontent = []
		for l in open(filename, "r").read().split("\0"):
			if not l:
				continue
			try:
				msgtype, msg = l.split(" ", 1)
			except ValueError:
				writemsg("!!! malformed entry in " + \
					"log file: '%s'\n" % filename, noiselevel=-1)
				continue

			if lastmsgtype is None:
				lastmsgtype = msgtype
			
			if msgtype == lastmsgtype:
				msgcontent.append(msg)
			else:
				if msgcontent:
					logentries[msgfunction].append((lastmsgtype, msgcontent))
				msgcontent = [msg]
			lastmsgtype = msgtype
		if msgcontent:
			logentries[msgfunction].append((lastmsgtype, msgcontent))

	# clean logfiles to avoid repetitions
	for f in mylogfiles:
		try:
			os.unlink(os.path.join(path, f))
		except OSError:
			pass
	return logentries

_msgbuffer = {}
def _elog_base(level, msg, phase="other", key=None, color=None, out=None):
	""" Backend for the other messaging functions, should not be called 
	    directly.
	"""

	global _msgbuffer

	if color == None:
		color = "GOOD"

	formatted_msg = colorize(color, " * ") + msg + "\n"

	if out is None:
		sys.stdout.write(formatted_msg)
	else:
		out.write(formatted_msg)

	if key not in _msgbuffer:
		_msgbuffer[key] = {}
	if phase not in _msgbuffer[key]:
		_msgbuffer[key][phase] = []
	_msgbuffer[key][phase].append((level, msg))

	#raise NotImplementedError()

def collect_messages():
	global _msgbuffer

	rValue = _msgbuffer
	_reset_buffer()
	return rValue

def _reset_buffer():
	""" Reset the internal message buffer when it has been processed, 
	    should not be called directly.
	"""
	global _msgbuffer
	
	_msgbuffer = {}

# creating and exporting the actual messaging functions
_functions = { "einfo": ("INFO", "GOOD"),
		"elog": ("LOG", "GOOD"),
		"ewarn": ("WARN", "WARN"),
		"eqawarn": ("QA", "WARN"),
		"eerror": ("ERROR", "BAD"),
}

def _make_msgfunction(level, color):
	def _elog(msg, phase="other", key=None, out=None):
		""" Display and log a message assigned to the given key/cpv 
		    (or unassigned if no key is given).
		""" 
		_elog_base(level, msg,  phase=phase, key=key, color=color, out=out)
	return _elog

import sys
for f in _functions:
	setattr(sys.modules[__name__], f, _make_msgfunction(_functions[f][0], _functions[f][1]))
del f, _functions
