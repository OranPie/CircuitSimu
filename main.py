#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circuit Simulator Launcher
Choose between TUI (Terminal) or GUI (Tkinter) interface

Usage:
    python main.py          # Launch GUI by default
    python main.py --tui    # Launch Terminal UI
    python main.py --gui    # Launch Graphical UI
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Circuit Simulator - Educational DC Circuit Analysis")
    parser.add_argument("--tui", action="store_true", help="Launch Terminal User Interface (curses)")
    parser.add_argument("--gui", action="store_true", help="Launch Graphical User Interface (tkinter)")
    
    args = parser.parse_args()
    
    if args.tui:
        print("Launching Terminal UI (TUI)...")
        import curses
        from tui import main_tui
        curses.wrapper(main_tui)
    elif args.gui or not args.tui:
        print("Launching Graphical UI (GUI)...")
        from gui import main_gui
        main_gui()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
