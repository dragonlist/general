# midifuncs.py

"""
This module is an integeral part of the program
MMA - Musical Midi Accompaniment.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Bob van der Poel <bob@mellowood.ca>

Low level entry points, mostly called directly from the parser.
"""


import gbl
import MMA.mdefine
from   MMA.common import *

# non-track functions


def setTimeSig(ln):
    """ Set the midi time signature. """

    if len(ln) == 1:
        a=ln[0].upper()
        if a == 'COMMON':
            ln=('4','4')
        elif a == 'CUT':
            ln=('2','2')

    if len(ln) != 2:
        error("TimeSig: Usage (num dem) or ('cut' or 'common')")

    nn = stoi(ln[0])

    if nn<1 or nn>126:
        error("Timesig NN must be 1..126")

    dd = stoi(ln[1])
    if     dd == 1:  dd = 0
    elif dd == 2:  dd = 1
    elif dd == 4:  dd = 2
    elif dd == 8:  dd = 3
    elif dd == 16: dd = 4
    elif dd == 32: dd = 5
    elif dd == 64: dd = 6
    else:
        error("Unknown value for timesig denominator")

    MMA.midi.timeSig.set(nn,dd)


def midiMarker(ln):
    """ Parse off midi marker. """

    if len(ln) == 2:
        offset = stof(ln[0])
        msg = ln[1]
    elif len(ln) == 1:
        offset = 0
        msg = ln[0]
    else:
        error("Usage: MidiMark [offset] Label")

    offset = int(gbl.tickOffset + (gbl.BperQ * offset))
    if offset < 0:
        error("MidiMark offset points before start of file")

    gbl.mtrks[0].addMarker(offset, msg)


def setMidiCue(ln):
    """ Insert MIDI cue (text) event into meta track."""

    if not ln:
        error("MidiCue requires text.")

    gbl.mtrks[0].addCuePoint(gbl.tickOffset, ' '.join(ln))


def rawMidi(ln):
    """ Send hex bytes as raw midi stream. """

    mb=''
    for a in ln:
        a=stoi(a)

        if a<0 or a >0xff:
            error("All values must be in the range 0 to 0xff, not '%s'" % a)

        mb += chr(a)

    gbl.mtrks[0].addToTrack(gbl.tickOffset, mb)

    if gbl.debug:
        print "Inserted raw midi in metatrack: ",
        for b in mb:
            print '%02x' % ord(b),
        print


def setMidiFileType(ln):
    """ Set some MIDI file generation flags. """

    if not ln:
        error("USE: MidiFile [SMF=0/1] [RUNNING=0/1]")

    for l in ln:
        try:
            mode, val = l.upper().split('=')
        except:
            error("Each arg must contain an '=', not '%s'" % l)

        if mode == 'SMF':
            if val == '0':
                gbl.midiFileType = 0
            elif val == '1':
                gbl.midiFileType = 1
            else:
                error("Use: MIDIFile SMF=0/1")

            if gbl.debug:
                print "Midi Filetype set to", gbl.midiFileType


        elif mode == 'RUNNING':
            if val == '0':
                gbl.runningStatus = 0
            elif val == '1':
                gbl.runningStatus = 1
            else:
                error("Use: MIDIFile RUNNING=0/1")

            if gbl.debug:
                print "Midi Running Status Generation set to",
                if gbl.runningStatus:
                    print 'ON (Default)'
                else:
                    print 'OFF'


        else:
            error("Use: MIDIFile [SMF=0/1] [RUNNING=0/1]")


def setChPref(ln):
    """ Set MIDI Channel Preference. """

    if not ln:
        error("Use: ChannelPref TRACKNAME=CHANNEL [...]")

    for i in ln:
        if '=' not in i:
            error("Each item in ChannelPref must have an '='")

        n,c = i.split('=')

        c = stoi(c, "Expecting an integer for ChannelPref, not '%s'" % c)

        if c<1 or c>16:
            error("Channel for ChannelPref must be 1..16, not %s" % c)

        gbl.midiChPrefs[n.upper()]=c

    if gbl.debug:
        print "ChannelPref:",
        for n,c in gbl.midiChPrefs.items():
            print "%s=%s" % (n,c),
        print


