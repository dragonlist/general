import MMA.midi
import MMA.midifuncs
import MMA.parse
import MMA.options
import MMA.auto
import MMA.lib

import gbl
from   MMA.common import *
from   MMA.lyric import lyric


def setup():
  # Set up initial meta track stuff. Track 0 == meta
  m = gbl.mtrks[0] = MMA.midi.Mtrk(0)
  m.addTempo(0, gbl.tempo)
  MMA.midifuncs.setTimeSig(['4','4'])
  gbl.createDocs = 0


def libUpdate():
  MMA.auto.libUpdate()

def parseMMA(content):
  setup()
  return 'done' 

def mma2midi(content_string):
  setup()
  
  for f in gbl.mmaStart:
      fn = MMA.file.locFile(f, gbl.incPath)
      if not fn:
          warning("MmaStart file '%s' not found/processed" % fn)
      MMA.parse.parseFile(fn)
      gbl.lineno = -1
  
  # The song file specified on the command line
  
  f = MMA.file.locFile(gbl.infile, None)
  
  if not f:
      gbl.lineno = -1
      error("Input file '%s' not found" % gbl.infile)
  
  MMA.parse.parseFile(f)
  
  # Finally, the mmaend files
  
  for f in gbl.mmaEnd:
      fn = MMA.file.locFile(f, None)
      if not fn:
          warning("MmaEnd file '%s' not found/processed" % f)
      MMA.parse.parseFile(fn)
  
  #################################################
  # Just display the channel assignments (-c) and exit...
  
  if gbl.chshow:
      print "\nFile '%s' parsed, but no MIDI file produced!" % gbl.infile
      print
      print "Tracks allocated:"
      k=gbl.tnames.keys()
      k.sort()
      max=0
      for a in k + gbl.deletedTracks:
          if len(a)>max:
              max = len(a)
      max+=1
      wrap=0
      for a in k:
          wrap += max
          if wrap>60:
              wrap = max
              print
          print " %-*s" %( max, a),
      print
      print
      if gbl.deletedTracks:
          print "Deleted Tracks:"
          wrap=0
          for a in gbl.deletedTracks:
              wrap += max
              if wrap>60:
                  wrap=max
                  print
              print " %-*s" %( max,a),
          print
          print
      print "Channel assignments:"
      for c, n in sorted(gbl.midiAssigns.items()):
          if n:
              wrap = 3
              print " %2s" % c,
              for nn in n:
                  wrap += max
                  if wrap>63:
                      print "\n   ",
                      wrap=max+3
                  print "%-*s" % (max,nn),
  
              print
      print
      sys.exit(0)
  
  
  ##############################
  # Create the output (MIDI) file
  
  gbl.lineno=-1    # disable line nums for error/warning
  
  
  """ We fix the outPath now. This lets you set outpath in the song file.
  
      The filename "outfile" was created in paths, get a copy.
  
      It is either the input filename with '.mma' changed to '.mid' (or kar)
      OR if -f<FILE> was used then it's just <FILE>.
  
      If any of the following is true we skip inserting the outputpath into the
      filename:
  
          - if outfile starts with a '/'
          - if outPath was not set
          - if -f was used
  
      Next, the outPath is inserted into the filename. If outPath starts with
      a ".", "/" or "\ " then it is inserted at the start of the path;
      otherwise it is inserted before the filename portion.
  """
  
  outfile = MMA.paths.outfile
  
  if (not outfile.startswith('/')) and gbl.outPath and not gbl.outfile and not gbl.playFile:
      if gbl.outPath[0] in '.\\/':
          outfile = "%s/%s" % (gbl.outPath, outfile)
      else:
          head, tail = os.path.split(outfile)
          outfile = "%s/%s/%s" % (head, gbl.outPath, tail)
  
  fileExist = os.path.exists(outfile)
  
  """ Check if any pending midi events are still around. Mostly
      this will be a DRUM event which was assigned to the 'DRUM'
      track, but no DRUM track was used, just DRUM-xx tracks used.
  """
  
  for n in gbl.tnames.values():
      if n.channel:
          n.doMidiClear()
          n.clearPending()
          n.doChannelReset()
          if n.riff:
              warning("%s has pending Riff(s)" % n.name)
  
  """ Check all the tracks and find total number used. When
      initializing each track (class) we made an initial entry
      in the track at offset 0 for the track name, etc. So, if the
      track only has one entry we can safely skip the entire track.
  """
  
  trackCount=1    # account for meta track
  
  for n in sorted(gbl.mtrks.keys())[1:]:     # check all but 0 (meta)
      if len(gbl.mtrks[n].miditrk) > 1:
          trackCount += 1
  
  if trackCount == 1: # only meta track
      if fileExist:
          print
      print "No data created. Did you remember to set a groove/sequence?"
      if fileExist:
          print "Existing file '%s' has not been modified." % outfile
      sys.exit(1)
  
  lyric.leftovers()
  
  if fileExist:
      print "Overwriting existing",
  else:
      print "Creating new",
  print "midi file (%s bars, %.2f min): '%s'" %  (gbl.barNum, gbl.totTime, outfile)
  
  try:
      out = file(outfile, 'wb')
  except:
      error("Can't open file '%s' for writing" % outfile)
  
  MMA.midi.writeTracks(out)
  out.close()
  
  
  
