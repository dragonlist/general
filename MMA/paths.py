# paths.py

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

This module contains functions for setting various path variables.

"""

import os

import gbl
from MMA.common import *
import MMA.auto
import MMA.grooves
import MMA.exits

outfile = ''

##################################
# These routines set various filepaths in gbl


def mmastart(ln):
    """ Set/append to the mmastart list. """

    if not ln:
        error ("Use: MMAstart FILE [file...]")

    for a in ln:
        gbl.mmaStart.append(MMA.file.fixfname(a))

    if gbl.debug:
        print "MMAstart set to:",
        for a in gbl.mmaStart:
            print "'%s'" % a,
        print


def mmaend(ln):
    """ Set/append to the mmaend list. """

    if not ln:
        error ("Use: MMAend FILE [file...]")

    for a in ln:
        gbl.mmaEnd.append(MMA.file.fixfname(a))

    if gbl.debug:
        print "MMAend set to:",
        for a in gbl.mmaEnd:
            print "'%s'" % a,
        print


def setLibPath(ln):
    """ Set the LibPath variable.  """

    if len(ln) > 1:
        error("Only one path can be entered for LibPath")

    f = MMA.file.fixfname(ln[0])
    gbl.libPath = f

    # forget about previously loaded mma lib databases

    MMA.auto.grooveDB = []
    MMA.grooves.glist = {}
    MMA.grooves.lastGroove = ''
    MMA.grooves.currentGroove = ''

    if gbl.debug:
        print "LibPath set to '%s'" % gbl.libPath


def setAutoPath(ln):
    """ Set the autoPath variable.    """

    if not ln:
        error("SetAutoLibPath: At least one filename is needed.")

    gbl.autoLib = []
    for l in ln:
        gbl.autoLib.append( MMA.file.fixfname(l))

    # delete previous auto groove list. We'll read again when needed.

    MMA.auto.grooveDB = []
        
    # To avoid conflicts, delete all existing grooves (current seq not effected)

    MMA.grooves.glist = {}
    MMA.grooves.lastGroove = ''
    MMA.grooves.currentGroove = ''
    
    if gbl.debug:
        print "AutoLibPath set to '%s'" %  gbl.autoLib


def setIncPath(ln):
    """ Set the IncPath variable.  """

    if len(ln)>1:
        error("Only one path is permitted in SetIncPath")

    gbl.incPath = MMA.file.fixfname(ln[0])

    if gbl.debug:
        print "IncPath set to '%s'" %  gbl.incPath


def setOutPath(ln):
    """ Set the Outpath variable. """

    if not ln:
        gbl.outPath = ""

    elif len(ln) > 1:
        error ("Use: SetOutPath PATH")

    else:
        gbl.outPath = MMA.file.fixfname(ln[0])

    if gbl.debug:
        print "OutPath set to '%s'" % gbl.outPath



def createOutfileName(extension):
   """ Create the output filename.
    
       Called from the mainline, below and from lyrics karmode.

       If outfile was specified on cmd line then leave it alone.
       Otherwise ...
         1. strip off the extension if it is .mma,
         2. append .mid
   """
   
   global outfile

   if gbl.playFile and gbl.outfile:
       error("You cannot use the -f option with -P")

   if gbl.outfile:
       outfile = gbl.outfile

   elif gbl.playFile:
       outfile = "MMAtmp%s.mid" % os.getpid()
       MMA.exits.files.append(outfile)

   else:
       outfile, ext = os.path.splitext(gbl.infile)
       if ext != gbl.ext:
           outfile=gbl.infile
       outfile += extension

   outfile=MMA.file.fixfname(outfile)
