# =========================
# CUSTOM MIDI PARSER
# MIDI TO PSYCH
# Version 0.0.6
# =========================

import struct


# =========================
# READ VARIABLE LENGTH
# =========================

def read_variable_length(data, index):

    value = 0

    while True:

        byte = data[index]
        index += 1

        value = (value << 7) | (byte & 0x7F)

        if not (byte & 0x80):
            break

    return value, index



# =========================
# LOAD MIDI
# =========================

def read_midi(path):

    with open(path, "rb") as file:
        data = file.read()


    if data[0:4] != b"MThd":
        raise Exception("Not a MIDI file")


    header_size = struct.unpack(
        ">I",
        data[4:8]
    )[0]


    midi_format, track_count, division = struct.unpack(
        ">HHH",
        data[8:14]
    )


    return {
        "data": data,
        "format": midi_format,
        "tracks": track_count,
        "ticks": division,
        "header_end": 8 + header_size
    }



# =========================
# DISPLAY MIDI INFO
# =========================

def scan_midi(path):

    midi = read_midi(path)

    print("--------------------------")
    print("MIDI INFORMATION")
    print("--------------------------")
    print("Format:", midi["format"])
    print("Tracks:", midi["tracks"])
    print("Ticks Per Quarter:", midi["ticks"])
    print("--------------------------")

    return midi



# =========================
# READ TRACKS
# =========================

def read_tracks(midi):

    data = midi["data"]

    index = midi["header_end"]

    tracks = []


    while index < len(data):

        if data[index:index+4] != b"MTrk":
            break


        size = struct.unpack(
            ">I",
            data[index+4:index+8]
        )[0]


        tracks.append(
            data[index+8:index+8+size]
        )


        index += 8 + size


    return tracks



# =========================
# TEMPO MAP
# =========================

def get_tempos(path):

    midi = read_midi(path)

    tracks = read_tracks(midi)


    tempos = [
        {
            "tick": 0,
            "tempo": 500000
        }
    ]


    for track in tracks:

        index = 0
        tick = 0


        while index < len(track):

            delta, index = read_variable_length(
                track,
                index
            )

            tick += delta


            if index >= len(track):
                break


            if track[index] == 0xFF:

                index += 1


                meta = track[index]
                index += 1


                length, index = read_variable_length(
                    track,
                    index
                )


                if meta == 0x51 and length == 3:

                    tempos.append(
                        {
                            "tick": tick,
                            "tempo": int.from_bytes(
                                track[index:index+3],
                                "big"
                            )
                        }
                    )


                index += length


            else:

                status = track[index]


                if status >= 0x80:
                    index += 1


                index += 1



    tempos.sort(
        key=lambda x:x["tick"]
    )


    return tempos



# =========================
# TICKS TO MS
# =========================

def tick_to_ms(
    tick,
    ticks_per_quarter,
    tempos
):

    current_tempo = tempos[0]["tempo"]

    last_tick = 0

    total = 0


    for tempo in tempos[1:]:

        if tick <= tempo["tick"]:
            break


        distance = tempo["tick"] - last_tick


        total += (
            distance *
            current_tempo /
            ticks_per_quarter /
            1000
        )


        last_tick = tempo["tick"]

        current_tempo = tempo["tempo"]



    distance = tick - last_tick


    total += (
        distance *
        current_tempo /
        ticks_per_quarter /
        1000
    )


    return int(total)



# =========================
# PARSE NOTES
# =========================

def parse_notes(path):

    midi = read_midi(path)

    tracks = read_tracks(midi)

    tempos = get_tempos(path)


    notes = []


    for track_id, track in enumerate(tracks):

        index = 0
        tick = 0

        running = None

        active_notes = {}



        while index < len(track):

            delta, index = read_variable_length(
                track,
                index
            )

            tick += delta


            if index >= len(track):
                break



            status = track[index]


            if status < 0x80:

                status = running

            else:

                index += 1

                running = status



            command = status & 0xF0

            channel = status & 0x0F



            # Ignore MIDI drums

            if channel == 9:

                if command in (0x80,0x90):
                    index += 2

                continue



            # NOTE ON

            if command == 0x90:

                pitch = track[index]

                velocity = track[index+1]

                index += 2



                if velocity > 0:

                    active_notes[pitch] = tick



                else:

                    if pitch in active_notes:

                        start = active_notes[pitch]


                        notes.append(
                            {
                                "pitch": pitch,
                                "channel": channel,
                                "track": track_id,
                                "start": tick_to_ms(
                                    start,
                                    midi["ticks"],
                                    tempos
                                ),
                                "end": tick_to_ms(
                                    tick,
                                    midi["ticks"],
                                    tempos
                                )
                            }
                        )


                        del active_notes[pitch]



            # NOTE OFF

            elif command == 0x80:

                pitch = track[index]

                index += 2


                if pitch in active_notes:

                    start = active_notes[pitch]


                    notes.append(
                        {
                            "pitch": pitch,
                            "channel": channel,
                            "track": track_id,
                            "start": tick_to_ms(
                                start,
                                midi["ticks"],
                                tempos
                            ),
                            "end": tick_to_ms(
                                tick,
                                midi["ticks"],
                                tempos
                            )
                        }
                    )


                    del active_notes[pitch]



            elif command in (0xC0,0xD0):

                index += 1


            else:

                index += 2



    # Sort notes

    notes.sort(
        key=lambda n:n["start"]
    )


    # Remove exact duplicates

    clean = []

    seen = set()


    for note in notes:

        key = (
            note["pitch"],
            note["start"],
            note["end"]
        )


        if key not in seen:

            clean.append(note)

            seen.add(key)


    return clean, midi["ticks"]
