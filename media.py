#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

# Copyright 2006 Eli J. MacKenzie
# Inspired by `media` (Copyright 2005 İsmail Dönmez)
# Added Clementine support by JP Meijers - 2010/06/08


# If you wish to customize the formatting strings, do so in this table.
# Do not change the numbers unless you're changing the logic.
# Title, artist, and album will be set once the player is queried.
# See Player.format() for how these are used.


#Changing these 3 values will likely cause the script to fail
Title =4
Artist=2
Album =1

#To disable self-titled (eponymous) checking, subtract 8
SelfTitled=11

outputFormat="/me $intro $info [$player]"
formatStrings = {
    Title+SelfTitled   : "$title by $artist (eponymous)",
    SelfTitled         : "${artist}'s self-titled album",
    Title+Artist+Album : "$title by $artist on $album", #7,15
    Title+Artist       : "$title by $artist", #6,14
    Title+Album        : "$title from $album", #5,13
    Album+Artist       : "$album by $artist", #3,11
    Title              : "$title", #4,12
    Artist             : "$artist", #2,10
    Album              : "$album", #1,9
}

#Intro defaults to first type the player supports when a specific type was not demanded
formatVariables={'audio': 'is listening to', 'video': 'is watching'}

## Static player ranking list
## If you add a new player, you must add it here or it won't get checked when in audio-only or video-only modes.
playerRankings= {
    'video' :['kaffeine','kmplayer', 'kplayer', 'noatun', 'kdetv'],
    'audio' :['clementine', 'amarok', 'juk', 'noatun', 'kscd', 'kaffeine', 'kmplayer', 'amarok2', 'yammi', 'Audacious', 'xmms', 'MPD']
}

## Title, album and artist fields to be quoted depending on contents
# List the possible trigger characters here.
# If you want a '-', it must be first. if you want a '^', it must be last.
SIMPLE_FIXUP = '' #I use ' '

# If you want to use a regex for the above, specify it here in which case it will be used
REGEX_FIXUP = ''

# Quote chars to use:
QUOTE_BEFORE = '"'
QUOTE_AFTER  = '"'


  ###############################
 ## The Real work is done below
#############################

import os
import sys
import re
import string

try:
    IRC_SERVER = sys.argv[1]
    TARGET = sys.argv[2]
except IndexError:
    print >>sys.stderr, "This script is intended to be run from within Konversation."
    sys.exit(0)

if (sys.hexversion >> 16) < 0x0204:
    err="The media script requires Python 2.4."
    os.popen('qdbus org.kde.konversation /irc error "%s"' %(err))
    sys.exit(err)

import subprocess

# Python 2.5 has this ...
try:
    any(())
except NameError:
    def any(data):
        """Return true of any of the items in the sequence 'data' are true.

        (ie non-zero or not empty)"""
        try:
            return reduce(lambda x,y: bool(x) or bool(y), data)
        except TypeError:
            return False

def tell(data, feedback='info'):
    """Report back to the user"""
    l=['qdbus', 'org.kde.konversation', '/irc', feedback]
    if type(data) is type(''):
        l.append(data)
    else:
        l.extend(data)
    subprocess.Popen(l).communicate()

class Player(object):
    def __init__(self, display_name, playerType=None):
        if playerType is None:
            self.type = "audio"
        else:
            self.type=playerType
        self.displayName=display_name
        self.running = False
        d={}
        d.update(formatVariables)
        d['player']=self.displayName
        self._format = d

    def get(self, mode):
        data=self.getData()
        if any(data):
            self._format['info']=self.format(*data)
            if mode and mode != self.displayName:
                self._format['intro']=self._format[mode]
            else:
                self._format['intro']=self._format[self.type.replace(',','').split()[0]]
            return string.Template(outputFormat).safe_substitute(self._format)
        return ''

    def format(self, title='', artist='', album=''):
        """Return a 'pretty-printed' info string for the track.

        Uses formatStrings from above."""
        #Update args last to prevent non-sensical override in formatVariables
        x={'title':title, 'artist':artist, 'album':album}
        if FIXUP:
            for i,j in x.items():
                if re.search(FIXUP,j):
                    x[i]='%s%s%s'%(QUOTE_BEFORE,j,QUOTE_AFTER)
        self._format.update(x)
        n=0
        if title:
            n|=4 #Still binary to make you read the code ;p
        if artist:
            if artist == album:
                n|=SelfTitled
            else:
                n|=2
        if album:
            n|=1
        if n:
            return string.Template(formatStrings[n]).safe_substitute(self._format)
        return ''

    def getData(self):
        """Implement this to do the work"""
        return ''

    def reEncodeString(self, input):
        if input:
            try:
                input = input.decode('utf-8')
            except UnicodeError:
                try:
                    input = input.decode('latin-1')
                except UnicodeError:
                    input = input.decode('ascii', 'replace')
            except NameError:
                    pass
        return input.encode('utf-8')

    def test_format(self, title='', artist='', album=''):
        s=[]
        l=["to","by","on"]
        if title:
            s.append(title)
        else:
            album,artist=artist,album
            l.pop()
        if artist:
            s.append(artist)
        else:
            del l[1]
        if album:
            s.append(album)
        else:
            l.pop()
        t=["is listening"]
        while l:
            t.append(l.pop(0))
            t.append(s.pop(0))
        return ' '.join(t)

    def isRunning(self):
        return self.running

