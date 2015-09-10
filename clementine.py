__module_name__ = "xchat-clementine"
__module_version__ = "1.0"
__module_description__ = "Get NP information from Clementine"
from dbus import Bus, DBusException
import xchat
import os
import sys
import re
import string
bus = Bus(Bus.TYPE_SESSION)
global nowplaying
global time
global chan
global cnc
nowplaying = " "
def get_clem():
    try:
        return bus.get_object('org.mpris.clementine', '/Player')
    except:
        print "\x02Clementine is not running."
        return "stop"

def command_np(word=None, word_eol=None, userdata=None):
    global nowplaying
    global chan
    global cnc
    chan = xchat.get_info("channel")
    cnc = xchat.find_context(channel = chan)
    clem = get_clem()
    if clem <> "stop":
       clemp = bus.get_object('org.mpris.clementine', '/Player')
       clemmd = clemp.GetMetadata()
       if clem:
	   pos = clem.PositionGet()
	   album=""
	   artist=""
	   if 'artist' in clemmd:
		artist = " by " + unicode(clemmd['artist']).encode('utf-8')
	   if 'album' in clemmd:
		album = " on " + unicode(clemmd['album']).encode('utf-8')
	   if ('title' in clemmd) and (pos <> 0):
		nowplaying = unicode(clemmd['title'])
	        pos = clem.PositionGet()
		listeningto = "me is listening to " + nowplaying.encode('utf-8')
		if artist <> "":
		    listeningto = listeningto + artist
		if album <> "":
		    listeningto = listeningto + album

		posM='%02d'%(int)(pos/60000);
		posS='%02d'%(int)((pos/1000)%60);

		cnc.command(listeningto+" @ "+unicode(posM).encode('utf-8')+':'+unicode(posS).encode('utf-8')+" [Clementine]")
	   else:
		print "\x02No song is currently playing."
    return xchat.EAT_ALL


def getData(word=None, word_eol=None, userdata=None):
	global chan
	global cnc
	chan = xchat.get_info("channel")
	cnc = xchat.find_context(channel = chan)
	playing=os.popen("ssh jpm@192.168.1.101 \"source dbusScript.sh ; qdbus org.mpris.clementine /Player  PositionGet\"").readlines()
	
	if len(playing)>2 and playing[2] != "0":
		title = ''
		artist = ''
		album = ''
		pos = int(playing[2])

		for line in os.popen("ssh jpm@192.168.1.101 \"source dbusScript.sh ; qdbus org.mpris.clementine /Player GetMetadata\"").readlines():
			#print line
			if line == "":
				break
			m = re.match(".*title:\s(.+)", line)
			if m is not None:
			    title = m.group(1)
			m = re.match(".*artist:\s(.+)", line)
			if m is not None:
			    artist = " by " + m.group(1)
			m = re.match(".*album:\s(.+)", line)
			if m is not None:
			    album = " on " + m.group(1)
			#	    return (title, artist, album)

		listeningto = "me is listening to " + title
		if artist <> "":
		    listeningto = listeningto + artist
		if album <> "":
		    listeningto = listeningto + album

		posM='%02d'%(int)(pos/60000);
		posS='%02d'%(int)((pos/1000)%60);

		cnc.command(listeningto+" @ "+unicode(posM).encode('utf-8')+':'+unicode(posS).encode('utf-8')+" [Clementine on 192.168.1.101]")
	else:
		print "\x02No song is currently playing."

	return xchat.EAT_ALL


#def strt(word, word_eol, userdata):
#	global chan
#	global cnc	

#	print "Now playing enabled"
#	time = xchat.hook_timer(5000,command_np)
#	return xchat.EAT_ALL

#def quit(word, word_eol, userdata):
#	global time
#	print "Now Playing is off"
#	xchat.unhook(time)
#	return xchat.EAT_ALL


xchat.hook_command("MEDIA",    command_np,                 help="Displays current playing song.")
xchat.hook_command("MEDIA2",    getData,                 help="Displays current playing song.")
#xchat.hook_command("NPOFF",    quit,                 help="Disables display of current playing song.")
print "\x02xchat-clementine plugin loaded"
