#!/usr/bin/env python3
import mido
import json
import os
import bisect
import time
from collections import defaultdict

# =========================
# CONFIG
# =========================
SECTION_BEATS = 4
START_CUTOFF_MS = 250
REBASE_TO_ZERO = True

# =========================
# TEMPO UTILS
# =========================
def build_tempo_lookup(mid):
    merged = mido.merge_tracks(mid.tracks)
    tpq = mid.ticks_per_beat
    tempo_events = [(0, 500000)]  # default 120 BPM

    abs_tick = 0
    for msg in merged:
        abs_tick += msg.time
        if msg.type == "set_tempo":
            if abs_tick == 0:
                tempo_events[0] = (0, msg.tempo)
            else:
                tempo_events.append((abs_tick, msg.tempo))

    tempo_events.sort(key=lambda x: x[0])

    ticks, ms, tempos = [], [], []
    cur_ms = 0.0
    prev_tick, prev_tempo = tempo_events[0]
    ticks.append(prev_tick)
    ms.append(cur_ms)
    tempos.append(prev_tempo)

    for tick, tempo in tempo_events[1:]:
        cur_ms += (tick - prev_tick) * prev_tempo / tpq / 1000.0
        ticks.append(tick)
        ms.append(cur_ms)
        tempos.append(tempo)
        prev_tick = tick
        prev_tempo = tempo

    return ticks, ms, tempos, tpq

def tick_to_ms(tick, ticks, ms, tempos, tpq):
    i = bisect.bisect_right(ticks, tick) - 1
    if i < 0:
        i = 0
    return ms[i] + (tick - ticks[i]) * tempos[i] / tpq / 1000.0

# =========================
# NOTE EXTRACTION
# =========================
def extract_notes(mid):
    merged = mido.merge_tracks(mid.tracks)
    abs_tick = 0
    active = defaultdict(list)
    notes = []

    for msg in merged:
        abs_tick += msg.time
        is_note_on = msg.type == "note_on" and msg.velocity > 0
        is_note_off = msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0)

        if is_note_on:
            active[(msg.channel, msg.note)].append((abs_tick, msg.velocity))
        elif is_note_off:
            key = (msg.channel, msg.note)
            if active[key]:
                start_tick, velocity = active[key].pop()
                if abs_tick > start_tick:
                    notes.append({
                        "note": msg.note,
                        "channel": msg.channel,
                        "velocity": velocity,
                        "start_tick": start_tick,
                        "end_tick": abs_tick
                    })
    notes.sort(key=lambda n: (n["start_tick"], n["note"], n["channel"]))
    return notes

def build_pitch_lane_map(notes):
    unique_pitches = sorted({n["note"] for n in notes})
    if not unique_pitches: return {}
    if len(unique_pitches) == 1: return {unique_pitches[0]: 2}

    lane_map = {}
    denom = len(unique_pitches) - 1
    for i, pitch in enumerate(unique_pitches):
        lane = int(round(i * 3 / denom))
        lane_map[pitch] = max(0, min(3, lane))
    return lane_map

def choose_lane(target_lane, occupied):
    if target_lane not in occupied: return target_lane
    for dist in range(1, 4):
        left, right = target_lane - dist, target_lane + dist
        if left >= 0 and left not in occupied: return left
        if right <= 3 and right not in occupied: return right
    return target_lane

# =========================
# PROCESSING ENGINE
# =========================
def process_midi_file(path, is_player, accuracy_mode):
    if not os.path.exists(path):
        return []
    
    mid = mido.MidiFile(path, clip=True)
    ticks, ms, tempos, tpq = build_tempo_lookup(mid)
    raw_notes = extract_notes(mid)
    lane_map = build_pitch_lane_map(raw_notes)
    
    processed = []
    for n in raw_notes:
        start_ms = tick_to_ms(n["start_tick"], ticks, ms, tempos, tpq)
        end_ms = tick_to_ms(n["end_tick"], ticks, ms, tempos, tpq)
        
        if start_ms < START_CUTOFF_MS:
            continue
            
        processed.append({
            **n,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "is_player": is_player
        })
    return processed, lane_map

