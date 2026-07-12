#!/usr/bin/env python3

def print_header():
    print("=" * 37)
    print("      MIDI TO PSYCH CONVERTER")
    print("             v0.0.1")
    print("=" * 37)
    print()

def main():
    while True:
        print_header()
        print("1: MIDI to Psych")
        print("0: Exit")
        print()

        choice = input("Andre: ").strip()

        if choice == "1":
            midi_path = input("Enter MIDI Path: ")
            song_name = input("Enter Song Name: ")
            bpm = input("Enter BPM: ")
            speed = input("Enter Scroll Speed: ")
            minify = input("Wanna Minify It Y/N: ").upper()
            side = input("Which Side? Opponent? Player? Both O/P/B: ").upper()

            print("Converting...")

            if minify == "Y":
                print("Compressing...")

            print("Done.")
            break

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid option.\n")

if __name__ == "__main__":
    main()
