
# grooves.py


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


""" Groove storage. Each entry in glist{} has a keyname
    of a saved groove.

    lastGroove and currentGroove are used by macros
"""

import os


import MMA.midi
import MMA.notelen
import MMA.auto
import MMA.volume
import MMA.parse
import MMA.seqrnd
import MMA.docs

import gbl
from   MMA.common import *


glist             =  {}
aliaslist         =  {}

lastGroove        =  ''     # name of the last groove (used by macros)
currentGroove     =  ''     # name of current groove (used by macros)

""" groovesList[] holds a list of grooves to use when the
     groove command is used with several args. ie, when
     we use either:

         Groove 2  groove1  groove2 groove3
     or
         Groove groove1 groove2 groove3

     in both cases, the names of the grooves are stored in groovesList[]
"""

groovesList = None
groovesCount = 0

def grooveDefine(ln):
    """ Define a groove.

        Current settings are assigned to a groove name.
    """

    if not len(ln):
        error("Use: DefGroove  Name")

    slot=ln[0].upper()

    # Slot names can't contain a '/' (reserved) or be an integer (used in groove select).

    if '/' in slot:
        error("The '/' is not permitted in a groove name")

    if slot.isdigit():
        error("Invalid slot name '%s'. Cannot be only digits" % slot)

    if slot in aliaslist:
        error("Can't define groove name %s, already defined as an alias for %s." \
                  % (slot, aliaslist[slot]))

    grooveDefineDo(slot)

    if gbl.debug:
        print "Groove settings saved to '%s'." % slot

    if gbl.makeGrvDefs:   # doing a database update ...
        MMA.auto.updateGrooveList(slot)

    if len(ln) > 1:
        MMA.docs.docDefine(ln)


def grooveDefineDo(slot):

    for n in gbl.tnames.values():
        n.saveGroove(slot)

    glist[slot] = {
        'SEQSIZE':   gbl.seqSize,
        'SEQRNDWT':  MMA.seqrnd.seqRndWeight[:],
        'QPERBAR':   gbl.QperBar,
        'SEQRND':    MMA.seqrnd.seqRnd[:],
        'TIMESIG':   MMA.midi.timeSig.get(),
        'SWINGMODE': MMA.swing.gsettings() ,
        'VRATIO':    (MMA.volume.vTRatio, MMA.volume.vMRatio)}


def grooveAlias(ln):
    """ Create an alias name for an existing groove. """

    global aliaslist

    if len(ln) != 2:
        error("GrooveAlias needs exactly 2 args: GrooveName AliasName.")

    a = ln[0].upper()
    g = ln[1].upper()

    if not g in glist:
        error("GrooveAlias: Groove %s has not been defined." % ln[0])

    aliaslist[a]=g
    

def groove(ln):
    """ Select a previously defined groove. """

    global groovesList, groovesCount, lastGroove, currentGroove

    if not ln:
        error("Groove: needs agrument(s)")

  
    tmpList =[]

    if ln[0].isdigit():
        wh=stoi(ln[0])
        if wh<1:
            error("Groove selection must be > 0, not '%s'" % wh)
        ln=ln[1:]
    else:
        wh = None

    for slot in ln:
        slot = slot.upper()
        if slot == "/":
            if len(tmpList):
                slot=tmpList[-1]
            else:
                error("A previous groove name is needed before a '/'")

        if not slot in glist:   # convert alias to real groove name
            for a,r in aliaslist.iteritems():
                if slot == a:
                    slot = r
                    break

        if not slot in glist:
            if gbl.debug:
                print "Groove '%s' not defined. Trying auto-load from libraries" \
                      % slot

            l=MMA.auto.findGroove(slot)    # name of the lib file with groove

            if l:
                if gbl.debug:
                    print "Attempting to load groove '%s' from '%s'." % (slot, l)
            
                reportFutureVols()
                MMA.parse.usefile([l])

                if not slot in glist:
                    error("Groove '%s' not found. Have libraries changed "
                          "since last 'mma -g' run?" % slot)

            else:
                error("Groove '%s' could not be found in memory or library files" % slot )

        tmpList.append(slot)

    if not len(tmpList):
        error("Use: Groove [selection] Name [...]")

    """ If the first arg to list was an int() (ie: 3 groove1 groove2 grooveFoo)
        we select from the list. After the selection, we reset the list to be
        just the selected entry. This was, if there are multiple groove names without
        a leading int() we process the list as groove list changing with each bar.
    """

    if wh:
        wh = (wh-1) % len(tmpList)
        tmpList=tmpList[wh:wh+1]

    slot=tmpList[0]
    grooveDo(slot)

    groovesCount = 0
    if len(tmpList)==1:
        groovesList=None
    else:
        groovesList=tmpList

    lastGroove = currentGroove
    currentGroove = slot
    if lastGroove == '':
        lastGroove = slot

    if gbl.debug:
        print "Groove settings restored from '%s'." % slot