def save_chart(out_file, name, section_map, bpm, speed, minify):
    max_section = max(section_map.keys()) if section_map else 0
    sections = []

    for idx in range(max_section + 1):
        # Determine who maps the section predominantly, or default to True
        notes_in_sec = section_map.get(idx, [])
        must_hit = True
        if notes_in_sec:
            player_notes = sum(1 for n in notes_in_sec if n[1] < 4)
            opponent_notes = sum(1 for n in notes_in_sec if n[1] >= 4)
            must_hit = player_notes >= opponent_notes

        sections.append({
            "sectionNotes": notes_in_sec,
            "mustHitSection": must_hit,
            "bpm": bpm,
            "changeBPM": False,
            "altAnim": False,
            "gfSection": False,
            "typeOfSection": 0,
            "lengthInSteps": 16
        })

    chart = {
        "song": {
            "song": name,
            "notes": sections,
            "bpm": bpm,
            "needsVoices": True,
            "speed": speed,
            "player1": "bf",
            "player2": "dad",
            "gfVersion": "gf",
            "stage": "stage",
            "events": []
        }
    }

    print("Converting...")
    time.sleep(0.6)

    with open(out_file, "w", encoding="utf-8") as f:
        if minify == 'Y':
            print("Compressing...")
            time.sleep(0.4)
            json.dump(chart, f, separators=(',', ':'))
        else:
            json.dump(chart, f, indent=2)
            
    print("Done..")

# =========================
# MAIN MENU INTERFACE
# =========================
def main():
    print("1: Split Midi Only")
    print("2: MIdi To Psych Chart")
    print("3: New Midi To Psych Chart\n")
    
    choice = input("Andre: ").strip()
    print("")

    if choice == "1":
        path = input("Enter MIDI Path: ").strip()
        splits = int(input("How many splits: ").strip())
        # (Split logic from original script runs here)
        
    elif choice == "2":
        # (Legacy single chart mode layout)
        pass

    elif choice == "3":
        p1_path = input("Enter Player midi aka p1.mid path: ").strip()
        p2_path = input("Enter Opponent midi aka p2.mid path: ").strip()
        bpm = float(input("Enter BPM: ").strip())
        scroll_speed = float(input("Enter Scroll Speed: ").strip())
        minify = input("Wanna Minify Json Y/N: ").strip().upper()
        accuracy_mode = input("Want The Song To Be Accurate Or Normal A/N: ").strip().upper()

        all_notes = []
        
        # Load data fields
        p1_notes, p1_lanes = process_midi_file(p1_path, True, accuracy_mode)
        p2_notes, p2_lanes = process_midi_file(p2_path, False, accuracy_mode)
        all_notes.extend(p1_notes)
        all_notes.extend(p2_notes)

        if not all_notes:
            print("❌ No notes parsed from either MIDI file.")
            return

        # Rebase timeline to absolute 0
        first_note_ms = min(n["start_ms"] for n in all_notes)
        if REBASE_TO_ZERO:
            for n in all_notes:
                n["start_ms"] -= first_note_ms
                n["end_ms"] -= first_note_ms

        # Group notes matching exact timeline points
        all_notes.sort(key=lambda n: (n["start_tick"], n["note"]))
        section_ms = (60000.0 / bpm) * SECTION_BEATS
        section_map = defaultdict(list)

        i = 0
        while i < len(all_notes):
            j = i
            start_tick = all_notes[i]["start_tick"]
            same_time = []
            while j < len(all_notes) and all_notes[j]["start_tick"] == start_tick:
                same_time.append(all_notes[j])
                j += 1

            occupied_player = set()
            occupied_opponent = set()
            same_time.sort(key=lambda n: n["note"])

            for n in same_time:
                if n["is_player"]:
                    target_lane = p1_lanes.get(n["note"], 2)
                    lane = choose_lane(target_lane, occupied_player)
                    occupied_player.add(lane)
                    # Psych engine format uses lane 0-3 for player if mustHitSection matches
                    final_lane = lane 
                else:
                    target_lane = p2_lanes.get(n["note"], 2)
                    lane = choose_lane(target_lane, occupied_opponent)
                    occupied_opponent.add(lane)
                    # Opponent lanes are shifted by 4 indices
                    final_lane = lane + 4

                # Timing calculation mapping
                if accuracy_mode == 'A':
                    strum_time = round(n["start_ms"], 4) # Retain decimals
                else:
                    strum_time = int(round(n["start_ms"])) # Clean integer conversion

                sustain = max(0, int(round(n["end_ms"] - n["start_ms"])))
                section_idx = int(n["start_ms"] // section_ms)
                section_map[section_idx].append([strum_time, final_lane, sustain])

            i = j

        out_name = os.path.splitext(os.path.basename(p1_path))[0] if p1_path else "custom_song"
        save_chart(f"{out_name}-chart.json", out_name, section_map, bpm, scroll_speed, minify)

if __name__ == "__main__":
    main()