class DCOPPlayer(Player):
    def __init__(self, display_name, service_name, getTitle='', getArtist='', getAlbum='',playerType=None):
        Player.__init__(self, display_name, playerType)
        self.serviceName=service_name
        self._title=getTitle
        self._artist=getArtist
        self._album=getAlbum
        self.DCOP=""

    def getData(self):
        self.getService()
        return (self.grab(self._title), self.grab(self._artist), self.grab(self._album))

    def getService(self):
        if self.DCOP:
            return self.DCOP
        running = re.findall('^' + self.serviceName + "(?:-\\d*)?$", DCOP_ITEMS, re.M)
        if type(running) is list:
            try:
                running=running[0]
            except IndexError:
                running=''
        self.DCOP=running.strip()
        self.running=bool(self.DCOP)
        return self.DCOP

    def grab(self, item):
        if item and self.isRunning():
            return self.reEncodeString(os.popen("dcop %s %s"%(self.DCOP, item)).readline().rstrip('\n'))
        return ''

    def isRunning(self):
        self.getService()
        return self.running

class AmarokPlayer(DCOPPlayer):
    def __init__(self):
        DCOPPlayer.__init__(self,'Amarok','amarok','player title','player artist','player album')

    def getData(self):
        data=DCOPPlayer.getData(self)
        if not any(data):
            data=(self.grab('player nowPlaying'),'','')
            if not data[0]:
                return ''
        return data

class ClementinePlayer(Player):
    def __init__(self):
        Player.__init__(self, 'Clementine', 'audio')
        self.isRunning()

    def getData(self):
        playing=os.popen("qdbus org.mpris.clementine /Player PositionGet").readline().strip() != "0"
        if playing and self.isRunning():
            title = ''
            artist = ''
            album = ''
            for line in os.popen("qdbus org.mpris.clementine /Player GetMetadata").readlines():
                m = re.match("^title:\s(.+)", line)
                if m is not None:
                    title = m.group(1)
                m = re.match("^artist:\s(.+)", line)
                if m is not None:
                    artist = m.group(1)
                m = re.match("^album:\s(.+)", line)
                if m is not None:
                    album = m.group(1)
            return (title, artist, album)
        else:
            return ''

    def isRunning(self):
        qdbus_items=subprocess.Popen(['qdbus'], stdout=subprocess.PIPE).communicate()[0]
        running=re.findall(r'^ org.mpris.clementine\r?$', qdbus_items, re.M)
        if type(running) is list:
            try:
                running=running[0]
            except IndexError:
                running=''
        self.running=bool(running.strip())
        return self.running

class Amarok2Player(Player):
    def __init__(self):
        Player.__init__(self, 'Amarok2', 'audio')
        self.isRunning()

    def getData(self):
        playing=os.popen("qdbus org.mpris.amarok /Player PositionGet").readline().strip() != "0"
        if playing and self.isRunning():
            title = ''
            artist = ''
            album = ''
            for line in os.popen("qdbus org.mpris.amarok /Player GetMetadata").readlines():
                m = re.match("^title:\s(.+)", line)
                if m is not None:
                    title = m.group(1)
                m = re.match("^artist:\s(.+)", line)
                if m is not None:
                    artist = m.group(1)
                m = re.match("^album:\s(.+)", line)
                if m is not None:
                    album = m.group(1)
            return (title, artist, album)
        else:
            return ''

    def isRunning(self):
        qdbus_items=subprocess.Popen(['qdbus'], stdout=subprocess.PIPE).communicate()[0]
        running=re.findall(r'^ org.mpris.amarok\r?$', qdbus_items, re.M)
        if type(running) is list:
            try:
                running=running[0]
            except IndexError:
                running=''
        self.running=bool(running.strip())
        return self.running