def grooveDo(slot):
    """ This is separate from groove() so we can call it from
        usefile() with a qualified name. """

    reportFutureVols()

    oldSeqSize = gbl.seqSize

    g=glist[slot]

    gbl.seqSize              = g['SEQSIZE']
    MMA.seqrnd.seqRndWeight  = g['SEQRNDWT']
    gbl.QperBar              = g['QPERBAR']
    MMA.seqrnd.seqRnd        = g['SEQRND']
    MMA.midi.timeSig.set( *g['TIMESIG'])  # passing tuple as 2 args.
    MMA.swing.grestore( g['SWINGMODE'] )
    MMA.volume.vTRatio, MMA.volume.vMRatio = g['VRATIO']


    for n in gbl.tnames.values():
        n.restoreGroove(slot)

    """ This is important! Tracks NOT overwritten by saved grooves way
        have the wrong sequence length. I don't see any easy way to hit
        just the unchanged/unrestored tracks so we do them all.
        Only done if a change in seqsize ... doesn't take long to be safe.
    """

    if oldSeqSize != gbl.seqSize:
        for a in gbl.tnames.values():
            a.setSeqSize()

    MMA.seqrnd.seqRndWeight = seqBump(MMA.seqrnd.seqRndWeight)

    gbl.seqCount = 0

def reportFutureVols():
    """ Print warning for pending track cresendos.

        We need a seperate func here since the groove() may
        parse a new file, which will clear out data before
        getting to grooveDo().

        Note that the test is for more that one trailing future volume.
        This is deliberate ... a construct like:

           Chord Cresc ff 1
           ..somechord
           Groove NEW

        will leave a future volume on the stack.
    """
    
    volerrs=[]
    for n in gbl.tnames.values():
        if len(n.futureVols)>1:
            volerrs.append(n.name)
        n.futureVols = []     # don't want leftover future vols a track level!

    if volerrs:
        volerrs.sort()
        warning("Pending (de)Cresc in %s." % ', '.join(volerrs))

def grooveClear(ln):
    """ Delete all previously loaded grooves from memory."""

    global groovesList, groovesCount, glist, lastGroove, currentGroove, aliaslist

    if ln:
        error("GrooveClear does not have any arguments.")

    groovesList = {}
    aliaslist   = {}
    groovesCount = 0
    
    try:
        a= glist[gmagic]
    except:
        a=None

    glist={}

    if a:
        glist[gmagic]=a

    lastGroove = ''
    currentGroove = ''


    if gbl.debug:
        print "All grooves deleted."
    


def nextGroove():
    """ Handle groove lists. Called from parse().

        If there is more than 1 entry in the groove list,
        advance (circle). We don't have to qualify grooves
        since they were verified when this list was created.
        groovesList==None if there is only one groove (or none).
    """

    global lastGroove, currentGroove, groovesCount

    if groovesList:
        groovesCount += 1
        if groovesCount > len(groovesList)-1:
            groovesCount = 0
        slot = groovesList[groovesCount]

        if slot !=  currentGroove:
            grooveDo(slot)

            lastGroove = currentGroove
            currentGroove = slot

            if gbl.debug:
                print "Groove (list) setting restored from '%s'." % slot

           
def trackGroove(name, ln):
    """ Select a previously defined groove for a single track. """

    if len(ln) != 1:
        error("Use: %s Groove Name" % name)

    slot = ln[0].upper()
    
    if not slot in glist:  # convert alias to real groove name
        for a,r in aliaslist.iteritems():
            if slot == a:
                slot = r
                break

    if not slot in glist:
        error("Groove '%s' not defined" % slot)

    g=gbl.tnames[name]
    g.restoreGroove(slot)

    if g.sequence == [None] * len(g.sequence):
        warning("'%s' Track Groove has no sequence. Track name error?" % name)

    g.setSeqSize()

    if gbl.debug:
        print "%s Groove settings restored from '%s'." % (name, slot)



def getAlias(al):
    """ This is used by the library doc printer to get a list aliases. """


    al=al.upper()
    l=[]

    for a,r in aliaslist.iteritems():
        if al == r:
            l.append(a.title())

    
    return ', '.join(l)
    
    

def allgrooves(ln):
    """ Apply a command to all currently defined grooves. """

    if not ln:
        error("AllGrooves: requires arguments.")
    
    origSlot = MMA.parse.gmagic    # save the current groove
    grooveDefineDo(origSlot)

    action = ln[0].upper()   # either a command or a trackname

    if len(ln)>1:
        trAction = ln[1].upper()   
    else:
        trAction = ''

    sfuncs = MMA.parse.simpleFuncs
    tfuncs = MMA.parse.trackFuncs

    counter = 0

    for g in glist:   # do command for each groove in memory
        grooveDo(g)     # active existing groove

        if action in sfuncs:        # test for non-track command and exe.
            sfuncs[action](ln[1:])
            counter += 1

        else:                       # not a non-track, see if track command
            if not trAction:
                error("AllGrooves: No command for assumed trackname %s." % action)

            name = action  # remember 'action' is ln[0]. Using 'name' just makes it clearer
            if not name in gbl.tnames:  # skip command if track doesn't exist
                continue

            if trAction in tfuncs:
                tfuncs[trAction](name, ln[2:])
                counter += 1
            else:
                error ("AllGrooves: Not a command: '%s'" % ' '.join(ln))

        grooveDefineDo(g)       # store the change!!!

    grooveDo(origSlot)          # restore original state
    
    if not counter:
        warning("No tracks affected with '%s'" % ' '.join(ln))
        
    else:
        if gbl.debug:
            print "AllGrooves: %s tracks modified." % counter

