from pydub import AudioSegment
from pydub.playback import play

alert_sound = AudioSegment.from_wav('/Users/pluro/Desktop/cash-register-purchase-87313.wav')  # notification sound
play(alert_sound)

