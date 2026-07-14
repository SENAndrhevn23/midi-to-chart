#!/usr/bin/env python3

# =========================
# MIDI TO PSYCH CONVERTER
# Version 0.0.4
# =========================

import os
import time

from midi import scan_midi, parse_notes
from chart import create_chart, save_chart

from config import (
    VERSION,
    START_CUTOFF_MS,
    REBASE_TO_ZERO
)


def print_header():

    print("=" * 37)
    print("      MIDI TO PSYCH CONVERTER")
    print("             v" + VERSION)
    print("=" * 37)
    print()



def midi_to_lane(pitch):

    """
    MIDI pitch to FNF lane

    0 = Left
    1 = Down
    2 = Up
    3 = Right
    """

    MIN_NOTE = 36
    MAX_NOTE = 84


    if pitch < MIN_NOTE:
        pitch = MIN_NOTE


    if pitch > MAX_NOTE:
        pitch = MAX_NOTE


    percent = (
        pitch - MIN_NOTE
    ) / (
        MAX_NOTE - MIN_NOTE
    )


    lane = int(
        percent * 4
    )


    if lane > 3:
        lane = 3


    return lane



def convert_notes(raw_notes, side):

    notes = []


    if len(raw_notes) == 0:
        return notes



    first_time = raw_notes[0]["start"]



    for midi_note in raw_notes:


        start = midi_note["start"]

        end = midi_note["end"]


        pitch = midi_note.get(
            "pitch",
            60
        )



        if start < START_CUTOFF_MS:
            continue



        if REBASE_TO_ZERO:

            start -= first_time
            end -= first_time



        sustain = end - start


        lane = midi_to_lane(
            pitch
        )



        # Player
        if side == "P":

            final_lane = lane



        # Opponent
        elif side == "O":

            final_lane = lane + 4



        # Both
        elif side == "B":

            final_lane = lane



        else:

            final_lane = lane



        notes.append(
            [
                start,
                final_lane,
                sustain
            ]
        )



    return notes



def convert_midi():

    print()


    midi_path = input(
        "Enter MIDI Path: "
    )


    song_name = input(
        "Enter Song Name: "
    )


    bpm = int(
        input(
            "Enter BPM: "
        )
    )


    speed = float(
        input(
            "Enter Scroll Speed: "
        )
    )


    minify = input(
        "Wanna Minify It Y/N: "
    ).upper()


    side = input(
        "Which Side? Opponent? Player? Both O/P/B: "
    ).upper()



    if not os.path.exists(midi_path):

        print(
            "ERROR: MIDI file not found!"
        )

        return



    print()

    print(
        "Converting..."
    )


    try:

        scan_midi(
            midi_path
        )


        print()

        print(
            "Reading MIDI Notes..."
        )


        raw_notes, ticks = parse_notes(
            midi_path
        )


    except Exception as error:

        print(
            "MIDI ERROR:",
            error
        )

        return



    print(
        "MIDI Notes Found:",
        len(raw_notes)
    )


    print()

    print(
        "Mapping MIDI Notes..."
    )


    notes = convert_notes(
        raw_notes,
        side
    )


    print(
        "Psych Notes Created:",
        len(notes)
    )


    print()

    print(
        "Creating Chart..."
    )


    chart = create_chart(
        song_name,
        bpm,
        speed,
        notes
    )



    if minify == "Y":

        print(
            "Compressing..."
        )

        time.sleep(
            0.5
        )



    output = save_chart(
        song_name,
        chart,
        minify
    )


    print()

    print(
        "Done."
    )


    print(
        "Saved:",
        output
    )


    print()



def main():

    while True:

        print_header()


        print(
            "1: MIDI to Psych"
        )


        print(
            "0: Exit"
        )


        print()


        choice = input(
            "Andre: "
        )


        if choice == "1":

            convert_midi()


        elif choice == "0":

            print(
                "Goodbye!"
            )

            break


        else:

            print(
                "Invalid option!"
            )

            print()



if __name__ == "__main__":

    main()