def setMidiCopyright(ln):
    """ Add a copyright message to the file. This is inserted into
        the meta track at offset 0. 
    """

    if not ln:
        error("MidiCopyright needs text message.")

    gbl.mtrks[0].addCopyright(0, ' '.join(ln))


  
def setMidiName(ln):
    """ Set global/meta track name. This will overwrite the song name set in main."""

    if not ln:
        error("Use: TrackName text")

    gbl.mtrks[0].addTrkName(0, ' '.join(ln) )

def setMidiText(ln):
    """ Set midi text into meta track."""

    if not ln:
        error("Use: MidiText text")

    gbl.mtrks[0].addText(gbl.tickOffset, ' '.join(ln))


################################################
## Track functions


def trackGlis(name, ln):
    """ Enable/disable portamento. """

    if len(ln) != 1:
        error("Use: %s MidiGlis NN, off=0, 1..127==on" % name)

    gbl.tnames[name].setGlis(ln[0])



def trackPan(name, ln):
    """ Set the Midi Pan value for a track."""

    if len(ln)==1 or len(ln)==3:
        gbl.tnames[name].setPan(ln)
    else:
        error("Use %s MidiPAN [Value] OR [Initvalue DestValue Beats]." % name)


def trackMidiText(name, ln):
    """ Insert midi text event. """

    if not ln:
        error("Use: %s Text" % name)


    # this calls func in pat.py since the event is queued and only
    # sent if the track is created.

    gbl.tnames[name].setMidiText(' '.join(ln))

 
def trackMidiCue(name, ln):
    """ Insert MIDI cue (text) event."""

    if not ln:
        error("Use: %s TrackName" % name)

    # this calls func in pat.py since the event is queued and only
    # sent if the track is created.

    gbl.tnames[name].setMidiCue(' '.join(ln))


def trackMidiExt(ln):
    """ Helper for trackMidiSeq() and trackMidiVoice()."""

    ids=1
    while 1:
        sp = ln.find("{")

        if sp<0:
            break

        ln, s = pextract(ln, "{", "}", 1)
        if not s:
            error("Did not find matching '}' for '{'")

        pn = "_%s" % ids
        ids+=1

        MMA.mdefine.mdef.set(pn, s[0])
        ln = ln[:sp] + ' ' + pn + ' ' + ln[sp:]

    return ln.split()



def trackMidiSeq(name, ln):
    """ Set reoccurring MIDI command for track. """

    if not ln:
        error("Use %s MidiSeq Controller Data" % name)

    if ln[0][0] != '{':      # add {} wrapper if missing
        ln.insert(0, '{')
        ln.extend('}')

    if len(ln) == 1 and ln[0]== '-':
        gbl.tnames[name].setMidiSeq('-')
    else:
        gbl.tnames[name].setMidiSeq( trackMidiExt(' '.join(ln) ))


def trackMidiVoice(name, ln):
    """ Set single shot MIDI command for track. """

    if not ln:
        error("Use %s MidiVoice Controller Data" % name)

    if ln[0][0] != '{':      # add {} wrapper if missing
        ln.insert(0, '{')
        ln.extend('}')

    if len(ln) == 1 and ln[0] == '-':
        gbl.tnames[name].setMidiVoice( '-' )
    else:
        gbl.tnames[name].setMidiVoice( trackMidiExt(' '.join(ln) ))


def trackMidiClear(name, ln):
    """ Set MIDI command to send at end of groove. """

    if not ln:
        error("Use %s MIDIClear Controller Data" % name)


    if len(ln) == 1 and ln[0] == '-':
        gbl.tnames[name].setMidiClear( '-' )
    else:
        ln=' '.join(ln)
        if '{' in ln or '}' in ln:
            error("{}s are not permitted in %s MIDIClear command" % name)
        gbl.tnames[name].setMidiClear( trackMidiExt( '{' + ln + '}' ))


   
def trackMidiName(name,ln):
    """ Set channel track name."""

    if not ln:
        error("Use: %s TrackName" % name)

    # this calls func in pat.py since the event is queued and only
    # sent if the track is created.

    gbl.tnames[name].setTname(ln[0])

