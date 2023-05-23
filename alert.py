from pydub import AudioSegment
from pydub.playback import play

sound = AudioSegment.from_wav('/Users/pluro/Desktop/beep-01a.wav')
play(sound)