
# patSolo.py

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

import MMA.notelen
import MMA.translate
import MMA.harmony
import MMA.volume
import MMA.alloc
import MMA.swing

import gbl

from   MMA.common import *
from   MMA.pat import PC
from   MMA.keysig import keySig

import re
import random

# Each note in a solo gets a NoteEvent. 
class NoteEvent:
    def __init__(self, pitch, velocity):
        self.duration = None
        self.pitch = pitch
        self.articulation = None
        self.velocity = velocity
        self.defvelocity = velocity

accValues = {'#': 1, "&":-1, 'n':0}

##############################

class Melody(PC):
    """ The melody and solo tracks are identical, expect that
        the solo tracks DO NOT get saved in grooves and are only
        initialized once.
    """

    vtype = 'MELODY'
    drumType = None
    
    endTilde = []
    drumTone = 38
    arpRate = 0
    arpDecay = 0
    arpDirection = 'UP'

    def setDrumType(self):
        """ Set this track to be a drum track. """

        if self.channel:
            error("You cannot change a track to DRUM once it has been used")

        self.drumType = 1
        self.setChannel('10')


    def definePattern(self, name, ln):
        error("Melody/solo patterns cannot be defined")

                
    def setArp(self, ln):
        """ Set the arpeggiate options. """

        notopt, ln = opt2pair(ln, 1)

        if notopt:
            error("%s Arpeggiate: expecting cmd=opt pairs, not '%s'." \
                      % (self.name, ' '.join(notopt) ))
        
        for cmd, opt in ln:
            if cmd == 'RATE':
                if opt == '0' or opt == 'NONE':
                    self.arpRate = 0
                else:
                    self.arpRate = MMA.notelen.getNoteLen(opt)

            elif cmd == 'DECAY':
                v = stof(opt, "Mallet Decay must be a value, not '%s'" % opt)
                if v < -50 or v > 50:
                    error("%s Arpeggiate: Decay rate must be -50..+50" % \
                              self.name )
                self.arpDecay = v/100

            elif cmd == 'DIRECTION':
                valid = ("UP", "DOWN", "BOTH", "RANDOM")
                if opt not in valid:
                    error("%s Arpeggiate Direction: Unknown setting '%s', use %s."\
                       % (self.name, opt, ', '.join(valid)))
                self.arpDirection = opt

 
    def restart(self):
        self.ssvoice = -1

    def setTone(self, ln):
        """ A solo track can have a tone, if it is DRUMTYPE."""

        if not self.drumType:
            error("You must set a Solo track to DrumType before setting Tone")

        if len(ln) > 1:
            error("Only 1 value permitted for Drum Tone in Solo tracks")
        
        
        self.drumTone = MMA.translate.dtable.get(ln[0])
       

    def xswingIt(self, notes):
        """ Adjust an entire bar of chords for swingmode.

            Check each chord in the array of chords for a bar for 
            successive 8ths on & off the beat. If found, the first is
            converted to 'long' 8th, the 2nd to a 'short'
            and the offset for the 2nd is adjusted to comp. for the 'long'.

            If there is a spurious offset between an on/off beat that pair
            will NOT be adjusted. Nor sure if that is right or not?

            Only called from getLine(), separate for sanity.
        """

        len8  = MMA.notelen.getNoteLen('8')
        len81 = MMA.notelen.getNoteLen('81')
        len82 = MMA.notelen.getNoteLen('82')
        all8 = set([len8])        
        onBeats = [ x * gbl.BperQ for x in range(gbl.QperBar)]

        nl = sorted(notes)   # list of offsets
        for i in range(len(nl)-1):
            
            # Check for successive note event offsets on 8th note positions

            if nl[i] in onBeats and nl[i+1] == nl[i]+len8:
                beat0 = nl[i]
                beat1 = nl[i+1]

                # check that all notes are 8ths by comparing a set of all
                # the durations in both offsets with set([len8])

                if set([nev.duration for nev in notes[beat0]+notes[beat1] ]) == all8:

                    # lengthen notes on-the-beat

                    for nev in notes[beat0]:
                        nev.duration = len81
                        nev.velocity *= MMA.swing.accent1
                        nev.defvelocity *= MMA.swing.accent1

                    # shorten notes off-the-beat

                    for nev in notes[beat1]:
                        nev.duration = len82
                        nev.velocity *= MMA.swing.accent2
                        nev.defvelocity *= MMA.swing.accent2

                    # move off-beat list back

                    notes[beat0+len81] = notes[beat1]
                    del notes[beat1]

        return notes

    def getChord(self, c, velocity, isdrum):
        """ Extract a set of notes for a single beat. 

            This is a function just to make getLine() a bit shorter
            and more readble.
        """

        c = re.split("[, ]+", c)

        if not c:
            error("You must specify the first note in a solo line")

        """ Convert the note part into a series of midi values
            Notes can be a single note, or a series of notes. And
            each note can be a letter a-g (or r), a '#,&,n' plus
            a series of '+'s or '-'s. Drum solos must have each
            note separated by ' ' or ','s: "Snare1,KickDrum1,44".

            Each chunk could be:
             - a midi value (44)
             - a drum note ( KickDrum1)
             - a single note (g#) (g&-)
             - Or groups with spaces/commas (f 100) (44 , KickDrum) (a,b c)
        """

        events = []   # array for each note event

        for cc in c:
            if not cc or not cc[0]:
                continue
            if '/' in cc:
                if cc.count('/') > 1:
                    error("%s: Only 1 '/velocity' permitted. You can separate " \
                          "notes in the chord with ',' or ' ' and it'll work." % \
                              self.name)
                cc, newvel = cc.split('/')
                if not newvel:
                    error("%s: expecting 'volume' after '/'" % self.name)

                if not cc:
                    error("%s: Volume '/' must immediately follow note." % self.name)

                thisvel = stoi(newvel)

                if thisvel < 0 or thisvel > 127:
                    error("%s: Velocity must be 0..127, not '%s'." % (self.name, newvel))
            else:
                thisvel = velocity

            if cc[0] == 'r':
                if events or len(cc) > 1:
                    error("%s: Rests and notes cannot be combined." % self.name)
                else:
                    events.append( NoteEvent(None, 0))  # note event with no pitch


            elif cc[0] in "1234567890":
                n = stoi(cc, "%s: Note values must be integer or literal." % \
                             self.name)
                if n<0 or n>127:
                    error("%s: Midi notes must be 0..127, not '%s'" % \
                              (self.name, n))

                # if using value we fake-adjust octave,
                # it (and transpose) is set later.

                if not isdrum:
                    n -= self.octave[self.seq]
                     
                events.append(NoteEvent(n, thisvel))


            elif isdrum:       # drum must be a value, * or drum-name
                if cc == '*':
                    events.append( NoteEvent(self.drumTone, thisvel ))
                else:
                    events.append( NoteEvent(int(MMA.translate.dtable.get(cc)), thisvel) )

            else:   # must be a note(s) in std. notation
                cc = list(cc)
                while cc:
                    name = cc.pop(0)

                    if not name in self.midiNotes:
                        error("%s: Encountered illegal note name '%s'"
                              % (self.name, name))

                    n = self.midiNotes[ name ]  # name is string, n is value
                    
                    # Parse out a "#', '&' or 'n' accidental.

                    if cc and cc[0] in accValues:
                        i = cc.pop(0)
                        self.acc[name] = accValues[i]

                    n += self.acc[name]  # accidental adjust (from above or keysig)

                    # Parse out +/- (or series) for octave

                    while cc and cc[0] in '+-':
                        a = cc.pop(0)
                        if a == '+':
                            n += 12
                        else:
                            n -= 12

                    events.append( NoteEvent(n, thisvel) )
                    

        return events

    def getLine(self, pat):
        """ Extract a melodyline for solo/melody tracks.

            This is only called from trackbar(), but it's nicer
            to isolate it here.


            RETURNS: notes structure. This is a dictionary. Each key represents
                     an offset in MIDI ticks in the current bar. The data for
                     each entry is an array of note events:

                 notes[offset] - [nev [,...] ] See top of file for noteEvent()
                                  class which sets the fields.
        """
 
        sc=self.seq

        savedSpecial = None

        """ Get a COPY of the keysignature note table (a dict). 
            As a bar is processed the table is updated. There is one flaw here---in
            real music an accidental for a note in a give octave does not
            effect the following same-named notes in different octaves.
            In this routine IT DOES.
        """

        self.acc=keySig.accList.copy()

        # list of notename to midivalues

        self.midiNotes = {'c':0, 'd':2, 'e':4, 'f':5, 'g':7, 'a':9, 'b':11, 'r':None }


        """ The initial string is in the format "1ab;4c;;4r;". The trailing
            ';' is important and needed. If we don't have this requirement
            we can't tell if the last note is a repeat of the previous. For
            example, if we have coded "2a;2a;" as "2a;;" and we didn't
            have the 'must end with ;' rule, we end up with "2a;" and
            then we make this into 2 notes...or do we? Easiest just to
            insist that all bars end with a ";".
        """

        if not pat.endswith(';'):
            error("All Solo strings must end with a ';'")
 
        barEnd   = gbl.BperQ*gbl.QperBar          # end of bar in ticks
        duration = MMA.notelen.getNoteLen('4')    # default note length
        velocity = 90               # intial/default velocity for solo notes
        articulation = 1            # additional articulation for solo notes

        notes={}   # NoteEvent list, keys == offset
        
        if self.drumType:
            isdrum = 1
            lastc = str(self.drumTone)
        else:
            isdrum = None
            lastc = ''             # last parsed note        

        # convert pat to a list
        pat = [x.strip() for x in pat.split(';')[:-1]]

        # set initial offset into bar. This compensates for the previous
        # bar ending in a ~ and this one starting with ~.
        # This special case bumps the initial bar offset

        if pat[0].startswith("~"):
            if not self.endTilde or self.endTilde[1] != gbl.tickOffset:
                error("Previous line did not end with '~'")
            else:
                pat[0] = pat[0][1:].strip()
                offset = self.endTilde[0]
        else:
            offset = 0

        lastOffset = None

        # Strip off trailing ~. This permits long notes to end past the
        # current barend. Note, flag set for the next bar to test for
        # a leading ~.

        if pat[-1].endswith("~"):
            self.endTilde = [1, gbl.tickOffset + (gbl.BperQ * gbl.QperBar) ]
            pat[-1] = pat[-1][:-1].strip()
        else:
            self.endTilde = []

        ##################################################
        # Now we can parse each chunk of the solo string.

        for a in pat:
            """ If we find a "<>" we just ignore that. It's useful when
                multiple continuation bars are needed with ~.
            """
            
            accentVol = None
            accentDur = None

            if a == '<>':
                savedSpecial = None
                continue

            """ Next, strip out all '<SPECIAL=xx>' settings.

              VOLUME: If no option is set, we assume VOLUME. The default
                      velocity setting was set before the loop (==90) and is
                      changed here for the duration of the current bar/riff.
                      The set velocity will still be modified by the global
                      and track volume adjustments.
            
              DURATION: Duration or articulation setting is defaulted to 100.
                        Changing it here will do so for the duration of the
                        bar/riff. Note, the track ARTICULATION is still applied.

              OFFSET: change the current offset into the bar. Can be negative
                      which forces overlapping notes.

            """

            a, vls = pextract(a, "<", ">")

            if vls:
                if len(vls) > 1:
                    error("Only 1 <modifier> is permitted per note-set")

                vls = vls[0].split(',')
                for vv in vls:

                    vv = vv.upper().strip()

                    if vv == '..':
                        savedSpecial = [','.join(vls)]
                        continue

                    if not '=' in vv:
                        vv = "VOLUME=" + vv
                        
                    vc,vo = vv.split('=', 1)  # note: it's already uppercase!

                    if vc == 'VOLUME':
                        if vo in MMA.volume.vols:   # arg was a volume 'FF, 'mp', etc.
                            velocity *= MMA.volume.vols[vo]
                        else:
                            error("%s: No volume '%s'." % (self.name, vo))
                    
                    elif vc == 'OFFSET':
                        offset = stoi(vo, "%s: Offset expecting integer, not %s." \
                                          % (self.name, vo))

                        if offset < 0:
                            error("%s: Offset must be positive." % self.name)

                        if offset >= barEnd:
                            error("%s: Offset has been set past the end of the bar." \
                                      % self.name )

                    elif vc == 'ARTICULATE':
                        articulation = stoi(vo, "%s: Articulation expecting integer,"
                                     " not %s." % (self.name, vo))
       
                        if articulation < 1 or articulation >200:
                                error("%s: Articulation must be 1..200, not %s." % \
                                          (self.name, vo) )
                        articulation /= 100.

                    else:
                        error("%s: Unknown command '%s'." % (self.name, vv))

            if offset >= barEnd:
                error("Attempt to start Solo note '%s' after end of bar" % a)

            """ Split the chord chunk into a note length and notes. Each
                part of this is optional and defaults to the previously
                parsed value.
            """

            i = 0
            while i < len(a):
                if not a[i] in '1234567890.+tT':
                    break
                else:
                    i += 1

            if i:
                l=MMA.notelen.getNoteLen(a[0:i].replace(' ', '') )
                a = a[i:].strip()
            else:
                l=duration

            duration = l    # save last duration for next loop

            # next item might be an accent string. 

            i = 0
            while i < len(a):
                if not a[i] in "!-^&":
                    break
                else:
                    i += 1

            if i:
                c = a[0:i]
                accentVol = 1
                accentDur = 1

                accentDur -=  c.count('!') * .2
                accentDur +=  c.count('-') * .2

                accentVol +=  c.count('^') * .2
                accentVol -=  c.count('&') * .2

                if accentDur<.1: accentDur = .1
                if accentDur>2:  accentDur = 2
                if accentVol<.1: accentVol = .1
                if accentVol>2:  accentVol = 2
                a = a[i:]

            # Now we get to look at pitches.

            if not a or a=='' or a==' ':
                a=lastc
            evts = self.getChord(a, velocity, isdrum)  # get chord

            for e in evts:
                e.velocity = self.adjustVolume(e.defvelocity, offset)
                if accentVol:
                    e.velocity *=  accentVol
                e.duration = duration

                if accentDur:
                    e.articulation = articulation * accentDur
                else:
                    e.articulation = articulation                

            lastc = a     # save last chord for next loop


            # add note event(s) to note{}

            if not offset in notes:
                notes[offset] = []
            notes[offset].extend(evts)

            lastOffset = offset
            offset += l


        if offset <= barEnd:
            if self.endTilde:
                error("Tilde at end of bar has no effect")

        else:
            if self.endTilde:
                self.endTilde[0]=offset-barEnd
            else:
                warning("%s, end of last note overlaps end of bar by %2.3f "
                    "beat(s)." % (self.name, (offset-barEnd)/float(gbl.BperQ)))

        if MMA.swing.mode:
            notes = MMA.swing.swingSolo(notes)

        return notes


    def addHarmony(self, notes, ctable):
        """ Add harmony to solo notes. """
        
        sc=self.seq

        harmony = self.harmony[sc]
        harmOnly = self.harmonyOnly[sc]
        
        
        for offset in notes:
            nn = notes[offset]

            if len(nn) == 1 and nn[0].pitch != None:
                tb = self.getChordInPos(offset, ctable)

                if tb.chordZ:
                    continue

                h = MMA.harmony.harmonize(harmony, nn[0].pitch, tb.chord.bnoteList)

                duration = nn[0].duration
                articulation = nn[0].articulation
                velocity = nn[0].defvelocity

                if harmOnly:  # remove melody note if harmony only
                    nn.pop(0)  # DON'T use nn=[] that would release the ptr.

                for n in h:
                    e = NoteEvent(n,
                         self.adjustVolume(velocity * self.harmonyVolume[sc], offset))
                    e.duration = duration
                    e.articulation = articulation
                    nn.append(e)
                    

    def trackBar(self, pat, ctable):
        """ Do the solo/melody line. Called from self.bar() """
        
        notes = self.getLine(pat)
        sc=self.seq
        
        if self.harmony[sc] and not self.drumType:
            self.addHarmony(notes, ctable)

        unify = self.unify[sc]

        rptr = self.mallet

        for offset in sorted(notes.keys()):
            nn=notes[offset]
            strumOffset = 0
            
            if self.arpRate:
                self.trackArp(nn, offset)
                continue

            for nev in nn:
                n = nev.pitch
                if n == None:     # skip rests
                    continue

                if not self.drumType:        # no octave/transpose for drums
                    n = self.adjustNote(n)
                self.sendNote(offset + strumOffset, 
                       self.getDur(int(nev.duration * nev.articulation)),
                       n, self.adjustVolume(nev.velocity, offset) )
                strumOffset += self.getStrum(sc)


    def trackArp(self, nn, offset):
        """ Special trackbar() for arpeggiator. """

        if self.drumType:
            error("%s Arpeggiate: Incompatible with DRUMTYPE. Try MALLET?" % self.name)
        
        notes = [ [self.adjustNote(x.pitch), x.velocity] for x in nn]
        notes.sort()

        random = self.direction == 'RANDOM'

        if self.arpDirection == "DOWN":
            notes.reverse()

        elif self.arpDirection == "BOTH":
            z=notes[:]
            z.reverse()
            notes.extend(z[1:-1])

        duration = self.arpRate             # duration of each note
        count = nn[0].duration / duration   # total number to play
        if count < 1:
            count = 1

        while 1:
            nn = range(len(notes))
            if random:
                random.randomize(nn)
            for i in nn:
                n = notes[i]
 
                self.sendNote(offset, 
                      self.getDur(duration), n[0],
                      self.adjustVolume(n[1], offset) )
                count -= 1
                if not count:
                    break

                offset += duration

                if self.arpDecay:
                    n[1] = int(n[1] + (n[1] * self.arpDecay))
                    if n[1] < 1: n[1] = 1
                    if n[1] > 127: n[1] = 127
                    
 
            if not count:
                break
               

 
