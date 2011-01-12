
# parse.py

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


This module does all file parsing. Most commands
are passed to the track classes; however, things
like TIME, SEQRND, etc. which just set global flags
are completely handled here.

"""

import os
import random
import copy

import gbl
from   MMA.common import *

import MMA.notelen
import MMA.chords
import MMA.file
import MMA.midi
import MMA.midifuncs
import MMA.midiIn
import MMA.midinote
import MMA.grooves
import MMA.docs
import MMA.auto
import MMA.translate
import MMA.patSolo
import MMA.mdefine
import MMA.volume
import MMA.seqrnd
import MMA.patch
import MMA.paths
import MMA.swing

import gbl

from   MMA.common import *
from   MMA.lyric import lyric
from   MMA.macro import macros
from   MMA.alloc import trackAlloc
from   MMA.keysig import keySig

lastChord = None   # tracks last chord for "/ /" data lines.

beginData = []      # Current data set by a BEGIN statement
beginPoints = []    # since BEGINs can be nested, we need ptrs for backing out of BEGINs

gmagic = 9988   # magic name for groove saved with USE



""" This table is passed to the track classes. It has
    an instance for each chord in the current bar.
"""

class CTable:
    name      = None    # Chord name (not used?)
    chord     = None    # A pointer to the chordNotes structures
    chStart   = None    # where in the bar the chord starts (in ticks, 0..)
    chEnd     = None    # where it ends (in ticks)
    chordZ    = None    # set if chord is tacet
    arpeggioZ = None    # set if arpeggio is tacet
    walkZ     = None    # set if walking bass is tacet
    drumZ     = None    # set if drums are tacet
    bassZ     = None    # set if bass is tacet
    scaleZ    = None    # set if scale track is tacet
    ariaZ     = None    # set if aria track is tacet
    plectrumZ = None    # set if plectrum is tacet


########################################
# File processing. Mostly jumps to pats
########################################


def parseFile(n):
    """ Open and process a file. Errors exit. """

    fp=gbl.inpath

    f=MMA.file.ReadFile(n)

    parse(f)
    gbl.inpath=fp

    if gbl.debug:
        print "File '%s' closed." % n


def parse(inpath):
    """ Process a mma input file. """

    global beginData, lastChord

    gbl.inpath = inpath

    curline = None

    while 1:
        curline = inpath.read()

        if curline == None:   # eof, exit parser
            break

        l = macros.expand(curline)

        """ Handle BEGIN and END here. This is outside of the Repeat/End
            and variable expand loops so SHOULD be pretty bullet proof.
            Note that the beginData stuff is global to this module ... the
            Include/Use directives check to make sure we're not doing that
            inside a Begin/End.

            beginData[] is a list which we append to as more Begins are
            encountered.

            The placement here is pretty deliberate. Variable expand comes
            later so you can't macroize BEGIN ... I think this makes sense.

            The tests for 'begin', 'end' and the appending of the current
            begin[] stuff have to be here, in this order.
        """

        action=l[0].upper()      # 1st arg in line

        if action == 'BEGIN':
            if not l[1:]:
                error("Use: Begin STUFF")
            beginPoints.append(len(beginData))
            beginData.extend(l[1:])
            continue

        if action == 'END':
            if len(l) > 1:
                error("No arguments permitted for END")
            if not beginData:
                error("No 'BEGIN' for 'END'")
            beginData=beginData[:beginPoints.pop(-1)]
            continue

        if beginData:
            l = beginData + l
            action = l[0].upper()


        if gbl.showExpand and action !='REPEAT':
            print l

        # If the command is in the simple function table, jump & loop.

        if action in simpleFuncs:
            simpleFuncs[action](l[1:])
            continue


        """ We have several possibilities ...
            1. The command is a valid assigned track name,
            2. The command is a valid track name, but needs to be
               dynamically allocated,
            3. It's really a chord action
        """

        if not action in gbl.tnames:
            trackAlloc(action, 0)    # ensure that track is allocated

        if action in gbl.tnames:    #  BASS/DRUM/APEGGIO/CHORD

            name = action
            if len(l) < 2:
                error("Expecting argument after '%s'" % name)
            action = l[1].upper()

            if action in trackFuncs:
                trackFuncs[action](name, l[2:])
            else:
                error ("Don't know '%s'" % curline)

            continue

        ### Gotta be a chord data line!


        """ A data line can have an optional bar number at the start
            of the line. Makes debugging input easier. The next
            block strips leading integers off the line. Note that
            a line number on a line by itself it okay.
        """

        if action.isdigit():   # isdigit() matches '1', '1234' but not '1a'!
            barLabel = l[0]
            l = l[1:]
            if not l:        # ignore empty lines
                continue
        else:
            barLabel = ''

        """ A bar can have an optional repeat count. This must
            be at the end of bar in the form '* xx'.
        """

        if len(l)>1 and l[-2]=='*':
            rptcount = stoi(l[-1], "Expecting integer after '*'")
            l=l[:-2]
        else:
            rptcount = 1


        """ Extract solo(s) from line ... this is anything in {}s.
            The solo data is pushed into RIFFs and discarded from
            the current line.
        """

        l = ' '.join(l)
        l = MMA.patSolo.extractSolo(l, rptcount)

        """ Set lyrics from [stuff] in the current line.
            NOTE: lyric.extract() inserts previously created
                  data from LYRICS SET and inserts the chord names
                  if that flag is active.
        """

        l, lyrics = lyric.extract(l, rptcount)

        l = l.split()

        """ At this point we have only chord info. A number
            of sanity checks are made:
              1. Make sure there is some chord data,
              2. Ensure the correct number of chords.
        """

        if not l:
            error("Expecting music (chord) data. Even lines with\n"
                  "  lyrics or solos still need a chord")


        """ We now have a chord line. It'll look something like:

              ['Cm', '/', 'z', 'F#@4.5'] or ['/' 'C@3' ]

            For each bar we create a list of CTables, one for each
            chord in the line. Each entry has the start/end (in beats), chordname, etc.
        """

        ctable = parseChordLine(l)

        # Create MIDI data for the bar

        for rpt in range(rptcount):   # for each bar in the repeat count ( Cm * 3)

            """ Handle global (de)cresc by popping a new volume off stack. """

            if MMA.volume.futureVol:
                MMA.volume.volume = MMA.volume.futureVol.pop(0)
            if MMA.volume.futureVol:
                MMA.volume.nextVolume = MMA.volume.futureVol[0]
            else:
                MMA.volume.nextVolume = None


            """ Set up for rnd seq. This may set the current seq point. If return
                is >=0 then we're doing track rnd.
            """

            rsq, seqlist = MMA.seqrnd.setseq()


            """ Process each track. It is important that the track classes
                are written so that the ctable passed to them IS NOT MODIFIED.
                This applies especially to chords. If the track class changes
                the chord, then restore it before returning!!!
            """

            for a in gbl.tnames.values():
                if rsq >= 0:
                    seqSave = gbl.seqCount
                    if a.name in seqlist:   # for seqrnd with tracklist
                        gbl.seqCount = rsq
                a.bar(ctable)    ## process entire bar!

                if rsq >= 0:   # for track rnd
                    gbl.seqCount = seqSave

            # Adjust counters

            """ After processsing each bar we update a dictionary of bar
                pointers. This table is used when the MIDI data is written
                when -b or -B is set to limit output.
            """

            gbl.barPtrs[gbl.barNum+1] = [barLabel, gbl.tickOffset,
                      gbl.tickOffset + (gbl.QperBar * gbl.BperQ)-1]

            gbl.totTime += float(gbl.QperBar) / gbl.tempo

            gbl.tickOffset += (gbl.QperBar * gbl.BperQ)

            gbl.barNum += 1
            gbl.seqCount = (gbl.seqCount+1) % gbl.seqSize

            if gbl.barNum > gbl.maxBars:
                error("Capacity exceeded. Maxbar setting is %s. Use -m option"
                      % gbl.maxBars)

            MMA.grooves.nextGroove()   # using groove list? Advance.

            # Enabled with the -r command line option

            if gbl.showrun:
                print "%3d:" % gbl.barNum,
                for c in l:
                    print c,
                if lyrics:
                    print lyrics,
                print

def parseChordLine(l):
    """ Parse a line of chord symbols and determine start/end points. """

    global lastChord

    ctable = []               # an entry for each chord in the bar
    quarter = gbl.BperQ       # ticks in a quarter note (== 1 beat)
    endTime = (quarter * gbl.QperBar)  # number of ticks in bar

    p = 0                    # our beat counter --- points to beat 1,2, etc in ticks

    for x in l:
        if "@" in x:
            ch, beat = x.split("@", 1)
            beat = int((stof(beat, "Expecting an value after the @ in '%s'" % x)-1) * quarter)
            p = int(beat/quarter) * quarter
        else:
            ch = x
            beat = p

        p += quarter       # for next loop. Always a full beat.

        if ch == '/':      # handle continuation chords
            if not ctable:
                if lastChord:
                   ch = lastChord
                else:
                    error("No previous chord for '/' at line start")
            else:         # '/' other than at start just increment the beat counter
                continue

        if ctable:
            if ctable[-1].name == ch:  # skip duplicate chords
                continue

            if ctable[-1].chStart >= beat:
                error("Chord positions out of order")

        else:    # first entry
            if beat != 0:
                error("The first chord must be at beat 1, not '%s'." % (beat/quarter) )

        ctab = CTable()
        ctab.name = ch
        ctab.chStart = beat

        """ If the chord we just extracted has a 'z' in it then we do the
            following ugly stuff to figure out which tracks to mute. 'ch'
            will be a chord name or 'z' when this is done.
        """

        if 'z' in ch:
            c, r = ch.split('z', 1)

            if not c:   # no chord specified
                c = 'z'        # dummy chord name to keep chordnotes() happy
                if r == '!':    # mute all
                    r = 'DCAWBSR'
                elif not r:     # mute all tracks except Drum
                    r = 'CBAWSR'
                else:
                    error("To mute individual tracks you must "
                          "use a chord/z combination not '%s'" % ch)

            else:    # illegal construct -- 'Cz!'
                if r == '!':
                    error("'%s' is illegal. 'z!' mutes all tracks "
                          "so you can't include the chord." % ch)

                elif not r:
                    error("'%s' is illegal. You must specify tracks "
                          "if you use a chord." % ch )

            ch = c   # this will be 'z' or the chord part

            # note this indent ... we do it always!
            for v in r:   # 'r' must be a list of track specifiers
                if v == 'C':
                    ctab.chordZ = 1
                elif v == 'B':
                    ctab.bassZ = 1
                elif v == 'A':
                    ctab.arpeggioZ = 1
                elif v == 'W':
                    ctab.walkZ = 1
                elif v == 'D':
                    ctab.drumZ = 1
                elif v == 'S':
                    ctab.scaleZ = 1
                elif v == 'R':
                    ctab.ariaZ = 1
                elif v == 'P':
                    ctab.plectrumZ = 1
                else:
                    error("Unknown track '%s' for muting in '%s'" % (v, ch) )

        ctab.chord = MMA.chords.ChordNotes(ch)  # Derive chord notes (or mute)

        ctable.append(ctab)

    # Done all chords in line, fix up some pointers.

    if ctable[-1].chStart >= endTime:
        error("Maximum offset for chord '%s' must be less than %s, not '%s'." % \
                ( ctable[-1].name, endTime/quarter+1, ctable[-1].chStart/quarter+1 ))

    for i, v in enumerate(ctable[:-1]):  # set end range for each chord
        ctable[i].chEnd = ctable[i+1].chStart

    ctable[-1].chEnd = endTime      # set end of range for last chord
    lastChord = ctable[-1].name     # remember chord at end of this bar for next

    return ctable


##################################################################

def allTracks(ln):
    """ Apply track to all tracks. """

    types1 = ('BASS', 'CHORD', 'ARPEGGIO', 'SCALE', 'DRUM', 'WALK', 'PLECTRUM')
    types2   = ('MELODY', 'SOLO', 'ARIA' )
    allTypes = types1 + types2

    ttypes = []

    if len(ln) < 1:
        error("AllTracks: argument (track?) required")

    i = 0
    while i < len(ln) and ln[i].upper() in allTypes:
        ttypes.append(ln[i].upper())
        i += 1

    if ttypes == []:
        ttypes = types1

    if i>=len(ln):
        error("AllTracks: Additional argument (command?) required")

    cmd = ln[i].upper()
    args = i+1

    if not cmd in trackFuncs:
        error("AllTracks: command '%s' doen't exist" % cmd)

    for n in gbl.tnames:
        if not gbl.tnames[n].vtype in ttypes:
            continue

        trackFuncs[cmd](n, ln[args:])


#######################################
# Do-nothing functions

def comment(ln):
    pass

def repeatend(ln):
    error("Repeatend/EndRepeat without Repeat")

def repeatending(ln):
    error("Repeatending without Repeat")

def endmset(ln):
    error("EndMset/MSetEnd without If")

def ifend(ln):
    error("ENDIF without IF")

def ifelse(ln):
    error("ELSE without IF")



#######################################
# Repeat/jumps


def repeat(ln):
    """ Repeat/RepeatEnd/RepeatEnding.

        Read input until a RepeatEnd is found. The entire
        chunk is pushed back into the input stream the
        correct number of times. This accounts for endings and
        nested repeats.
    """


    def repeatChunk():
        q=[]
        qnum=[]
        nesting = 0

        while 1:
            l=gbl.inpath.read()

            if not l:
                error("EOF encountered processing Repeat")

            act=l[0].upper()

            if act=='REPEAT':
                nesting += 1

            elif act in ('REPEATEND', 'ENDREPEAT') and nesting:
                nesting -= 1

            elif act == 'REPEATENDING' and nesting:
                pass

            elif act in ('REPEATEND', 'ENDREPEAT', 'REPEATENDING'):
                return (q, qnum, act, l[1:])

            q.append(l)
            qnum.append(gbl.lineno)

    stack=[]
    stacknum=[]
    main=[]
    mainnum=[]
    ending = 0

    if ln:
        error("REPEAT takes no arguments")

    main, mainnum, act, l = repeatChunk()

    while 1:
        if act in ('REPEATEND', 'ENDREPEAT'):
            if l:
                l = macros.expand(l)
                if len(l) == 2 and l[0].upper() == 'NOWARN':
                    l=l[1:]
                    warn=0
                else:
                    warn=1

                if len(l) != 1:
                    error("%s: Use [NoWarn] Count" % act)

                count=stoi(l[0], "%s takes an integer arg" % act)

                if count == 2 and warn:
                    warning("%s count of 2 duplicates default. Did you mean 3 or more?" % act)

                elif count == 1 and warn:
                    warning("%s count of 1 means NO REPEAT" % act)

                elif count == 0 and warn:
                    warning("%s count of 0, Skipping entire repeated section" % act)

                elif count < 0:
                    error("%s count must be 0 or greater" % act)

                elif count > 10 and warn:
                    warning("%s is a large value for %s" % (count, act) )

            else:
                count=2

            if not ending:
                count += 1
            for c in range(count-1):
                stack.extend(main)
                stacknum.extend(mainnum)
            gbl.inpath.push(stack, stacknum)
            break

        elif act == 'REPEATENDING':
            ending = 1

            if l:
                l = macros.expand(l)
                if len(l) == 2 and l[0].upper() == 'NOWARN':
                    warn=0
                    l=l[1:]
                else:
                    warn=1

                if len(l) != 1:
                    error("REPEATENDING: Use [NoWarn] Count")

                count=stoi(l[0], "RepeatEnding takes an integer arg")

                if count < 0:
                    error("RepeatEnding count must be postive, not '%s'" % count)

                elif count == 0 and warn:
                    warning("RepeatEnding count of 0, skipping section")

                elif count == 1 and warn:
                    warning("RepeatEnding count of 1 duplicates default")

                elif count > 10 and warn:
                    warning("%s is a large value for RepeatEnding" % count)
            else:
                count = 1

            rpt, rptnum, act, l = repeatChunk()

            for c in range(count):
                stack.extend(main)
                stacknum.extend(mainnum)
                stack.extend(rpt)
                stacknum.extend(rptnum)


        else:
            error("Unexpected line in REPEAT")

def goto(ln):
    if len(ln) != 1:
        error("Usage: GOTO Label")
    gbl.inpath.goto(ln[0].upper())

def eof(ln):
        gbl.inpath.toEof()


#######################################
# Tempo/timing


def setTime(ln):
    """ Set the 'time sig'.

        We do restrict the time setting to the range of 1..12.
        No particular reason, but we do need some limit? Certainly
        it has to be greater than 0.
    """

    if len(ln) != 1:
        error("Use: Time N")

    n = stoi(ln[0], "Argument for time must be integer")

    if n < 1 or n > 12:
        error("Time (beats/bar) must be 1..12")

    # If no change, just ignore this.

    if gbl.QperBar != n:
        gbl.QperBar = int(n)

        # Time changes zap all predfined sequences

        for a in gbl.tnames.values():
            a.clearSequence()


def tempo(ln):
    """ Set tempo. """

    if not ln or len(ln) >2:
        error("Use: Tempo [*,+,-]BperM [BARS]")

    # Get new value.

    a = ln[0][0]
    if a in "+-*":
        v = stof(ln[0][1:], "Tempo expecting value for rate adjustment, not '%s'" % ln[0])
        if a == '-':
            v = gbl.tempo - v
        elif a == '+':
            v += gbl.tempo
        elif a == '*':
            v *= gbl.tempo

    else:
        v  = stof(ln[0], "Tempo expecting rate, not '%s'" % ln[0])


    # is this immediate or over time?

    if len(ln) == 1:
        gbl.tempo = int(v)
        gbl.mtrks[0].addTempo(gbl.tickOffset, gbl.tempo)
        if gbl.debug:
            print "Set Tempo to %s" % gbl.tempo


    else:         # Do a tempo change over bar count
        bars = ln[1]

        bars = stof(bars, "Expecting value, not %s" % bars )
        numbeats = int(bars * gbl.QperBar)

        if numbeats < 1:
            error("Beat count must be greater than 1")

        # Vary the rate in the meta track

        tincr = (v - gbl.tempo) / float(numbeats)    # incr per beat
        bstart = gbl.tickOffset            # start
        boff = 0
        tempo = gbl.tempo

        for n in range(numbeats):
            tempo += tincr
            if tempo:
                gbl.mtrks[0].addTempo(bstart + boff, int(tempo))
            boff += gbl.BperQ

        if tempo != v:
            gbl.mtrks[0].addTempo(bstart + boff, int(v) )

        gbl.tempo = int(v)

        if gbl.debug:
            print "Set future Tempo to %s over %s beats" % \
                ( int(tempo), numbeats)

    if gbl.tempo <=0:
        error("Tempo setting must be greater than 0.")


def beatAdjust(ln):
    """ Delete or insert some beats into the sequence.

        This just adjusts the current song position. Nothing is
        lost or added to the actual file.
    """


    if len(ln) != 1:
        error("Use: BeatAdjust NN")

    adj = stof(ln[0], "Expecting a value (not %s) for BeatAdjust" % ln[0])

    gbl.tickOffset += int(adj * gbl.BperQ)

    gbl.totTime += adj / gbl.tempo   # adjust total time

    if gbl.debug:
        print "BeatAdjust: inserted %s at bar %s." % (adj, gbl.barNum + 1)


def cut(ln):
    """ Insert a all-note-off into all tracks. """

    if not len(ln):
        ln=['0']

    if len(ln) != 1:
        error("Use: Cut Offset")

    """ Loop though all the tracks. Note that trackCut() checks
        to make sure that there is a need to insert in specified track.
        In this loop we create a list of channels as we loop though
        all the tracks, skipping over any duplicate channels or
        tracks with no channel assigned.
    """

    l=[]
    for t in sorted(gbl.tnames.keys()):
        c = gbl.tnames[t].channel
        if not c or c in l:
            continue
        l.append(c)
        trackCut(t, ln)


def fermata(ln):
    """ Apply a fermata timing to the specified beat. """

    if len(ln) != 3:
        error("Use: Fermata 'offset' 'duration' 'adjustment'")

    offset = stof(ln[0], "Expecting a value (not '%s') "
              "for Fermata Offset" % ln[0] )

    if offset < -gbl.QperBar or offset > gbl.QperBar:
        warning("Fermata: %s is a large beat offset" % offset)

    dur = stof(ln[1], "Expecting a value (not '%s') for Fermata Duration" % ln[1])

    if dur <= 0:
        error("Fermata duration must be greater than 0")

    if dur > gbl.QperBar:
        warning("Fermata: %s is a large duration" % dur)

    adj = stof(ln[2], "Expecting a value (not '%s') for Fermata Adjustment" % ln[2])

    if adj< 100:
        warning("Fermata: Adjustment less than 100 is shortening beat value")

    if adj == 100:
        error("Fermata: using value of 100 makes no difference, must be an error")

    moff=int(gbl.tickOffset + (gbl.BperQ * offset))

    if moff < 0:
        error("Fermata offset comes before track start")

    gbl.mtrks[0].addTempo(moff, int(gbl.tempo / (adj/100)) )

    tickDur = int(gbl.BperQ * dur)

    gbl.mtrks[0].addTempo(moff + tickDur, gbl.tempo)

    # Clear out NoteOn events in all tracks

    if offset < 0:
        start = moff + int(.05 * gbl.BperQ)
        end = moff + tickDur - int(.05 * gbl.BperQ)

        for n, tr in gbl.mtrks.items():
            if n <= 0: continue        # skip meta track
            tr.zapRangeTrack(start, end )

    if gbl.debug:
        print "Fermata: Beat %s, Duration %s, Change %s, Bar %s" % \
              (offset, dur, adj, gbl.barNum + 1)
        if offset < 0:
            print "\tNoteOn Events removed in tick range %s to %s" \
                  % (start, end)



#######################################
# File and I/O

def include(ln):
    """ Include a file. """

    global beginData

    if beginData:
        error("INCLUDE not permitted in Begin/End block")

    if len(ln) != 1:
        error("Use: Include FILE" )

    fn = MMA.file.locFile(MMA.file.fixfname(ln[0]), gbl.incPath)
    if not fn:
        error("Could not find include file '%s'" % ln)

    else:
        parseFile(fn)


def usefile(ln):
    """ Include a library file. """

    global beginData

    if beginData:
        error("USE not permitted in Begin/End block")

    if len(ln) != 1:
        error("Use: Use FILE")

    f = MMA.file.fixfname(ln[0])
    fn = MMA.file.locFile(f, gbl.libPath)

    if not fn:
        error("Unable to locate library file '%s'" % f)

    """ USE saves current state, just like defining a groove.
        Here we use a magic number which can't be created with
        a defgroove ('cause it's an integer). Save, read, restore.
    """

    slot = gmagic
    MMA.grooves.grooveDefineDo(slot)
    parseFile(fn)
    MMA.grooves.grooveDo(slot)

#######################################
# Sequence

def seqsize(ln):
    """ Set the length of sequences. """

    if len(ln) !=1:
        error("Usage 'SeqSize N'")

    n = stoi(ln[0], "Argument for SeqSize must be integer")

    if n < 1:
        error("SeqSize: sequence size must be 1 or greater, not '%s'." % n)

    # Setting the sequence size always resets the seq point

    gbl.seqCount = 0

    """ Now set the sequence size for each track. The class call
        will expand/contract existing patterns to match the new
        size.
    """

    if n != gbl.seqSize:
        gbl.seqSize = n
        for a in gbl.tnames.values():
            a.setSeqSize()

        MMA.seqrnd.seqRndWeight = seqBump(MMA.seqrnd.seqRndWeight)

    if gbl.debug:
        print "Set SeqSize to ", n


def seq(ln):
    """ Set the sequence point. """

    if len(ln) == 0:
        s = 0
    elif len(ln)==1:
        s = stoi(ln[0], "Expecting integer value after SEQ")
    else:
        error("Use: SEQ or SEQ NN to reset seq point")


    if s > gbl.seqSize:
        error("Sequence size is '%d', you can't set to '%d'" %
              (gbl.seqSize, s))

    if s==0:
        s=1

    if s<0:
        error("Seq parm must be greater than 0, not %s", s)

    gbl.seqCount = s-1

    if MMA.seqrnd.seqRnd[0] == 1:
        warning("SeqRnd has been disabled by a Seq command")
        MMA.seqrnd.seqRnd = [0]


def seqClear(ln):
    """ Clear all sequences (except SOLO/ARIA tracks). """

    if ln:
        error ("Use: 'SeqClear' with no args")

    for n in gbl.tnames.values():
        if n.vtype != 'SOLO' and n.vtype != 'ARIA':
            n.clearSequence()
    MMA.volume.futureVol = []

    MMA.seqrnd.setSeqRndWeight(['1'])



def restart(ln):
    """ Restart all tracks to almost-default conditions. """

    if ln:
        error ("Use: 'Restart' with no args")

    for n in gbl.tnames.values():
        n.restart()


#######################################
# Misc

def synchronize(ln):
    """ Set synchronization in the MIDI. A file mode for -0 and -1. """

    if not ln:
        error("SYNCHRONIZE: requires args END and/or START.")

    for a in ln:
        if a.upper() == 'END':
            gbl.endsync =  1
        elif a.upper() == 'START':
            gbl.synctick = 1
        else:
            error("SYNCHRONIZE: expecting END or START")


def rndseed(ln):
    """ Reseed the random number generator. """

    if not ln:
        random.seed()

    elif len(ln)>1:
        error("RNDSEED: requires 0 or 1 arguments")
    else:
        random.seed(stof(ln[0]))

def transpose(ln):
    """ Set transpose value. """


    if len(ln) != 1:
        error("Use: Transpose N")

    t = stoi(ln[0], "Argument for Tranpose must be an integer, not '%s'" % ln[0])
    if t < -12 or t > 12:
            error("Tranpose %s out-of-range; must be -12..12" % t)

    gbl.transpose = t

    if gbl.debug:
        print "Set Transpose to %s" % t


def lnPrint(ln):
    """ Print stuff in a "print" command. """

    print " ".join(ln)


def printActive(ln):
    """ Print a list of the active tracks. """

    print "Active tracks, groove:", MMA.grooves.currentGroove, ' '.join(ln)

    for a in sorted(gbl.tnames.keys()):
        f=gbl.tnames[a]
        if f.sequence:
            print "     ",a
    print


def setDebug(ln):
    """ Set debugging options dynamically. """

    msg=( "Use: Debug MODE=On/Off where MODE is one or more of "
          "DEBUG, FILENAMES, PATTERNS, SEQUENCE, "
          "RUNTIME, WARNINGS, EXPAND, ROMAN or PLECTRUM." )


    if not len(ln):
        error(msg)

    # save current flags

    gbl.Ldebug         = gbl.debug
    gbl.LshowFilenames = gbl.showFilenames
    gbl.Lpshow         = gbl.pshow
    gbl.Lseqshow       = gbl.seqshow
    gbl.Lshowrun       = gbl.showrun
    gbl.LnoWarn        = gbl.noWarn
    gbl.LnoOutput      = gbl.noOutput
    gbl.LshowExpand    = gbl.showExpand
    gbl.Lchshow        = gbl.chshow
    gbl.LplecShow      = gbl.plecShow
    gbl.LrmShow        = gbl.rmShow

    for l in ln:
        try:
            mode, val = l.upper().split('=')
        except:
            error("Each debug option must contain a '=', not '%s'" % l)

        if val == 'ON' or val == '1':
            setting = 1
        elif val == 'OFF' or val == '0':
            setting = 0
        else:
            error(msg)

        if mode == 'DEBUG':
            gbl.debug = setting
            if gbl.debug:
                print "Debug=%s." % val

        elif mode == 'FILENAMES':
            gbl.showFilenames = setting
            if gbl.debug:
                print "ShowFilenames=%s." % val

        elif mode == 'PATTERNS':
            gbl.pshow = setting
            if gbl.debug:
                print "Pattern display=%s." % val

        elif mode == 'SEQUENCE':
            gbl.seqshow = setting
            if gbl.debug:
                print "Sequence display=%s." % val

        elif mode == 'RUNTIME':
            gbl.showrun = setting
            if gbl.debug:
                print "Runtime display=%s." % val

        elif mode == 'WARNINGS':
            gbl.noWarn = not(setting)
            if gbl.debug:
                print "Warning display=%s" % val

        elif mode == 'EXPAND':
            gbl.showExpand = setting
            if gbl.debug:
                print "Expand display=%s." % val

        elif mode == 'ROMAN':
            gbl.rmShow = setting
            if gbl.debug:
                print "Roman numeral chords/slash display=%s" % val

        elif mode == 'PLECTRUM':
            gbl.plecShow = setting
            if gbl.debug:
                print "Plectrum display=%s" % val

        else:
            error(msg)



###########################################################
###########################################################
## Track specific commands


#######################################
# Pattern/Groove

def trackDefPattern(name, ln):
    """ Define a pattern for a track.

    Use the type-name for all defines.... check the track
    names and if it has a '-' in it, we use only the
    part BEFORE the '-'. So DRUM-Snare becomes DRUM.
    """

    ln=ln[:]

    name=name.split('-')[0]

    trackAlloc(name, 1)

    if ln:
        pattern = ln.pop(0).upper()
    else:
        error("Define is expecting a pattern name")

    if pattern in ('z', 'Z', '-'):
        error("Pattern name '%s' is reserved" % pattern)

    if pattern.startswith('_'):
        error("Names with a leading underscore are reserved")

    if not ln:
        error("No pattern list given for '%s %s'" % (name, pattern) )

    ln=' '.join(ln)
    gbl.tnames[name].definePattern(pattern, ln)


def trackSequence(name, ln):
    """ Define a sequence for a track.

    The format for a sequence:
    TrackName Seq1 [Seq2 ... ]

    Note, that SeqX can be a predefined seq or { seqdef }
    The {} is dynamically interpreted into a def.
    """

    if not ln:
        error ("Use: %s Sequence NAME [...]" % name)

    ln = ' '.join(ln)


    """ Before we do extraction of {} stuff make sure we have matching {}s.
        Count the number of { and } and if they don't match read more lines and 
        append. If we get to the EOF then we're screwed and we error out. Only trick
        is to make sure we do macro expansion! This code lets one have long
        sequence lines without bothering with '\' continuations.
    """
    
    oLine=gbl.lineno   # in case we error out, report start line
    while ln.count('{') != ln.count('}'):
        l = gbl.inpath.read()
        if l == None:   # reached eof, error
            gbl.lineno = oLine
            error("%s Sequence {}s do not match" % name)

        l=' '.join(macros.expand(l))
        #print l, '<%s>' % l[-1]
        if l[-1] != '}' and l[-1] != ';':
            error("%s: Expecting multiple sequence lines to end in ';'" % name)

        ln += ' ' + l


    """ Extract out any {} definitions and assign them to new
    define variables (__1, __99, etc) and melt them
    back into the string.
    """

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
        
        trk=name.split('-')[0]
        trackAlloc(trk, 1)

        """ We need to mung the plectrum classes. Problem is that we define all
            patterns in the base class (plectrum-banjo is created in PLECTRUM)
            which is fine, but the def depends on the number of strings in the
            instrument (set by the tuning option). So, we save the tuning for
            the base class, copy the real tuning, and restore it.

            NOTE: at this point the base and current tracks have been initialized.
        """

        if trk == 'PLECTRUM' and name != trk:
            z=gbl.tnames[trk]._tuning[:]
            gbl.tnames[trk]._tuning = gbl.tnames[name]._tuning
        else:
            z = None

        gbl.tnames[trk].definePattern(pn, s[0])  # 'trk' is a base class!
        if z:
            gbl.tnames[trk]._tuning = z

        ln = ln[:sp] + ' ' + pn + ' ' + ln[sp:]

    ln=ln.split()

    gbl.tnames[name].setSequence(ln)


def trackSeqClear(name,     ln):
    """ Clear sequence for specified tracks.

    Note: "Drum SeqClear" clears all Drum tracks,
          "Drum-3 SeqClear" clears track Drum-3.
    """

    if ln:
        error("No args permitted. Use %s SEQCLEAR" % name)

    for n in gbl.tnames:
        if n.find(name) == 0:
            if gbl.debug:
                print "SeqClear: Track %s cleared." % n
            gbl.tnames[n].clearSequence()


def trackSeqRnd(name, ln):
    """ Set random order for specified track. """

    if len(ln) != 1:
        error("Use: %s SeqRnd [On, Off]" % name)

    gbl.tnames[name].setRnd(ln[0].upper())

def trackSeqRndWeight(name, ln):
    """ Set rnd weight for track. """

    if not ln:
        error("Use: %s RndWeight <weight factors>" % name)

    gbl.tnames[name].setRndWeight(ln)


def trackRestart(name, ln):
    """ Restart track to almost-default condidions. """

    if ln:
        error ("Use: '%s Resart' with no args", name)

    gbl.tnames[name].restart()


def trackRiff(name, ln):
    """ Set a riff for a track. """

    gbl.tnames[name].setRiff(' '.join(ln))

def trackDupRiff(name, ln):
    """ Set a riff for a track. """

    if not ln:
        error("%s DupRiff: need at least one track to copy to.")

    gbl.tnames[name].dupRiff(ln)


def deleteTrks(ln):
    """ Delete a track and free the MIDI track. """

    if not len(ln):
        error("Use Delete Track [...]")

    for name in ln:
        name=name.upper()
        if name in gbl.tnames:
            tr = gbl.tnames[name]
        else:
            error("Track '%s' does not exist" % name)

        if tr.channel:
            tr.doMidiClear()
            tr.clearPending()

            if tr.riff:
                warning("%s has pending RIFF(s)" % name)
            gbl.midiAvail[tr.channel] -= 1

            # NOTE: Don't try deleting 'tr' since it's just a copy!!

            del gbl.tnames[name]

        if not name in gbl.deletedTracks:
            gbl.deletedTracks.append(name)

        if gbl.debug:
            print "Track '%s' deleted" % name



#######################################
# Volume

def trackRvolume(name, ln):
    """ Set random volume for specific track. """

    if not ln:
        error ("Use: %s RVolume N [...]" % name)

    gbl.tnames[name].setRVolume(ln)

def trackSwell(name, ln):
    gbl.tnames[name].setSwell(ln)

def trackCresc(name, ln):
    gbl.tnames[name].setCresc(1, ln)

def trackDeCresc(name, ln):
    gbl.tnames[name].setCresc(-1, ln)

def trackVolume(name, ln):
    """ Set volume for specific track. """

    if not ln:
        error ("Use: %s Volume DYN [...]" % name)

    gbl.tnames[name].setVolume(ln)


def trackChannelVol(name, ln):
    """ Set the channel volume for a track."""

    if len(ln) != 1:
        error("Use: %s ChannelVolume" % name)

    v=stoi(ln[0], "Expecting integer arg, not %s" % ln[0])

    if v<0 or v>127:
        error("ChannelVolume must be 0..127")

    gbl.tnames[name].setChannelVolume(v)

def trackChannelCresc(name, ln):
    """ MIDI cresc. """

    doTrackCresc(name, ln, 1)

def trackChannelDecresc(name, ln):
    """ MIDI cresc. """

    doTrackCresc(name, ln, -1)

def doTrackCresc(name, ln, dir):
    """ Call func for midi(de)cresc """

    if dir == -1:
        func="MIDIDeCresc"
    else:
        func = "MIDICresc"

    if len(ln) != 3:
        error("Use: %s %s <start> <end> <count>" % (name, func))

    v1=stoi(ln[0], "Expecting integer arg, not %s" % ln[0])
    v2=stoi(ln[1], "Expecting integer arg, not %s" % ln[1])
    count=stof(ln[2])

    if count<=0:
        error("%s: count must be >0" % func)

    if v1<0 or v1>127 or v2<0 or v2>127:
        error("%s: Volumes must be 0..127." % func)

    if dir == -1 and v1<v2:
        warning("%s: dest volume > start" % func)
    elif dir == 1 and v1>v2:
        warning("%s: dest volume < start" % func)

    gbl.tnames[name].setMidiCresc(v1, v2, count)

def trackAccent(name, ln):
    """ Set emphasis beats for track."""

    gbl.tnames[name].setAccent(ln)


#######################################
# Timing

def trackCut(name, ln):
    """ Insert a ALL NOTES OFF at the given offset. """


    if not len(ln):
        ln=['0']

    if    len(ln) != 1:
        error("Use: %s Cut Offset" % name)


    offset = stof(ln[0], "Cut offset expecting value, (not '%s')" % ln[0])

    if offset < -gbl.QperBar or offset > gbl.QperBar:
        warning("Cut: %s is a large beat offset" % offset)



    moff = int(gbl.tickOffset + (gbl.BperQ * offset))

    if moff < 0:
        error("Calculated offset for Cut comes before start of track")

    """ Insert allnoteoff directly in track. This skips the normal
    queueing in pats because it would never take if at the end
    of a track.
    """

    m = gbl.tnames[name].channel
    if m and len(gbl.mtrks[m].miditrk) > 1:
        gbl.mtrks[m].addNoteOff(moff)


        if gbl.debug:
            print "%s Cut: Beat %s, Bar %s" % (name, offset, gbl.barNum + 1)


def trackMallet(name, ln):
    """ Set repeating-mallet options for solo/melody track. """

    if not ln:
        error("Use: %s Mallet <Option=Value> [...]" % name)

    gbl.tnames[name].setMallet(ln)


def trackRtime(name, ln):
    """ Set random timing for specific track. """

    if not ln:
        error ("Use: %s RTime N [...]" % name)


    gbl.tnames[name].setRTime(ln)


def trackRskip(name, ln):
    """ Set random skip for specific track. """

    if not ln:
        error ("Use: %s RSkip N [...]" % name)


    gbl.tnames[name].setRSkip(ln)


def trackArtic(name, ln):
    """ Set articulation. """

    if not ln:
        error("Use: %s Articulation N [...]" % name)


    gbl.tnames[name].setArtic(ln)


#######################################
# Chord stuff


def trackCompress(name, ln):
    """ Set (unset) compress for track. """

    if not ln:
        error("Use: %s Compress <value[s]>" % name)

    gbl.tnames[name].setCompress(ln)


def trackVoicing(name, ln):
    """ Set Voicing options. Only valid for chord tracks at this time."""

    if not ln:
        error("Use: %s Voicing <MODE=VALUE> [...]" % name)


    gbl.tnames[name].setVoicing(ln)



def trackDupRoot(name, ln):
    """ Set (unset) the root note duplication. Only applies to chord tracks. """

    if not ln:
        error("Use: %s DupRoot <value> ..." % name)

    gbl.tnames[name].setDupRoot(ln)


def trackChordLimit(name, ln):
    """ Set (unset) ChordLimit for track. """

    if len(ln) != 1:
        error("Use: %s ChordLimit <value>" % name)

    gbl.tnames[name].setChordLimit(ln[0])

def trackRange(name, ln):
    """ Set (unset) Range for track. Only effects arp and scale. """

    if not ln:
        error("Use: %s Range <value> ... " % name)


    gbl.tnames[name].setRange(ln)


def trackInvert(name, ln):
    """ Set invert for track."""

    if not ln:
        error("Use: %s Invert N [...]" % name)

    gbl.tnames[name].setInvert(ln)


def trackSpan(name, ln):
    """ Set midi note span for track. """

    if len(ln) != 2:
        error("Use: %s Start End" % name)

    start = stoi(ln[0], "Expecting integer for SPAN 1st arg")
    if start <0 or start >127:
        error("Start arg for Span must be 0..127, not %s" % start)

    end = stoi(ln[1], "Expecting integer for SPAN 2nd arg")
    if end <0 or end >127:
        error("End arg for Span must be 0..127, not %s" % end)

    if end <= start:
        error("End arg for Span must be greater than start")

    if end-start < 11:
        error("Span range must be at least 12")

    gbl.tnames[name].setSpan(start, end)



def trackOctave(name, ln):
    """ Set octave for specific track. """

    if not ln:
        error ("Use: %s Octave N [...], (n=0..10)" % name)


    gbl.tnames[name].setOctave( ln )


def trackStrum(name, ln):
    """ Set all specified track strum. """

    if not ln:
        error ("Use: %s Strum N [...]" % name)


    gbl.tnames[name].setStrum( ln )


def trackHarmony(name, ln):
    """ Set harmony value. """

    if not ln:
        error("Use: %s Harmony N [...]" % name)

    gbl.tnames[name].setHarmony(ln)


def trackHarmonyOnly(name, ln):
    """ Set harmony only for track. """

    if not ln:
        error("Use: %s HarmonyOnly N [...]" % name)

    gbl.tnames[name].setHarmonyOnly(ln)

def trackHarmonyVolume(name, ln):
    """ Set harmony volume for track."""

    if not ln:
        error("Use: %s HarmonyVolume N [...]" % name)

    gbl.tnames[name].setHarmonyVolume(ln)


#######################################
# Plectrum stuff

def trackPlectrumTuning(name, ln):
    """ Define the number of strings and tuning for
        for an instrument that can be played with a plectrum.
    """

    if not ln:
        error("Use: %s Tuning string1 string2 string3 [stringN ...]" % name)
    
    g=gbl.tnames[name]
    
    if hasattr(g, "setPlectrumTuning" ):
        g.setPlectrumTuning(ln)
    else:
        warning("TUNING: not permitted in %s tracks. Arg '%s' ignored." % \
                    ( g.vtype, ' '.join(ln) ) )


def trackPlectrumCapo(name, ln):
    """ Define the position of the capo
        (unlike a real guitar negative numbers are allowed)
        for an instrument that can be played with a plectrum.
    """

    if not ln or len(ln) != 1:
        error("Use: %s Capo N" % name)
  
    g=gbl.tnames[name]
    if hasattr(g, "setPlectrumCapo"):
        g.setPlectrumCapo(ln[0])
    else:
        warning("CAPO: not permitted in %s tracks. Arg '%s' ignored." % \
                    ( g.vtype, ' '.join(ln) ) )


#######################################
# MIDI setting


def trackChannel(name, ln):
    """ Set the midi channel for a track."""

    if not ln:
        error("Use: %s Channel" % name)

    gbl.tnames[name].setChannel(ln[0])


def trackChShare(name, ln):
    """ Set MIDI channel sharing."""

    if len(ln) !=1:
        error("Use: %s ChShare TrackName" % name)

    gbl.tnames[name].setChShare(ln[0])


def trackVoice(name, ln):
    """ Set voice for specific track. """

    if not ln:
        error ("Use: %s Voice NN [...]" % name)


    gbl.tnames[name].setVoice(ln)


def trackOff(name, ln):
    """ Turn a track off """

    if ln:
        error("Use: %s OFF with no paramater" % name)

    gbl.tnames[name].setOff()


def trackOn(name, ln):
    """ Turn a track on """

    if ln:
        error("Use: %s ON with no paramater" % name)

    gbl.tnames[name].setOn()



def trackTone(name, ln):
    """ Set the tone (note). Only valid in drum tracks."""


    gbl.tnames[name].setTone(ln)


def trackForceOut(name, ln):
    """ Force output of voice settings. """

    if len(ln):
        error("Use %s ForceOut (no options)" % name)

    gbl.tnames[name].setForceOut()


#######################################
# Misc

def trackArpeggiate(name, ln):
    """ Set up the solo/melody arpeggiator. """


    if not ln:
        error("Use: %s Arpeggiate N" % name)
  
    g=gbl.tnames[name]
    if hasattr(g, "setArp"):
        g.setArp(ln)
    else:
        warning("Arpeggiate: not permitted in %s tracks. Arg '%s' ignored." % \
                    ( g.vtype, ' '.join(ln) ) )



def trackDrumType(name, ln):
    """ Set a melody or solo track to be a drum solo track."""

    tr = gbl.tnames[name]
    if tr.vtype not in ('SOLO', 'MELODY'):
        error ("Only Solo and Melody tracks can be to DrumType, not '%s'" % name)
    if ln:
        error("No parmeters permitted for DrumType command")

    tr.setDrumType()


def trackDirection(name, ln):
    """ Set scale/arp direction. """

    if not ln:
        error("Use: %s Direction OPT" % name)


    gbl.tnames[name].setDirection(ln)


def trackScaletype(name, ln):
    """ Set the scale type. """

    if not ln:
        error("Use: %s ScaleType OPT" % name)

    gbl.tnames[name].setScaletype(ln)


def trackCopy(name, ln):
    """ Copy setting in 'ln' to 'name'. """

    if len(ln) != 1:
        error("Use: %s Copy ExistingTrack" % name)

    gbl.tnames[name].copySettings(ln[0].upper())


def trackUnify(name, ln):
    """ Set UNIFY for track."""

    if not len(ln):
        error("Use %s UNIFY 1 [...]" % name)

    gbl.tnames[name].setUnify(ln)


""" =================================================================

    Command jump tables. These need to be at the end of this module
    to avoid undefined name errors. The tables are only used in
    the parse() function.

    The first table is for the simple commands ... those which DO NOT
    have a leading trackname. The second table is for commands which
    require a leading track name.

    The alphabetic order is NOT needed, just convenient.

