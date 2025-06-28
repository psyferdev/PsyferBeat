import curses
import time
import threading

class TUISequencer:
    def __init__(self, sequencer):
        self.seq = sequencer
        self.cursor_track = 0
        self.cursor_step = 0
        self.playing = False
        self.play_thread = None
        self.edit_mode = None
        self.input_buffer = ""

    def draw(self, stdscr):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        title = "Psyferbeat TUI - SPACE=toggle, Arrows=move, p=play/stop, n=note, v=vel, b=var, s=save, l=load, q=quit"
        stdscr.addstr(0, 0, title[:w])
        step_header = "     " + " ".join([f"{i+1:02}" for i in range(self.seq.steps)])
        stdscr.addstr(2, 0, step_header[:w])
        for i, track in enumerate(self.seq.pattern):
            line = []
            for j, step in enumerate(track):
                char = "X" if step["on"] else "."
                attr = curses.A_NORMAL
                if i == self.cursor_track and j == self.cursor_step:
                    attr = curses.A_REVERSE
                if self.playing and hasattr(self, 'play_cursor') and j == self.play_cursor:
                    attr = curses.color_pair(1) | curses.A_BOLD
                line.append((f" {char} ", attr))
            track_name = self.seq.track_names[i][:6]
            stdscr.addstr(3 + i, 0, f"{track_name:<6}: ")
            for idx, (txt, attr) in enumerate(line):
                stdscr.addstr(3 + i, 8 + idx * 3, txt, attr)
        if self.edit_mode:
            stdscr.addstr(h-2, 0, f"Editing {self.edit_mode}. Type value and press Enter: {self.input_buffer}")
        elif self.playing:
            stdscr.addstr(h-2, 0, "Playing... Press 'p' to stop")
        else:
            stdscr.addstr(h-2, 0, "Stopped. Press 'p' to play")
        stdscr.refresh()

    def playback_loop(self):
        step_duration = self.seq.get_step_duration()
        self.play_cursor = 0
        while self.playing:
            for step_idx in range(self.seq.steps):
                if not self.playing:
                    break
                self.play_cursor = step_idx
                self.draw(self.stdscr)
                for track_idx, track in enumerate(self.seq.pattern):
                    step = track[step_idx]
                    if step["on"]:
                        if hasattr(self.seq, "play_step_callback"):
                            self.seq.play_step_callback(track_idx, step)
                time.sleep(step_duration)
        self.play_cursor = None
        self.draw(self.stdscr)

    def run(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        stdscr.nodelay(True)
        self.draw(stdscr)

        while True:
            c = stdscr.getch()
            if self.edit_mode:
                if c in (10, 13):
                    self.commit_edit()
                elif c == 27:
                    self.edit_mode = None
                    self.input_buffer = ""
                elif c in range(32, 127):
                    self.input_buffer += chr(c)
            else:
                if c == curses.ERR:
                    time.sleep(0.05)
                    continue
                if c == ord('q'):
                    self.playing = False
                    if self.play_thread:
                        self.play_thread.join()
                    break
                elif c == ord('p'):
                    if self.playing:
                        self.playing = False
                        if self.play_thread:
                            self.play_thread.join()
                    else:
                        self.playing = True
                        self.play_thread = threading.Thread(target=self.playback_loop)
                        self.play_thread.daemon = True
                        self.play_thread.start()
                elif c in [curses.KEY_RIGHT, ord('l')]:
                    self.cursor_step = (self.cursor_step + 1) % self.seq.steps
                elif c in [curses.KEY_LEFT, ord('h')]:
                    self.cursor_step = (self.cursor_step - 1) % self.seq.steps
                elif c in [curses.KEY_DOWN, ord('j')]:
                    self.cursor_track = (self.cursor_track + 1) % len(self.seq.pattern)
                elif c in [curses.KEY_UP, ord('k')]:
                    self.cursor_track = (self.cursor_track - 1) % len(self.seq.pattern)
                elif c == ord(' '):
                    self.seq.toggle_step(self.cursor_track, self.cursor_step)
                elif c == ord('n'):
                    self.edit_mode = "note"
                    self.input_buffer = ""
                elif c == ord('v'):
                    self.edit_mode = "velocity"
                    self.input_buffer = ""
                elif c == ord('b'):
                    self.edit_mode = "variation"
                    self.input_buffer = ""
                elif c == ord('s'):
                    self.seq.save_to_file("pattern.json")
                elif c == ord('l'):
                    loaded = self.seq.load_from_file("pattern.json")
                    self.seq.pattern = loaded.pattern
                    self.seq.steps = loaded.steps
                    self.seq.tempo = loaded.tempo
                    self.seq.resolution = loaded.resolution
            self.draw(stdscr)

    def commit_edit(self):
        try:
            val = self.input_buffer.strip()
            if self.edit_mode == "note":
                note = int(val)
                self.seq.set_note(self.cursor_track, self.cursor_step, note)
            elif self.edit_mode == "velocity":
                velocity = float(val)
                velocity = max(0.0, min(1.0, velocity))
                self.seq.pattern[self.cursor_track][self.cursor_step]["velocity"] = velocity
            elif self.edit_mode == "variation":
                variation = int(val)
                variation = max(0, min(4, variation))
                self.seq.pattern[self.cursor_track][self.cursor_step]["variation"] = variation
        except:
            pass
        self.edit_mode = None
        self.input_buffer = ""
