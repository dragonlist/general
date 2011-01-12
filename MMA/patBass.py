
# patBass.py

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
import MMA.harmony

import gbl
from   MMA.common import *
from   MMA.pat import PC


class Bass(PC):
    """ Pattern class for a bass track. """
 

    vtype = 'BASS'
    
    def getPgroup(self, ev):
        """ Get group for bass pattern.

            Fields - start, length, note, volume

        """

        if len(ev) != 4:
            error("There must be n groups of 4 in a pattern definition, "
                  "not <%s>" % ' '.join(ev) )

        a = struct()

        a.offset   = self.setBarOffset(ev[0])
        a.duration = MMA.notelen.getNoteLen( ev[1] )

        offset = ev[2]
        n=offset[0]
        if n in "1234567":
            a.noteoffset = int(n)-1
        else:
            error("Note offset in Bass must be '1'...'7', not '%s'" % n )

        n = offset[1:2]
        if n == "#":
            a.accidental = 1
            ptr = 2
        elif n == 'b' or n == 'b' or n == '&':
            a.accidental = -1
            ptr = 2
        else:
            a.accidental = 0
            ptr = 1

        a.addoctave  = 0

        for n in ev[2][ptr:]:
            if n == '+':
                a.addoctave += 12
            elif n == '-':
                a.addoctave -= 12

            else:
                error("Only '- + # b &' are permitted after a noteoffset, not '%s'" % n)

        a.vol = stoi(ev[3], "Note volume in Bass definition not int")

        return a

    def restart(self):
        self.ssvoice = -1


    def trackBar(self, pattern, ctable):
        """ Do the bass bar.

        Called from self.bar()

        """

        sc = self.seq
        unify = self.unify[sc]

        for p in pattern:
            ct = self.getChordInPos(p.offset, ctable)

            if ct.bassZ:
                continue

            note = ct.chord.scaleList[p.noteoffset] + p.addoctave + p.accidental

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