import socket

class JukPlayer(Player):
    def __init__(self):
        Player.__init__(self, 'Juk', 'audio')
        self.isRunning()

    def getData(self):
        playing=os.popen("qdbus org.kde.juk /Player playin").readline().strip() != "false"
        if playing and self.isRunning():
            title = os.popen("qdbus org.kde.juk /Player trackProperty Title").readline().strip()
            artist = os.popen("qdbus org.kde.juk /Player trackProperty Artist").readline().strip()
            album = os.popen("qdbus org.kde.juk /Player trackProperty Album").readline().strip()
            return (title, artist, album)
        else:
            return ''

    def isRunning(self):
        qdbus_items=subprocess.Popen(['qdbus'], stdout=subprocess.PIPE).communicate()[0]
        running=re.findall(r'^ org.kde.juk\r?$', qdbus_items, re.M)
        if type(running) is list:
            try:
                running=running[0]
            except IndexError:
                running=''
        self.running=bool(running.strip())
        return self.running

import socket

class MPD(Player):
    def __init__(self, display_name):
        Player.__init__(self, display_name)

        self.host = "localhost"
        self.port = 6600
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(0.5)

        try:
            self.sock.connect((self.host, self.port))
            # just welcome message, we don't need it
            self.sock.recv(1024)
            self.running = True
        except socket.error:
            self.running = False

    def getData(self):
        if not self.running:
            return ''
        try:
            self.sock.send("currentsong\n")
            data = self.sock.recv(1024)
        except socket.error:
            return ''

        # mpd sends OK always, so if nothing to show, we should seek for at least 3 chars
        if len(data) < 4:
            return ''
        else:
            # if there is Artist, Title and Album, get it
            data=data.splitlines()
            d={}
            for i in data:
                if ':' not in i:
                    continue
                k,v=i.split(':',1)
                d[k.lower()]=self.reEncodeString(v.strip())
            data=(d.get('title',''),d.get('artist',''),d.get('album',''))
            if not any(data):
                return d.get('file','')
            return data

class StupidPlayer(DCOPPlayer):
    def getData(self):
        data=DCOPPlayer.getData(self)[0]
        if data:
            if data.startswith('URL'):
                # KMPlayer window titles in the form of "URL - file:///path/to/<media file> - KMPlayer"
                data=data.split(None,2)[2].rsplit(None,2)[0].rsplit('/')[-1]
            else:
                # KPlayer window titles in the form of "<media file> - KPlayer"
                data=data.rsplit(None,2)[0]
            return (data,'','')
        return ''

try:
    import xmms.common
    class XmmsPlayer(Player):
        def __init__(self, display_name):
            Player.__init__(self, display_name)

        def isRunning(self):
            self.running = xmms.control.is_running()
            return self.running

        def getData(self):
            if self.isRunning() and xmms.control.is_playing():
                # get the position in the playlist for current playing track
                index = xmms.control.get_playlist_pos();
                # get the title of the currently playing track
                return (self.reEncodeString(xmms.control.get_playlist_title(index)),'','')
            return ''

except ImportError:
    XmmsPlayer=Player

class AudaciousPlayer(Player):
    def __init__(self, display_name):
        Player.__init__(self, display_name)

    def isRunning(self):
        self.running = not os.system('audtool current-song')
        return self.running

    def getData(self):
        if self.isRunning() and not os.system('audtool playback-playing'):
            # get the title of the currently playing track
            data = os.popen('audtool current-song').read().strip()
            data_list = data.split(' - ')
            list_length = len(data_list)
            if list_length == 1:
                return (self.reEncodeString(data_list[0]),'','')
            elif list_length == 3:
                return (self.reEncodeString(data_list[-1]),data_list[0],data_list[1])
            else:
                return (self.reEncodeString(data),'','')
        else:
            return ''


def playing(playerList, mode=None):
    for i in playerList:
        s=i.get(mode)
        if s:
            tell([IRC_SERVER, TARGET, s], 'say' )
            return 1
    return 0

