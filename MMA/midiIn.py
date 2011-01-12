
# midiIn.py

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

"""

import os

import MMA.midiM
import MMA.file

import gbl
from   MMA.common import *
from   MMA.alloc import trackAlloc



# The following set of variables are global. A bit ugly :)

midifile = ''   # The imported MIDI file (data) as a long string
offset = 0      # Current pointer into the MIDI file 

# These are the start/end points for the included file. They are in
# beats, but are adjusted after the file is opened to ticks.

istart=0
iend = 0xffffff

octAdjust = 0
volAdjust = 100
firstNote = 0   # signals where 1st note is in file in ticks
ignorePC = 1      # skip program changes in input file

""" Helper functions

    It might be better to have these
    functions setup in midiM.py ... but it's easier just
    now to have it here. The main problem is that we are
    reading from a buffer and don't know how many bytes to
    pass back and forth.
"""


def mvarlen():
    """ Convert variable length midi value to int. """

    global offset

    x=0L
    for i in range(4):

        try:
            byte=ord(midifile[offset])
            offset += 1
        except:
            error("Invalid MIDI file include (varlen->int)")

        if byte < 0x80:
            x = ( x << 7 ) + byte
            break
        else:
            x = ( x << 7 ) + ( byte & 0x7f )

    return int(x)


def chars(count):
    """ Return 'count' chars from file (updates global pointer). """

    global offset

    bytes=midifile[offset:offset+count]
    offset+=count
    return bytes


def m1i():
    """ Get 1 byte (updates global pointer). """

    global offset

    try:
        byte = midifile[offset]
        offset += 1
    except:
        error("Invalid MIDI file include (byte, offset=%s)" % offset)

    return ord(byte)


def m32i():
    """ Convert 4 bytes to integer. """

    global offset

    x = 0L
    for i in range(4):
        try:
            byte = midifile[offset]
            offset += 1
        except:
            error("Invalid MIDI file include (i32->int, offset=%s)" % offset)
        x = (x << 8) + ord(byte)

    return int(x)


def m16i():
    """ Convert 2 bytes to integer. """

    global offset

    x = 0L
    for i in range(2):
        try:
            byte = midifile[offset]
            offset += 1
        except:
            error("Invalid MIDI file include (i16->int, offset=%s)" % offset)
        x = (x << 8) + ord(byte)

    return int(x)

def readMidi(filename):
    """ Read existing midi file, parse and return events, textevents & lyrics """

    global offset, midifile, beatDivision, istart, iend, firstNote, ignorePC

    try:
        inpath = file(filename, "rb")
    except:
        error("Unable to open MIDI file %s for reading" % filename)

    midifile=inpath.read()
    inpath.close()

    # Create our storage:
    #    A dic with the channels 0-15 as keys for the midi note events
    #    2 lists for lyrics and text events. These have tuples for (time, text)

    events={}
    for c in range(0,16):
        events[c]=[]

    textEvs=[]
    lyricEvs=[]

    # Ensure this is valid header

    hd=midifile[0:4]
    if hd != 'MThd':
        error("Expecting 'MThd', %s not a standard midi file" % filename)

    offset = 4
    a = m32i()

    if a != 6:
        error("Expecting a 32 bit value of 6 in header")

    format=m16i()

    if format not in (0,1):
        error("MIDI file format %s not recognized" % format)

    ntracks=m16i()
    beatDivision=m16i()

    if beatDivision != gbl.BperQ:
        warning("MIDI file '%s' tick/beat of %s differs from MMA's "
            "%s. Will try to compensate" %
            (filename, beatDivision, gbl.BperQ))

    # Adjust start/end to the file's tick

    istart *= beatDivision
    iend   *= beatDivision

    midievents={}
    firstNote = 0xffffff

    for tr in range(ntracks):
        tm=0

        hdr = midifile[offset:offset+4]
        offset+=4

        if hdr != 'MTrk':
            error("Malformed MIDI file in track header")
        trlen = m32i()    # track length, not used?

        lastevent = None

        """ Parse the midi file. We have to parse off each event, even
            though many will just be thrown away. You can't just skip around
            in a midi file :) In the future we might decide to include meta
            stuff, etc. Or, we may not :) For now, we keep:
                - note on
                - note off
                 - key pressure
                - control change
                - program change
                - channel pressure
                - pitch blend
                - text event
                - lyric event
        """

        while 1:
            tm += mvarlen()        # adjust total offset by delta

            ev=m1i()

            if ev < 0x80:
                if not lastevent:
                    error("Illegal running status in %s at %s" % (midifile, offset))
                offset -= 1
                ev=lastevent


            sValue = ev>>4        # Shift MSBs to get a 4 bit value
            channel = ev & 0x0f

            if sValue == 0x8:        # note off event

                note=m1i()
                vel=m1i()

                if octAdjust and channel != 10:
                    note += octAdjust
                    while note < 0:  note += 12
                    while note >127: note -= 12
                events[channel].append([tm, ev & 0xf0, chr(note)+chr(vel)])

            elif sValue == 0x9:        # note on event
                if tm < firstNote:
                    firstNote = tm
                note=m1i()
                vel=m1i()

                if octAdjust and channel != 10:
                    note += octAdjust
                    while note < 0:  note += 12
                    while note >127: note -= 12

                if volAdjust != 100:
                    vel = int( (vel*volAdjust)/100)
                    if vel<0: vel=1
                    if vel>127: vel=127

                events[ev & 0xf].append([tm, ev & 0xf0, chr(note)+chr(vel)])

            elif sValue == 0xa:        # key pressure
                events[ev & 0xf].append([tm, ev & 0xf0, chars(2)])

            elif sValue == 0xb:        # control change
                events[ev & 0xf].append([tm, ev & 0xf0, chars(2)])
            
            elif sValue == 0xc:        # program change
                if ignorePC:  # default is to ignore these
                    offset += 1  
                else:         # set with option IgnorePC=1
                    events[ev & 0xf].append([tm, ev & 0xf0, chars(1)])

            elif sValue == 0xd:        # channel pressure
                events[ev & 0xf].append([tm, ev & 0xf0, chars(1)])

            elif sValue == 0xe:        # pitch blend
                events[ev & 0xf].append([tm, ev & 0xf0, chars(2)])

            elif sValue == 0xf:        # system, mostly ignored
                if ev == 0xff:        # meta events
                    a=m1i()

                    if a == 0x00:    # sequence number
                        l=mvarlen()
                        offset += l

                    elif a == 0x01: # text (could be lyrics)
                        textEvs.append((tm, chars(mvarlen())))

                    elif a == 0x02: # copyright
                        l=mvarlen()
                        offset += l

                    elif a == 0x03: # seq/track name
                        l=mvarlen()
                        offset += l

                    elif a == 0x04: # instrument name
                        l=mvarlen()
                        offset += l

                    elif a == 0x05: # lyric
                        lyricEvs.append((tm, chars(mvarlen())))

                    elif a == 0x06: # marker
                        l=mvarlen()
                        offset += l

                    elif a == 0x07: # cue point
                        l=mvarlen()
                        offset += l

                    elif a == 0x21: # midi port
                        l=mvarlen()
                        offset += l

                    elif a == 0x2f: # end of track
                        l=mvarlen()
                        offset += l
                        break

                    elif a == 0x51: #tempo
                        l=mvarlen()
                        offset += l

                    elif a == 0x54: # SMPTE offset
                        l=mvarlen()
                        offset += l

                    elif a == 0x58: # time sig
                        l=mvarlen()
                        offset += l

                    elif a == 0x59: # key sig
                        l=mvarlen()
                        offset += l

                    else:        # probably 0x7f, proprietary event
                        l=mvarlen()
                        offset += l


                elif ev == 0xf0:    # system exclusive
                    l=mvarlen()
                    offset += l

                elif ev == 0xf2:    # song position pointer, 2 bytes
                    offset += 2

                elif ev == 0xf3:    # song select, 1 byte
                    offset += 1

                else:        # all others are single byte commands
                    pass

            if ev >= 0x80 and ev <= 0xef:
                lastevent = ev

    return (events, textEvs, lyricEvs)


######################################################
## Main function, called from parser.

def midiinc(ln):
    """ Include a MIDI file into MMA generated files. """

    global midifile, offset, octAdjust, volAdjust, firstNote, istart, iend, ignorePC

    filename = ''
    doLyric = 0
    doText = 0
    channels = []
    transpose = None
    stripSilence = 1
    report = 0

    notopt, ln = opt2pair(ln)

    if notopt:
        error("MidiInc expecting cmd=opt pairs, not '%s'." % ' '.join(notopt) )
        
    for cmd, opt in ln:
        cmd=cmd.upper()

        if cmd == 'FILE':
            filename = MMA.file.fixfname(opt)

        elif cmd == 'VOLUME':
            volAdjust = stoi(opt)

        elif cmd == 'OCTAVE':
            octAdjust = stoi(opt)
            if octAdjust < -4 or octAdjust > 4:
                error("Octave adjustment must be -4 to 4, not %s" % opt)
            octAdjust *= 12

        elif cmd == 'TRANSPOSE':
            transpose = stoi(opt)
            if transpose < -24 or transpose > 24:
                error("Transpose must be -24 to 24, not %s" % opt)

        elif cmd == 'START':
            istart = stof(opt)

        elif cmd == 'END':
            iend = stof(opt)

        elif cmd == 'TEXT':
            opt=opt.upper()
            if opt in ("ON", '1'):
                doText=1
            elif opt in ("OFF", '0'):
                doText=0
            else:
                error("MidiInc Text= expecting 'ON' or 'OFF'")

        elif cmd == 'LYRIC':
            opt=opt.upper()
            if opt in ("ON", '1'):
                doLyric=1
            elif opt in ("OFF", '0'):
                doLyric=0
            else:
                error("MidiInc Lyric: expecting 'ON' or 'OFF'")
        
        elif cmd == "REPORT":
            opt=opt.upper()
            if opt in ("ON", '1'):
                report=1
            elif opt in ("OFF", '0'):
                report=0
            else:
                error("MidiInc Report: expecting 'ON' or 'OFF'")
        

        elif cmd == "STRIPSILENCE":
            opt=opt.upper()
            if opt in ("OFF", '0'):
                stripSilence = 0
            elif opt == "ON": # this is the default
                stripSilence = -1
            else:
                stripSilence = stoi(opt,
                     "MIdiInc StripSilence= expecting 'value', 'On' or 'Off', "
                      "not %s" % opt)

        elif cmd == "INCLUDEPC":
            opt=op.upper()
            if opt in ("TRUE", "ON", "1"):   # default
                ignorePC=1
            elif opt in ("FALSE", "OFF", "0"):  # use program change in imported
                ignorePC=0
            else:
                error ("MIdiInc IncludePC= expecting 'True' or 'False', not %s" % opt)

        # If none of the above matched a CMD we assume that it is
        # a trackname. Keep this as the last test!

        else:
            trackAlloc(cmd, 0)
            if not cmd in gbl.tnames:
                error("MidiInc: %s is not a valid MMA track" % cmd)

            opt = opt.split(',')
            riffmode=0
            printriff=0
            ch = None
            for o in opt:
                o=o.upper()
                if o == 'RIFF':
                    riffmode = 1
                elif o == 'PRINT':
                    printriff = 1
                    riffmode = 1
                else:
                    if ch != None:
                        error("MidiInc: Only one channel assignment per track.")
                    ch = stoi(o)
                
            if ch < 1 or ch > 16:
                error("MidiInc: MIDI channel for import must be 1..16, not %s" % ch)

            channels.append( (cmd, ch-1, riffmode, printriff))


    if report:  # don't bother with channel tests, etc.
        gbl.noWarn=1
        events, textEvs, lyricEvs = readMidi(filename)

        print "MIDI File %s successfully read." % filename
        print "Total Text events: %s"  % len(textEvs)
        print "Total Lyric events: %s" % len(lyricEvs)
        if beatDivision != gbl.BperQ:
            s = "(MMA uses %s, MidiInc will compensate)" % gbl.BperQ
        else: 
            s=''
        print "Ticks per quarter note: %s %s" % (beatDivision, s)
        print

        for ch in sorted(events.keys()):
            if not events[ch]:
                continue

            fnote = fevent = 0xffffff
            ncount = 0
            for ev in events[ch]:
                delta = ev[0]
                if delta < fevent:
                    fevent = delta
                if ev[1]>>4 == 0x9:
                    if delta < fnote:
                        fnote = delta
                    if ord(ev[2][1]):
                        ncount +=1
            print "Channel %2s: First event %-8s" % (ch+1, fevent),
            if ncount:
                print "First Note %-8s Total Notes %-4s" %  (fnote, ncount)
            else:
                print
        print


        print "No data generated!"
        sys.exit(0)




    if not channels:
        if doLyric or doText:
            warning("MidiInc: no import channels specified, "
                    "only text or lyrics imported")
        else:
            error("MidiInc: A channel to import and a destination "
                  "track must be specified")

    if (istart >= iend) or (istart < 0) or (iend < 0):
         error("MidiInc range invalid: start=%s, end=%s" % (istart, iend))

    if gbl.debug:
        print "MidiInc: file=%s, Volume=%s, Octave=%s, Transpose=%s, Lyric=%s, " \
            "Text=%s, Range=%s..%s StripSilence=%s" \
            % (filename, volAdjust, octAdjust, transpose, doLyric, doText, \
                   istart, iend, stripSilence)
        for t, ch, riffmode, riffprint in channels:
            o=''
            if riffmode:
                o=',riff'
            elif printriff:
                o=',riff,print'
            print "MidiInc: Channel %s-->%s%s" % (ch+1, t, o),
        print

    # If transpose was NOT set, use the global transpose value
    # Note special riff value as well. Need to double adjust since
    # the riff import will do its own adjustment.

    if transpose == None:
        transpose = gbl.transpose
        riffTranspose = -gbl.transpose
    else:
        riffTranspose = 0

    octAdjust += transpose    # this takes care of octave and transpose

    events, textEvs, lyricEvs = readMidi(filename)


    # Midi file parsed, add selected events to mma data

    beatad = gbl.BperQ / float(beatDivision)
    if not stripSilence:
        firstNote = 0
    elif stripSilence > 0:
        firstNote = stripSilence

    if doText:
        inst=0
        disc=0
        for tm,tx in textEvs:
            delta = tm-firstNote
            if delta >= istart and delta <= iend:
                gbl.mtrks[0].addText(gbl.tickOffset + int(delta * beatad), tx)
                inst+=1
            else:
                disc+=1
        if gbl.debug:
            print"MidiInc text events: %s inserted, %s out of range." % (inst, disc)

    if doLyric:
        inst=0
        disc=0
        for tm, tx in lyricEvs:
            delta = tm-firstNote
            if delta >= istart and delta <= iend:
                gbl.mtrks[0].addLyric(gbl.tickOffset + int(delta * beatad), tx)
                inst+=1
            else:
                disc+=1
        if gbl.debug:
            print"MidiInc lyric events: %s inserted, %s out of range." % (inst, disc)


    for n,c, riffmode, printriff in channels:
        if not len(events[c]):
            warning("No data to assign from imported channel %s to track %s" % (c+1, n))

    inst=0
    disc=0

    for tr, ch, riffmode, printriff in channels:

        if gbl.tnames[tr].disable:   # skip if disabled track 
            continue

        t=gbl.tnames[tr]
        if not t.channel:
            t.setChannel()

        if riffmode:
            riff = []
            if t.vtype not in ('MELODY', 'SOLO'):
                error("MidiInc Riff only works on Melody/Solo tracks, not '%s'." % t.name)

        t.clearPending()
        if t.voice[0] != t.ssvoice:
            gbl.mtrks[t.channel].addProgChange( gbl.tickOffset, t.voice[0], t.ssvoice)

        channel = t.channel
        track = gbl.mtrks[channel]

        for ev in events[ch]:
            delta = ev[0]-firstNote

            if delta >= istart and delta <= iend:
                if riffmode:
                    offset = int(delta * beatad) 
                    x=ev[1]>>4
                    if x != 0x09 and x != 0x08:
                        continue
                    pitch=ord(ev[2][0])
                    velocity=ord(ev[2][1])
                    if x == 0x8:
                        velocity = 0
                    riff.append([offset, pitch, velocity]) 
                else:
                    offset = gbl.tickOffset + int(delta * beatad)
                    track.addToTrack( offset, chr(ev[1] | channel-1) + ev[2] )
                inst+=1
            else:
                disc+=1

        if riffmode:
            createRiff(riff, tr, printriff, riffTranspose, beatad)

    if gbl.debug:
            print"MidiInc events: %s inserted, %s out of range." % (inst, disc)



def createRiff(riff, tname, pt, riffTranspose, beatad):

    # convert list of ON values to durations. We need to
    # look at each event and, if an on-event, search forward
    # for an off. Subtract 2 times and save in new list.

    if gbl.tnames[tname].riff:
        error("MidiInc: Data already pending for %s." % tname)

    missed = 0
    events=[]
    riff.sort()
    for i in range(len(riff)):
        duration = None
        offset,pitch,velocity = riff[i]
        if velocity:
            for t in range(i,len(riff)):
                off1, pitch1, vel1 = riff[t]
                if not vel1 and pitch1 == pitch:
                    duration = off1 - offset
                    break
            if duration:
                if riffTranspose:
                    pitch += riffTranspose
                    while pitch > 127:  pitch -= 12
                    while pitch < 0:    pitch += 12
                events.append([offset, duration, pitch, velocity])

            else:
                missed += 1

    if missed:
        warning("MidiInc Riff: conversion missed %s notes in track %s" % (missed, tname))

    # We have a list of events: [offset, duration, pitch, velocity]...
    # create yet another list with the events put into bars. Easier
    # this time to use a dict

    tickBar = gbl.BperQ * gbl.QperBar
    bars = {}

    for offset, duration, pitch, velocity in events:
        b = (offset/tickBar)
        if not b in bars:
            bars[b]=''
        bars[b]+=  "<Offset=%s> %st %s/%s;" % \
                  ( int(offset % tickBar), duration, pitch, velocity)

    w = gbl.noWarn
    gbl.noWarn=1
    for a in bars:
        if pt:
            print "%s Riff %s" % (tname, bars[a])
        else:
            gbl.tnames[tname].setRiff(bars[a])
    w = gbl.noWarn

