
# patAria.py

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

import random

import MMA.notelen 
import MMA.harmony

import gbl
from   MMA.common import *
from   MMA.pat import PC


class Aria(PC):
    """ Pattern class for an aria (auto-melody) track. """

    vtype = 'ARIA'
    notes = []
    selectDir = [1]
    noteptr = 0
    dirptr  = 0
    lastChord = None
    lastStype = None
    lastRange = None


    def restoreGroove(self, gname):
        """ Grooves are not saved/restored for aria tracks. But, seqsize is honored! """
        self.setSeqSize()

    def saveGroove(self, gname):
        """ No save done for grooves. """
        pass


    def getPgroup(self, ev):
        """ Get group for aria pattern.

            Fields - start, length, velocity

        """

        if len(ev) != 3:
            error("There must be n groups of 3 in a pattern definition, "
                  "not <%s>" % ' '.join(ev) )

        a = struct()

        a.offset   = self.setBarOffset(ev[0])
        a.duration = MMA.notelen.getNoteLen( ev[1] )
        a.vol =  stoi(ev[2], "Note volume in Aria definition not int")

        return a


    def setScaletype(self, ln):
        """ Set scale type. """

        ln = lnExpand(ln, "%s ScaleType" % self.name)
        tmp = []

        for n in ln:
            n = n.upper()
            if not n in ( 'CHROMATIC', 'SCALE', 'AUTO', 'CHORD'):
                error("Unknown %s ScaleType. Only Chromatic, Scale (Auto) and Chord are valid" % self.name)
            tmp.append(n)

        self.scaleType = seqBump(tmp)

        if gbl.debug:
            print "Set %s ScaleType: " % self.name,
            printList(self.scaleType)


    def setDirection(self, ln):
        """ Set direction for melody creation.

            This function replaces the pattern function of the same name ...
            the command name is shared, the function is different. Note we
            need to use a different storage name as well since
            self.direction is managed in the PC class.
        """

        if not len(ln):
            error("There must be at least one value for %s Direction." % self.name)
        
        self.selectDir = []
        for a in ln:
            if set(a.upper()) == set('R'):    # is direction 'r', 'rr', 'rrr', etc.
                if len(a) > 4:
                    error("Aria Direction has too much randomness"
                          "(Maximum of 4 r's, got %d)." % len(a))
                self.selectDir.append(a.upper())
            else:   # not random, has to be an integer -4 ... 4
                a=stoi(a, "Expecting integer value or 'r*'.")
                if a < -4 or a > 4:
                    error("Aria direction must be 'r' or -4 to 4, not '%s'" % a)
                self.selectDir.append(a)

        if gbl.debug:
            print "Set %s Direction:" % self.name,
            printList(self.selectDir)

    def restart(self):
        self.ssvoice = -1
 

    def trackBar(self, pattern, ctable):
        """ Do the aria bar.

        Called from self.bar()

        """

        sc = self.seq
        unify = self.unify[sc]

        for p in pattern:
            ct = self.getChordInPos(p.offset, ctable)

            if ct.ariaZ:
                continue

            thisChord = ct.chord.tonic + ct.chord.chordType
            stype = self.scaleType[sc]
            chrange = self.chordRange[sc]

            ### Generate notelist if nesc.

            if self.lastChord != thisChord or self.lastStype != stype or \
                    self.lastRange != chrange:

                self.lastChord = thisChord
                self.lastStype = stype
                self.lastRange = chrange

                if stype == 'CHORD':
                    notelist = ct.chord.noteList
                elif stype == 'CHROMATIC':
                    notelist = [ ct.chord.rootNote + x for x in range(0,12)]
                else:
                    notelist = list(ct.chord.scaleList)

                o=0
                self.notes=[]

                while chrange >= 1:
                    for a in notelist:
                        self.notes.append(a+o)
                    o+=12
                    chrange-=1

                if chrange>0 and chrange<1:  # for fractional scale lengths
                    chrange = int(len(notelist) * chrange)
                    if chrange < 2:   # important, must be at least 2 notes in a scale
                        chrange=2
                    for a in notelist[:chrange]:
                        self.notes.append(a+o)
            
            # grab a note from the list

            if self.dirptr >= len(self.selectDir):
                self.dirptr=0
            
            # the direction ptr is either an int(-4..4) or a string of 'r', 'rr, etc.

            a = self.selectDir[self.dirptr]
  
            if type(a) == type(1):
                self.noteptr += a
            else:
                self.noteptr += random.choice( range(-len(a), len(a)+1 ))

            if self.noteptr >= len(self.notes):
                if a > 0:
                    self.noteptr = 0
                else:
                    self.noteptr = len(self.notes)-1
            elif self.noteptr < 0:
                if a < 0:
                    self.noteptr = len(self.notes)-1
                else:
                    self.noteptr = 0

            note = self.notes[self.noteptr]
            self.dirptr  += 1

            # output

            if not self.harmonyOnly[sc]:
                self.sendNote(
                    p.offset,
                    self.getDur(p.duration),
                    self.adjustNote(note),
                    self.adjustVolume(p.vol, p.offset))

            if self.harmony[sc]:
                h = MMA.harmony.harmonize(self.harmony[sc], note, ct.chord.noteList)
                
                strumOffset = self.getStrum(sc)

                for n in h:
                    self.sendNote(
                        p.offset + strumOffset,
                        self.getDur(p.duration),
                        self.adjustNote(n),
                        self.adjustVolume(p.vol * self.harmonyVolume[sc], -1))

                    strumOffset += self.getStrum(sc)
