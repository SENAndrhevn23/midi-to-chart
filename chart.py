# =========================
# PSYCH ENGINE CHART WRITER
# Version 0.0.1
# =========================

import json
import os

from config import SECTION_BEATS


def create_section(notes, bpm):
    return {
        "gfSection": False,
        "altAnim": False,
        "typeOfSection": 0,

        "sectionNotes": notes,

        "bpm": bpm,
        "sectionBeats": SECTION_BEATS,

        "changeBPM": False,
        "mustHitSection": True,

        "crossFade": False
    }


def split_into_sections(notes, bpm):
    """
    For now every note goes into section 0.
    Later we will split based on beats.
    """

    sections = []

    sections.append(
        create_section(
            notes,
            bpm
        )
    )

    # Add an empty section like Psych charts usually have
    sections.append(
        create_section(
            [],
            bpm
        )
    )

    return sections


def create_chart(song_name, bpm, speed, notes):

    sections = split_into_sections(
        notes,
        bpm
    )

    chart = {
        "song": {

            "speed": speed,

            "stage": "stage",

            "player1": "bf",
            "player2": "dad",

            "events": [],

            "notes": sections,

            "splashSkin": "noteSplashes",

            "gfVersion": "gf",

            "bpm": bpm,

            "needsVoices": True,

            "arrowSkin": "",

            "song": song_name,

            "specialAudioName": ""

        }
    }

    return chart


def save_chart(filename, chart, minify):

    os.makedirs(
        "output",
        exist_ok=True
    )

    path = os.path.join(
        "output",
        filename + ".json"
    )


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        if minify == "Y":

            json.dump(
                chart,
                file,
                separators=(",", ":")
            )

        else:

            json.dump(
                chart,
                file,
                indent=4
            )


    return path