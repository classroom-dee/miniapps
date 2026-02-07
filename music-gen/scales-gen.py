from music21 import stream, scale, metadata, pitch, interval

# from music21 import environment
# env = environment.UserSettings()
# env['musescoreDirectPNGPath'] = '/path/to/mscore'

from helpers import (
    RH_LOW,
    RH_HIGH,
    LH_LOW,
    LH_HIGH,
    arp_up_down,
    build_hand_part,
    scale_pitches,
    make_key_signature,
    get_output_path,
)

# sig    0   #1   #2   #3   #4   #5  #6/b6(F#) b5    b4    b3    b2    b1
KEYS = ["C", "G", "D", "A", "E", "B", "Gb", "Db", "Ab", "Eb", "Bb", "F"]

# fmt: off
MINOR_MODES = {
    "Dorian b2": (["P1", "m2", "m3", "P4", "P5", "M6", "m7"], "DorianFlatSecondScale"),
    "Lydian Augmented": (["P1", "M2", "M3", "A4", "A5", "M6", "M7"], "LydianAugmentedScale"),
    "Lydian Dominant": (["P1", "M2", "M3", "A4", "P5", "M6", "m7"], "LydianDominantScale"),
    "Mixolydian b6": (["P1", "M2", "M3", "P4", "P5", "m6", "m7"], "MixolydianFlatSixScale"),
    "Locrian #2": (["P1", "M2", "m3", "P4", "d5", "m6", "m7"], "LocrianSharpSecondScale"),
    "Altered": (["P1", "m2", "m3", "d4", "d5", "m6", "m7"], "SuperLocrianScale"),
}
# fmt: on


def _scale_factory(intervals: list[str], name=None, base=scale.ConcreteScale):
    """Generates a ConcretScale class based on the interval input"""
    name = name or "CustomScale"

    def __init__(self, tonic):
        # build relative to tonic
        p = pitch.Pitch(tonic)
        # raw int transpose will result in enharmonic notation error! (like F# in C Loc#II instead of Gb)
        pitches = [interval.Interval(i).transposePitch(p) for i in intervals]
        base.__init__(self, pitches=pitches)

    return type(name, (base,), {"__init__": __init__})


# Contemporary-centered
SCALES = {
    "Ionian": scale.MajorScale,
    "Dorian": scale.DorianScale,
    "Phrygian": scale.PhrygianScale,
    "Lydian": scale.LydianScale,
    "Mixolydian": scale.MixolydianScale,
    "Aeolian": scale.MinorScale,
    "Locrian": scale.LocrianScale,
    # Minor-focused / jazz
    "Harmonic Minor": scale.HarmonicMinorScale,
    "Melodic Minor": scale.MelodicMinorScale,
    "Dorian b2": _scale_factory(*MINOR_MODES["Dorian b2"]),
    "Lydian Augmented": _scale_factory(*MINOR_MODES["Lydian Augmented"]),
    "Lydian Dominant": _scale_factory(*MINOR_MODES["Lydian Dominant"]),
    "Mixolydian b6": _scale_factory(*MINOR_MODES["Mixolydian b6"]),
    "Locrian #2": _scale_factory(*MINOR_MODES["Locrian #2"]),
    "Altered": _scale_factory(*MINOR_MODES["Altered"]),
}


def generate_scale_exercise(tonic, scale_name, scale_cls):
    score = stream.Score()
    score.insert(0, metadata.Metadata())
    score.metadata.title = f"{tonic} {scale_name}"
    score.metadata.composer = "Dee H. Seon"
    score.insert(0, make_key_signature(tonic))

    sc = scale_cls(tonic)

    # Right hand
    rh_pitches = scale_pitches(sc, tonic, RH_LOW, RH_HIGH)
    rh_line = arp_up_down(rh_pitches)
    rh = build_hand_part(rh_line)
    rh.id = "Right Hand"

    # Left hand
    lh_pitches = scale_pitches(sc, tonic, LH_LOW, LH_HIGH)
    lh_line = arp_up_down(lh_pitches)
    lh = build_hand_part(lh_line)
    lh.id = "Left Hand"

    score.insert(0, rh)
    score.insert(0, lh)
    return score


def main():
    for tonic in KEYS:
        for name, cls in SCALES.items():
            score = generate_scale_exercise(tonic, name, cls)

            safe_name = (
                name.replace(" ", "_").replace("#", "sharp").replace("b", "flat")
            )
            filename = f"{tonic}_{safe_name}"

            score.write("musicxml", get_output_path("out", f"{filename}.musicxml"))
            score.write("midi", get_output_path("out", f"{filename}.mid"))


if __name__ == "__main__":
    main()