"""

simpleFuncs={
    'ADJUSTVOLUME':     MMA.volume.adjvolume,
    'ALLGROOVES':       MMA.grooves.allgrooves,
    'ALLTRACKS':        allTracks,
    'AUTHOR':           MMA.docs.docAuthor,
    'AUTOSOLOTRACKS':   MMA.patSolo.setAutoSolo,
    'BEATADJUST':       beatAdjust,
    'CHANNELPREF':      MMA.midifuncs.setChPref,
    'CHORDADJUST':      MMA.chords.chordAdjust,
    'COMMENT':          comment,
    'CRESC':            MMA.volume.setCresc,
    'CUT':              cut,
    'DEBUG':            setDebug,
    'DEC':              macros.vardec,
    'DECRESC':          MMA.volume.setDecresc,
    'DEFALIAS':         MMA.grooves.grooveAlias,
    'DEFCHORD':         MMA.chords.defChord,
    'DEFGROOVE':        MMA.grooves.grooveDefine,
    'DELETE':           deleteTrks,
    'DOC':              MMA.docs.docNote,
    'DOCVAR':           MMA.docs.docVars,
    'DRUMVOLTR':        MMA.translate.drumVolTable.set,
    'ELSE':             ifelse,
    'ENDIF':            ifend,
    'ENDMSET':          endmset,
    'ENDREPEAT':        repeatend,
    'EOF':              eof,
    'FERMATA':          fermata,
    'GOTO':             goto,
    'GROOVE':           MMA.grooves.groove,
    'GROOVECLEAR':      MMA.grooves.grooveClear,
    'IF':               macros.varIF,
    'IFEND':            ifend,
    'INC':              macros.varinc,
    'INCLUDE':          include,
    'KEYSIG':           keySig.set,
    'LABEL':            comment,
    'LYRIC':            lyric.option,
    'MIDIDEF':          MMA.mdefine.mdefine,
    'MIDI':             MMA.midifuncs.rawMidi,
    'MIDICOPYRIGHT':    MMA.midifuncs.setMidiCopyright,
    'MIDICUE':          MMA.midifuncs.setMidiCue,
    'MIDIFILE':         MMA.midifuncs.setMidiFileType,
    'MIDIINC':          MMA.midiIn.midiinc,
    'MIDIMARK':         MMA.midifuncs.midiMarker,
    'MIDISPLIT':        MMA.midi.setSplitChannels,
    'MIDITEXT':         MMA.midifuncs.setMidiText,
    'MIDITNAME':        MMA.midifuncs.setMidiName,
    'MMAEND':           MMA.paths.mmaend,
    'MMASTART':         MMA.paths.mmastart,
    'MSET':             macros.msetvar,
    'MSETEND':          endmset,
    'NEWSET':           macros.newsetvar,
    'PATCH':            MMA.patch.patch,
    'PRINT':            lnPrint,
    'PRINTACTIVE':      printActive,
    'PRINTCHORD':       MMA.chords.printChord,
    'REPEAT':           repeat,
    'REPEATEND':        repeatend,
    'REPEATENDING':     repeatending,
    'RESTART':          restart,
    'RNDSEED':          rndseed,
    'RNDSET':           macros.rndvar,
    'SEQ':              seq,
    'SEQCLEAR':         seqClear,
    'SEQRND':           MMA.seqrnd.setSeqRnd,
    'SEQRNDWEIGHT':     MMA.seqrnd.setSeqRndWeight,
    'SEQSIZE':          seqsize,
    'SET':              macros.setvar,
    'SETAUTOLIBPATH':   MMA.paths.setAutoPath,
    'SETINCPATH':       MMA.paths.setIncPath,
    'SETLIBPATH':       MMA.paths.setLibPath,
    'SETOUTPATH':       MMA.paths.setOutPath,
    'SHOWVARS':         macros.showvars,
    'STACKVALUE':       macros.stackValue,
    'SWELL':            MMA.volume.setSwell,
    'SWINGMODE':        MMA.swing.swingMode,
    'SYNCHRONIZE':      synchronize,
    'TEMPO':            tempo,
    'TIME':             setTime,
    'TIMESIG':          MMA.midifuncs.setTimeSig,
    'TONETR':           MMA.translate.dtable.set,
    'UNSET':            macros.unsetvar,
    'USE':              usefile,
    'VARCLEAR':         macros.clear,
    'VEXPAND':          macros.vexpand,
    'VOICEVOLTR':       MMA.translate.voiceVolTable.set,
    'VOICETR':          MMA.translate.vtable.set,
    'VOLUME':           MMA.volume.setVolume,
    'TRANSPOSE':        transpose
}


trackFuncs={
    'ACCENT':          trackAccent,
    'ARPEGGIATE':      trackArpeggiate,
    'ARTICULATE':      trackArtic,
    'CHANNEL':         trackChannel,
    'DUPRIFF':         trackDupRiff,
    'MIDIVOLUME':      trackChannelVol,
    'MIDICRESC':       trackChannelCresc,
    'MIDIDECRESC':     trackChannelDecresc,
    'CHSHARE':         trackChShare,
    'COMPRESS':        trackCompress,
    'COPY':            trackCopy,
    'CRESC':           trackCresc,
    'CUT':             trackCut,
    'DECRESC':         trackDeCresc,
    'DIRECTION':       trackDirection,
    'DRUMTYPE':        trackDrumType,
    'DUPROOT':         trackDupRoot,
    'FORCEOUT':        trackForceOut,
    'GROOVE':          MMA.grooves.trackGroove,
    'HARMONY':         trackHarmony,
    'HARMONYONLY':     trackHarmonyOnly,
    'HARMONYVOLUME':   trackHarmonyVolume,
    'INVERT':          trackInvert,
    'LIMIT':           trackChordLimit,
    'MALLET':          trackMallet,
    'MIDICLEAR':       MMA.midifuncs.trackMidiClear,
    'MIDICUE':         MMA.midifuncs.trackMidiCue,
    'MIDIDEF':         MMA.mdefine.trackMdefine,
    'MIDIGLIS':        MMA.midifuncs.trackGlis,
    'MIDIPAN':         MMA.midifuncs.trackPan,
    'MIDISEQ':         MMA.midifuncs.trackMidiSeq,
    'MIDITEXT':        MMA.midifuncs.trackMidiText,
    'MIDITNAME':       MMA.midifuncs.trackMidiName,
    'MIDIVOICE':       MMA.midifuncs.trackMidiVoice,
    'OCTAVE':          trackOctave,
    'OFF':             trackOff,
    'ON':              trackOn,
    'TUNING':          trackPlectrumTuning,
    'CAPO':            trackPlectrumCapo,
    'RANGE':           trackRange,
    'RESTART':         trackRestart,
    'RIFF':            trackRiff,
    'RSKIP':           trackRskip,
    'RTIME':           trackRtime,
    'RVOLUME':         trackRvolume,
    'SCALETYPE':       trackScaletype,
    'SEQCLEAR':        trackSeqClear,
    'SEQRND':          trackSeqRnd,
    'SEQUENCE':        trackSequence,
    'SEQRNDWEIGHT':    trackSeqRndWeight,
    'SWELL':           trackSwell,
    'MIDINOTE':        MMA.midinote.parse,
    'NOTESPAN':        trackSpan,
    'STRUM':           trackStrum,
    'TONE':            trackTone,
    'UNIFY':           trackUnify,
    'VOICE':           trackVoice,
    'VOICING':         trackVoicing,
    'VOLUME':          trackVolume,
    'DEFINE':          trackDefPattern
}


