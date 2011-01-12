
# miditables.py

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

This module contains the constant names for the various
MIDI controllers.

Having only the constants in this separate file permits to
call this from other programs, mainly the mma doc creators.


              **** IMPORTANT *** IMPORTANT
   
   The tables *Names/*Inx MUST have matching keys/values.
   The KEYS in the *Inx tables are the values from the
   *Name tables in UPPERCASE. Be very careful making changes!!!!!

"""

#  Standard GM drum tone  names.

drumNames={
    27:'HighQ', 28:'Slap', 29:'ScratchPush',
    30:'ScratchPull', 31:'Sticks', 32:'SquareClick',
    33:'MetronomeClick', 34:'MetronomeBell', 35:'KickDrum2',
    36:'KickDrum1', 37:'SideKick', 38:'SnareDrum1',
    39:'HandClap', 40:'SnareDrum2', 41:'LowTom2',
    42:'ClosedHiHat', 43:'LowTom1', 44:'PedalHiHat',
    45:'MidTom2', 46:'OpenHiHat', 47:'MidTom1',
    48:'HighTom2', 49:'CrashCymbal1', 50:'HighTom1',
    51:'RideCymbal1', 52:'ChineseCymbal', 53:'RideBell',
    54:'Tambourine', 55:'SplashCymbal', 56:'CowBell',
    57:'CrashCymbal2', 58:'VibraSlap', 59:'RideCymbal2',
    60:'HighBongo', 61:'LowBongo', 62:'MuteHighConga',
    63:'OpenHighConga', 64:'LowConga', 65:'HighTimbale',
    66:'LowTimbale', 67:'HighAgogo', 68:'LowAgogo',
    69:'Cabasa', 70:'Maracas', 71:'ShortHiWhistle',
    72:'LongLowWhistle', 73:'ShortGuiro', 74:'LongGuiro',
    75:'Claves', 76:'HighWoodBlock', 77:'LowWoodBlock',
    78:'MuteCuica', 79:'OpenCuica', 80:'MuteTriangle',
    81:'OpenTriangle', 82:'Shaker', 83:'JingleBell',
    84:'Castanets', 85:'MuteSudro', 86:'OpenSudro'}

drumInx={
    'HIGHQ':27, 'SLAP':28, 'SCRATCHPUSH':29,
    'SCRATCHPULL':30, 'STICKS':31, 'SQUARECLICK':32,
    'METRONOMECLICK':33, 'METRONOMEBELL':34, 'KICKDRUM2':35,
    'KICKDRUM1':36, 'SIDEKICK':37, 'SNAREDRUM1':38,
    'HANDCLAP':39, 'SNAREDRUM2':40, 'LOWTOM2':41,
    'CLOSEDHIHAT':42, 'LOWTOM1':43, 'PEDALHIHAT':44,
    'MIDTOM2':45, 'OPENHIHAT':46, 'MIDTOM1':47,
    'HIGHTOM2':48, 'CRASHCYMBAL1':49, 'HIGHTOM1':50,
    'RIDECYMBAL1':51, 'CHINESECYMBAL':52, 'RIDEBELL':53,
    'TAMBOURINE':54, 'SPLASHCYMBAL':55, 'COWBELL':56,
    'CRASHCYMBAL2':57, 'VIBRASLAP':58, 'RIDECYMBAL2':59,
    'HIGHBONGO':60, 'LOWBONGO':61, 'MUTEHIGHCONGA':62,
    'OPENHIGHCONGA':63, 'LOWCONGA':64, 'HIGHTIMBALE':65,
    'LOWTIMBALE':66, 'HIGHAGOGO':67, 'LOWAGOGO':68,
    'CABASA':69, 'MARACAS':70, 'SHORTHIWHISTLE':71,
    'LONGLOWWHISTLE':72, 'SHORTGUIRO':73, 'LONGGUIRO':74,
    'CLAVES':75, 'HIGHWOODBLOCK':76, 'LOWWOODBLOCK':77,
    'MUTECUICA':78, 'OPENCUICA':79, 'MUTETRIANGLE':80,
    'OPENTRIANGLE':81, 'SHAKER':82, 'JINGLEBELL':83,
    'CASTANETS':84, 'MUTESUDRO':85, 'OPENSUDRO':86}



# Standard GM voice names. 


voiceNames={
    0:'Piano1', 1:'Piano2', 2:'Piano3',
    3:'Honky-TonkPiano', 4:'RhodesPiano', 5:'EPiano',
    6:'HarpsiChord', 7:'Clavinet', 8:'Celesta',
    9:'Glockenspiel', 10:'MusicBox', 11:'Vibraphone',
    12:'Marimba', 13:'Xylophone', 14:'TubularBells',
    15:'Santur', 16:'Organ1', 17:'Organ2',
    18:'Organ3', 19:'ChurchOrgan', 20:'ReedOrgan',
    21:'Accordion', 22:'Harmonica', 23:'Bandoneon',
    24:'NylonGuitar', 25:'SteelGuitar', 26:'JazzGuitar',
    27:'CleanGuitar', 28:'MutedGuitar', 29:'OverDriveGuitar',
    30:'DistortonGuitar', 31:'GuitarHarmonics', 32:'AcousticBass',
    33:'FingeredBass', 34:'PickedBass', 35:'FretlessBass',
    36:'SlapBass1', 37:'SlapBass2', 38:'SynthBass1',
    39:'SynthBass2', 40:'Violin', 41:'Viola',
    42:'Cello', 43:'ContraBass', 44:'TremoloStrings',
    45:'PizzicatoString', 46:'OrchestralHarp', 47:'Timpani',
    48:'Strings', 49:'SlowStrings', 50:'SynthStrings1',
    51:'SynthStrings2', 52:'ChoirAahs', 53:'VoiceOohs',
    54:'SynthVox', 55:'OrchestraHit', 56:'Trumpet',
    57:'Trombone', 58:'Tuba', 59:'MutedTrumpet',
    60:'FrenchHorn', 61:'BrassSection', 62:'SynthBrass1',
    63:'SynthBrass2', 64:'SopranoSax', 65:'AltoSax',
    66:'TenorSax', 67:'BaritoneSax', 68:'Oboe',
    69:'EnglishHorn', 70:'Bassoon', 71:'Clarinet',
    72:'Piccolo', 73:'Flute', 74:'Recorder',
    75:'PanFlute', 76:'BottleBlow', 77:'Shakuhachi',
    78:'Whistle', 79:'Ocarina', 80:'SquareWave',
    81:'SawWave', 82:'SynCalliope', 83:'ChifferLead',
    84:'Charang', 85:'SoloVoice', 86:'5thSawWave',
    87:'Bass&Lead', 88:'Fantasia', 89:'WarmPad',
    90:'PolySynth', 91:'SpaceVoice', 92:'BowedGlass',
    93:'MetalPad', 94:'HaloPad', 95:'SweepPad',
    96:'IceRain', 97:'SoundTrack', 98:'Crystal',
    99:'Atmosphere', 100:'Brightness', 101:'Goblins',
    102:'EchoDrops', 103:'StarTheme', 104:'Sitar',
    105:'Banjo', 106:'Shamisen', 107:'Koto',
    108:'Kalimba', 109:'BagPipe', 110:'Fiddle',
    111:'Shanai', 112:'TinkleBell', 113:'AgogoBells',
    114:'SteelDrums', 115:'WoodBlock', 116:'TaikoDrum',
    117:'MelodicTom1', 118:'SynthDrum', 119:'ReverseCymbal',
    120:'GuitarFretNoise', 121:'BreathNoise', 122:'SeaShore',
    123:'BirdTweet', 124:'TelephoneRing', 125:'HelicopterBlade',
    126:'Applause/Noise', 127:'GunShot' }

voiceInx={
    'PIANO1':0, 'PIANO2':1, 'PIANO3':2,
    'HONKY-TONKPIANO':3, 'RHODESPIANO':4, 'EPIANO':5,
    'HARPSICHORD':6, 'CLAVINET':7, 'CELESTA':8,
    'GLOCKENSPIEL':9, 'MUSICBOX':10, 'VIBRAPHONE':11,
    'MARIMBA':12, 'XYLOPHONE':13, 'TUBULARBELLS':14,
    'SANTUR':15, 'ORGAN1':16, 'ORGAN2':17,
    'ORGAN3':18, 'CHURCHORGAN':19, 'REEDORGAN':20,
    'ACCORDION':21, 'HARMONICA':22, 'BANDONEON':23,
    'NYLONGUITAR':24, 'STEELGUITAR':25, 'JAZZGUITAR':26,
    'CLEANGUITAR':27, 'MUTEDGUITAR':28, 'OVERDRIVEGUITAR':29,
    'DISTORTONGUITAR':30, 'GUITARHARMONICS':31, 'ACOUSTICBASS':32,
    'FINGEREDBASS':33, 'PICKEDBASS':34, 'FRETLESSBASS':35,
    'SLAPBASS1':36, 'SLAPBASS2':37, 'SYNTHBASS1':38,
    'SYNTHBASS2':39, 'VIOLIN':40, 'VIOLA':41,
    'CELLO':42, 'CONTRABASS':43, 'TREMOLOSTRINGS':44,
    'PIZZICATOSTRING':45, 'ORCHESTRALHARP':46, 'TIMPANI':47,
    'STRINGS':48, 'SLOWSTRINGS':49, 'SYNTHSTRINGS1':50,
    'SYNTHSTRINGS2':51, 'CHOIRAAHS':52, 'VOICEOOHS':53,
    'SYNTHVOX':54, 'ORCHESTRAHIT':55, 'TRUMPET':56,
    'TROMBONE':57, 'TUBA':58, 'MUTEDTRUMPET':59,
    'FRENCHHORN':60, 'BRASSSECTION':61, 'SYNTHBRASS1':62,
    'SYNTHBRASS2':63, 'SOPRANOSAX':64, 'ALTOSAX':65,
    'TENORSAX':66, 'BARITONESAX':67, 'OBOE':68,
    'ENGLISHHORN':69, 'BASSOON':70, 'CLARINET':71,
    'PICCOLO':72, 'FLUTE':73, 'RECORDER':74,
    'PANFLUTE':75, 'BOTTLEBLOW':76, 'SHAKUHACHI':77,
    'WHISTLE':78, 'OCARINA':79, 'SQUAREWAVE':80,
    'SAWWAVE':81, 'SYNCALLIOPE':82, 'CHIFFERLEAD':83,
    'CHARANG':84, 'SOLOVOICE':85, '5THSAWWAVE':86,
    'BASS&LEAD':87, 'FANTASIA':88, 'WARMPAD':89,
    'POLYSYNTH':90, 'SPACEVOICE':91, 'BOWEDGLASS':92,
    'METALPAD':93, 'HALOPAD':94, 'SWEEPPAD':95,
    'ICERAIN':96, 'SOUNDTRACK':97, 'CRYSTAL':98,
    'ATMOSPHERE':99, 'BRIGHTNESS':100, 'GOBLINS':101,
    'ECHODROPS':102, 'STARTHEME':103, 'SITAR':104,
    'BANJO':105, 'SHAMISEN':106, 'KOTO':107,
    'KALIMBA':108, 'BAGPIPE':109, 'FIDDLE':110,
    'SHANAI':111, 'TINKLEBELL':112, 'AGOGOBELLS':113,
    'STEELDRUMS':114, 'WOODBLOCK':115, 'TAIKODRUM':116,
    'MELODICTOM1':117, 'SYNTHDRUM':118, 'REVERSECYMBAL':119,
    'GUITARFRETNOISE':120, 'BREATHNOISE':121, 'SEASHORE':122,
    'BIRDTWEET':123, 'TELEPHONERING':124, 'HELICOPTERBLADE':125,
    'APPLAUSE/NOISE':126, 'GUNSHOT':127 }


# Controller names. Tables are borrowed from:
#     http://www.midi.org/about-midi/table3.shtml

#      0-31 Double Precise Controllers    MSB (14-bits, 16,384 values)
#      32-63  Double Precise Controllers  LSB (14-bits, 16,384 values)
#      64-119 Single Precise Controllers  (7-bits, 128 values)
#      120-127 Channel Mode Messages

ctrlNames = {
    0:'Bank', 1:'Modulation', 2:'Breath',
    3:'Ctrl3', 4:'Foot', 5:'Portamento',
    6:'Data', 7:'Volume', 8:'Balance',
    9:'Ctrl9', 10:'Pan', 11:'Expression',
    12:'Effect1', 13:'Effect2', 14:'Ctrl14',
    15:'Ctrl15', 16:'General1', 17:'General2',
    18:'General3', 19:'General4', 20:'Ctrl20',
    21:'Ctrl21', 22:'Ctrl22', 23:'Ctrl23',
    24:'Ctrl24', 25:'Ctrl25', 26:'Ctrl26',
    27:'Ctrl27', 28:'Ctrl28', 29:'Ctrl29',
    30:'Ctrl30', 31:'Ctrl31', 32:'BankLSB',
    33:'ModulationLSB', 34:'BreathLSB', 35:'Ctrl35',
    36:'FootLSB', 37:'PortamentoLSB', 38:'DataLSB',
    39:'VolumeLSB', 40:'BalanceLSB', 41:'Ctrl41',
    42:'PanLSB', 43:'ExpressionLSB', 44:'Effect1LSB',
    45:'Effect2LSB', 46:'Ctrl46', 47:'Ctrl47',
    48:'General1LSB', 49:'General2LSB', 50:'General3LSB',
    51:'General4LSB', 52:'Ctrl52', 53:'Ctrl53',
    54:'Ctrl54', 55:'Ctrl55', 56:'Ctrl56',
    57:'Ctrl57', 58:'Ctrl58', 59:'Ctrl59',
    60:'Ctrl60', 61:'Ctrl61', 62:'Ctrl62',
    63:'Ctrl63', 64:'Sustain', 65:'Portamento',
    66:'Sostenuto', 67:'SoftPedal', 68:'Legato',
    69:'Hold2', 70:'Variation', 71:'Resonance',
    72:'ReleaseTime', 73:'AttackTime', 74:'Brightness',
    75:'DecayTime', 76:'VibratoRate', 77:'VibratoDepth',
    78:'VibratoDelay', 79:'Ctrl79', 80:'General5',
    81:'General6', 82:'General7', 83:'General8',
    84:'PortamentoCtrl', 85:'Ctrl85', 86:'Ctrl86',
    87:'Ctrl87', 88:'Ctrl88', 89:'Ctrl89',
    90:'Ctrl90', 91:'Reverb', 92:'Tremolo',
    93:'Chorus', 94:'Detune', 95:'Phaser',
    96:'DataInc', 97:'DataDec', 98:'NonRegLSB',
    99:'NonRegMSB', 100:'RegParLSB', 101:'RegParMSB',
    102:'Ctrl102', 103:'Ctrl103', 104:'Ctrl104',
    105:'Ctrl105', 106:'Ctrl106', 107:'Ctrl107',
    108:'Ctrl108', 109:'Ctrl109', 110:'Ctrl110',
    111:'Ctrl111', 112:'Ctrl112', 113:'Ctrl113',
    114:'Ctrl114', 115:'Ctrl115', 116:'Ctrl116',
    117:'Ctrl117', 118:'Ctrl118', 119:'Ctrl119',
    120:'AllSoundsOff', 121:'ResetAll', 122:'LocalCtrl',
    123:'AllNotesOff', 124:'OmniOff', 125:'OmniOn',
    126:'PolyOff', 127:'PolyOn' }

ctrlInx = {
    'BANK':0, 'MODULATION':1, 'BREATH':2,
    'CTRL3':3, 'FOOT':4, 'PORTAMENTO':5,
    'DATA':6, 'VOLUME':7, 'BALANCE':8,
    'CTRL9':9, 'PAN':10, 'EXPRESSION':11,
    'EFFECT1':12, 'EFFECT2':13, 'CTRL14':14,
    'CTRL15':15, 'GENERAL1':16, 'GENERAL2':17,
    'GENERAL3':18, 'GENERAL4':19, 'CTRL20':20,
    'CTRL21':21, 'CTRL22':22, 'CTRL23':23,
    'CTRL24':24, 'CTRL25':25, 'CTRL26':26,
    'CTRL27':27, 'CTRL28':28, 'CTRL29':29,
    'CTRL30':30, 'CTRL31':31, 'BANKLSB':32,
    'MODULATIONLSB':33, 'BREATHLSB':34, 'CTRL35':35,
    'FOOTLSB':36, 'PORTAMENTOLSB':37, 'DATALSB':38,
    'VOLUMELSB':39, 'BALANCELSB':40, 'CTRL41':41,
    'PANLSB':42, 'EXPRESSIONLSB':43, 'EFFECT1LSB':44,
    'EFFECT2LSB':45, 'CTRL46':46, 'CTRL47':47,
    'GENERAL1LSB':48, 'GENERAL2LSB':49, 'GENERAL3LSB':50,
    'GENERAL4LSB':51, 'CTRL52':52, 'CTRL53':53,
    'CTRL54':54, 'CTRL55':55, 'CTRL56':56,
    'CTRL57':57, 'CTRL58':58, 'CTRL59':59,
    'CTRL60':60, 'CTRL61':61, 'CTRL62':62,
    'CTRL63':63, 'SUSTAIN':64, 'PORTAMENTO':65,
    'SOSTENUTO':66, 'SOFTPEDAL':67, 'LEGATO':68,
    'HOLD2':69, 'VARIATION':70, 'RESONANCE':71,
    'RELEASETIME':72, 'ATTACKTIME':73, 'BRIGHTNESS':74,
    'DECAYTIME':75, 'VIBRATORATE':76, 'VIBRATODEPTH':77,
    'VIBRATODELAY':78, 'CTRL79':79, 'GENERAL5':80,
    'GENERAL6':81, 'GENERAL7':82, 'GENERAL8':83,
    'PORTAMENTOCTRL':84, 'CTRL85':85, 'CTRL86':86,
    'CTRL87':87, 'CTRL88':88, 'CTRL89':89,
    'CTRL90':90, 'REVERB':91, 'TREMOLO':92,
    'CHORUS':93, 'DETUNE':94, 'PHASER':95,
    'DATAINC':96, 'DATADEC':97, 'NONREGLSB':98,
    'NONREGMSB':99, 'REGPARLSB':100, 'REGPARMSB':101,
    'CTRL102':102, 'CTRL103':103, 'CTRL104':104,
    'CTRL105':105, 'CTRL106':106, 'CTRL107':107,
    'CTRL108':108, 'CTRL109':109, 'CTRL110':110,
    'CTRL111':111, 'CTRL112':112, 'CTRL113':113,
    'CTRL114':114, 'CTRL115':115, 'CTRL116':116,
    'CTRL117':117, 'CTRL118':118, 'CTRL119':119,
    'ALLSOUNDSOFF':120, 'RESETALL':121, 'LOCALCTRL':122,
    'ALLNOTESOFF':123, 'OMNIOFF':124, 'OMNION':125,
    'POLYOFF':126, 'POLYON':127 }

