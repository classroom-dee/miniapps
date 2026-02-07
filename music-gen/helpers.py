import os
from pathlib import Path
from music21 import note, stream, key, interval

# Piano ranges
RH_LOW = "C4"
RH_HIGH = "C6"
LH_LOW = "C2"
LH_HIGH = "C4"


def get_output_path(output_dir, filename):
    """Makes the output directory if not exist and return the full path for the input filename"""
    path = os.path.join(Path(__file__).resolve().parent, output_dir)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)


def clamp_pitches(pitches, low, high):
    """Ensure pitches fit inside a playable range."""
    out = []
    for p in pitches:
        while p < note.Note(low).pitch:
            p = p.transpose(interval.Octave())
        while p > note.Note(high).pitch:
            p = p.transpose(-interval.Octave())
        out.append(p)
    return out


def arp_up_down(pitches):
    """Return pitches up then down (Hanon-style)."""
    return pitches + list(reversed(pitches[:-1]))


def build_hand_part(pitches, ql=0.5):
    """Create a music21 Part from pitch list."""
    part = stream.Part()
    for p in pitches:
        part.append(note.Note(p, quarterLength=ql))
    return part


def scale_pitches(scale_obj, low, high):
    """Generate scale pitches clamped to range."""
    raw = scale_obj.getPitches(low, high)
    return clamp_pitches(raw, low, high)


def make_key_signature(tonic):
    return key.Key(tonic)