def handleErrors(playerList, kind):
    if kind:
        kind=kind.strip()
        kind=kind.center(len(kind)+2)
    else:
        kind= ' supported '
    x=any([i.running for i in playerList])
    if x:
        l=[i.displayName for i in playerList if i.isRunning()]
        err= "Nothing is playing in %s."%(', '.join(l))
    else:
        err= "No%splayers are running."%(kind,)
    tell(err,'error')

def run(kind):
    if not kind:
        kind = ''
        play=PLAYERS
    else:
        if kind in ['audio', 'video']:
            unsorted=dict([(i.displayName.lower(),i) for i in PLAYERS if kind in i.type])
            play=[unsorted.pop(i.lower(),Player("ImproperlySupported")) for i in playerRankings[kind]]
            if len(unsorted):
                play.extend(unsorted.values())
        else:
            play=[i for i in PLAYERS if i.displayName.lower() == kind]
            try:
                kind=play[0].displayName
            except IndexError:
                tell("%s is not a supported player."%(kind,),'error')
                sys.exit(0)

    if not playing(play, kind):
        print play
        handleErrors(play, kind)


#It would be so nice to just keep this pipe open and use it for all the dcop action,
#but of course you're supposed to use the big iron (language bindings) instead of
#the command line tools. One could consider `dcop` the bash dcop language binding,
#but of course when using shell you don't need to be efficient at all, right?

try:
    DCOP_ITEMS=subprocess.Popen(['dcop'], stdout=subprocess.PIPE).communicate()[0]  #re.findall("^amarok(?:-\\d*)?$",l,re.M)
except OSError:
    DCOP_ITEMS=""

# Add your new players here. No more faulty logic due to copy+paste.

PLAYERS = [
AmarokPlayer(),
JukPlayer(),
DCOPPlayer("JuK","juk","Player trackProperty Title","Player trackProperty Artist","Player trackProperty Album"),
DCOPPlayer("Clementine","clementine","Player trackProperty Title","Player trackProperty Artist","Player trackProperty Album"),
DCOPPlayer("Noatun",'noatun',"Noatun title",playerType='audio, video'),
DCOPPlayer("Kaffeine","kaffeine","KaffeineIface title","KaffeineIface artist","KaffeineIface album",playerType='video, audio'),
StupidPlayer("KMPlayer","kmplayer","kmplayer-mainwindow#1 caption",playerType="video audio"),
StupidPlayer("KPlayer","kplayer","kplayer-mainwindow#1 caption",playerType="video audio"),
DCOPPlayer("KsCD","kscd","CDPlayer currentTrackTitle","CDPlayer currentArtist","CDPlayer currentAlbum"),
DCOPPlayer("kdetv","kdetv","KdetvIface channelName",playerType='video'),
Amarok2Player(),
ClementinePlayer(),
DCOPPlayer("Yammi","yammi","YammiPlayer songTitle","YammiPlayer songArtist","YammiPlayer songAlbum"),
AudaciousPlayer('Audacious'), XmmsPlayer('XMMS'),
MPD('MPD')
]

# Get rid of players that didn't get subclassed so they don't appear in the available players list
for i in PLAYERS[:]:
    if type(i) is Player:
        PLAYERS.remove(i)

if REGEX_FIXUP:
    FIXUP=REGEX_FIXUP
elif SIMPLE_FIXUP:
    FIXUP="[%s]"%(SIMPLE_FIXUP)
else:
    FIXUP=''

# It all comes together right here
if __name__=="__main__":

    if not TARGET:
        s="""media v2.0.1 for Konversation 1.0. One media command to rule them all, inspired from Kopete's now listening plugin.
Usage:
        "\00312/media\017" - report what the first player found is playing
        "\00312/media\017 [ '\00312audio\017' | '\00312video\017' ]" - report what is playing in a supported audio or video player
        "\00312/media\017 { \00312Player\017 }" - report what is playing in \00312Player\017 if it is supported

        Available players are:
                """ + ', '.join([("%s (%s)"%(i.displayName,i.type)) for i in PLAYERS])

        for i in s.splitlines():
            tell(i)
        #tell("%s"%(len(s.splitlines()),))
        # called from the server tab
        pass
    else:
        try:
            kind = sys.argv[3].lower()
        except IndexError:
            kind = None

        run(kind)