class Solo(Melody):
    """ Pattern class for a solo track. """

    vtype = 'SOLO'


    # Grooves are not saved/restored for solo tracks.

    def restoreGroove(self, gname):
        self.setSeqSize()

    def saveGroove(self, gname):
        pass


#######################

""" When solos are included in a chord/data line they are
    assigned to the tracks listed in this list. Users can
    change the tracks with the setAutoSolo command.
"""

autoSoloTracks = [ 'SOLO', 'SOLO-1', 'SOLO-2', 'SOLO-3' ]


def setAutoSolo(ln):
    """ Set the order and names of tracks to use when assigning
        automatic solos (specified on chord lines in {}s).
    """

    global autoSoloTracks

    if not len(ln):
        error("You must specify at least one track for autosolos")

    autoSoloTracks = []
    for n in ln:
        n=n.upper()
        MMA.alloc.trackAlloc(n, 1)
        if gbl.tnames[n].vtype not in ('MELODY', 'SOLO'):
            error("All autotracks must be Melody or Solo tracks, not %s"\
                      % gbl.tnames[n].vtype)

        autoSoloTracks.append(n)

    if gbl.debug:
        print "AutoSolo track names:",
        for a in autoSoloTracks:
            print a,
        print



###############


def extractSolo(ln, rptcount):
    """ Parser calls this to extract solo strings. """

    a = ln.count('{')
    b = ln.count('}')

    if a != b:
        error("Mismatched {}s for solo found in chord line")

    if a:
        if rptcount > 1:
            error("Bars with both repeat count and solos are not permitted")

        ln, solo = pextract(ln, '{', '}')
        
        if len(solo) > len(autoSoloTracks):
            error("Too many melody/solo riffs in chord line. %s used, "
                  "only %s defined" % (len(solo), len(autoSoloTracks)) )


        firstSolo = solo[0][:]  # save for autoharmony tracks
        
        """ We have the solo information. Now we loop though each "solo" and:
              1. Ensure or Create a MMA track for the solo
              2. Push the solo data into a Riff for the given track.
        """

        for s, trk in zip(solo, autoSoloTracks):
            if not s: continue    # skip placeholder/empty tracks
            MMA.alloc.trackAlloc(trk, 1)
            t = gbl.tnames[trk]
            if t.riff:
                error("%s: Attempt to add {} solo when the track "
                      "has pending RIFF data." % t.name)
            t.setRiff( s.strip() )

        """ After all the solo data is interpreted and sent to the
            correct track, we check any leftover tracks. If any of these
            tracks are  empty of data AND are harmonyonly the note
            data from the first track is interpeted again for that
            track. Tricky: the max() is needed since harmonyonly can
            have different setting for each bar...this way
            the copy is done if ANY bar in the seq has harmonyonly set.
        """

        for t in autoSoloTracks[1:]:
            if t in gbl.tnames and not gbl.tnames[t].riff \
                   and max(gbl.tnames[t].harmonyOnly):
                gbl.tnames[t].setRiff( firstSolo[:] )

                if gbl.debug:
                    print "%s duplicated to %s for HarmonyOnly." % (trk, t)

    return ln

