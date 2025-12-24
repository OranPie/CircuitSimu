#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circuit Simulator TUI (Terminal User Interface)
- Terminal rendering via curses
- TCP JSONL control server
"""

import curses
import json
import queue
import socket
import threading
import time
from typing import Dict, Optional, Tuple

from core import Circuit, Component, SolveResult, solve_circuit, comp_symbol, format_si, format_si_safe, bulb_resistance, Point, meter_ranges, meter_full_scale, meter_native_full_scale, CircuitHistory, goal_seek_parameter

HOST = "127.0.0.1"
PORT = 9999
SAVE_FILE = "circuit.json"

GRID_W = 64
GRID_H = 20

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def draw_line(canvas, a: Point, b: Point, ch_h="─", ch_v="│"):
    x1, y1 = a
    x2, y2 = b
    if x1 == x2:
        ylo, yhi = sorted([y1, y2])
        for y in range(ylo, yhi + 1):
            canvas[(x1, y)] = ch_v
    elif y1 == y2:
        xlo, xhi = sorted([x1, x2])
        for x in range(xlo, xhi + 1):
            canvas[(x, y1)] = ch_h
    else:
        xlo, xhi = sorted([x1, x2])
        for x in range(xlo, xhi + 1):
            canvas[(x, y1)] = ch_h
        ylo, yhi = sorted([y1, y2])
        for y in range(ylo, yhi + 1):
            canvas[(x2, y)] = ch_v

def _path_points(a: Point, b: Point):
    x1, y1 = a
    x2, y2 = b
    pts = []
    if x1 == x2:
        ylo, yhi = sorted([y1, y2])
        for y in range(ylo, yhi + 1):
            pts.append((x1, y))
        return pts
    if y1 == y2:
        xlo, xhi = sorted([x1, x2])
        for x in range(xlo, xhi + 1):
            pts.append((x, y1))
        return pts
    xlo, xhi = sorted([x1, x2])
    step = 1 if x2 >= x1 else -1
    x = x1
    while True:
        pts.append((x, y1))
        if x == x2:
            break
        x += step
    step2 = 1 if y2 >= y1 else -1
    y = y1
    while True:
        pts.append((x2, y))
        if y == y2:
            break
        y += step2
    return pts

def _junction_char(mask: int) -> str:
    # bits: 1=N 2=E 4=S 8=W
    table = {
        0: " ",
        1: "│",
        2: "─",
        4: "│",
        8: "─",
        1 | 4: "│",
        2 | 8: "─",
        1 | 2: "└",
        2 | 4: "┌",
        4 | 8: "┐",
        8 | 1: "┘",
        1 | 2 | 4: "├",
        2 | 4 | 8: "┬",
        4 | 8 | 1: "┤",
        8 | 1 | 2: "┴",
        1 | 2 | 4 | 8: "┼",
    }
    return table.get(mask, "┼")

class SocketServer(threading.Thread):
    def __init__(self, inbox: "queue.Queue[dict]"):
        super().__init__(daemon=True)
        self.inbox = inbox
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)
        srv.settimeout(0.5)
        while not self._stop.is_set():
            try:
                conn, _addr = srv.accept()
            except socket.timeout:
                continue
            conn.settimeout(0.5)
            buf = b""
            try:
                while not self._stop.is_set():
                    try:
                        data = conn.recv(4096)
                        if not data:
                            break
                        buf += data
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                obj = json.loads(line.decode("utf-8"))
                                self.inbox.put(obj)
                            except Exception:
                                pass
                    except socket.timeout:
                        continue
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
        try:
            srv.close()
        except Exception:
            pass

class TUIApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.cir = Circuit()
        self.result = SolveResult(ok=True)
        self.history = CircuitHistory()
        self.cursor = (4, 4)
        self.mode = 0
        self.place_type = "wire"
        self.wire_start: Optional[Point] = None
        self.show_details = False
        self.status = "就绪"
        self.inbox: "queue.Queue[dict]" = queue.Queue()
        self.server = SocketServer(self.inbox)
        self.server.start()

        self._colors_inited = False

    def init_colors(self):
        if self._colors_inited:
            return
        self._colors_inited = True
        try:
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_RED, -1)
        except Exception:
            pass

        sid = self.cir.add("socket", (8, 6), (8, 12), V=6.0, Iwarn=5.0)
        rid = self.cir.add("resistor", (8, 6), (20, 6), R=20.0)
        self.cir.add("wire", (20, 6), (20, 12))
        self.cir.add("wire", (20, 12), (8, 12))
        self.history.record(self.cir)
        self.solve()

    def stop(self):
        self.server.stop()

    def solve(self):
        self.result = solve_circuit(self.cir)
        if self.result.singular:
            self.status = "仿真失败：奇异矩阵（断路/冲突/理想短路）"
        else:
            self.status = "仿真完成" if self.result.ok else "仿真失败"

    def handle_socket_commands(self):
        changed = False
        while True:
            try:
                cmd = self.inbox.get_nowait()
            except queue.Empty:
                break
            try:
                c = cmd.get("cmd")
                if c == "add":
                    t = cmd["type"]
                    a = tuple(cmd["a"])
                    b = tuple(cmd["b"])
                    props = {k: v for k, v in cmd.items() if k not in ("cmd", "type", "a", "b")}
                    self.cir.add(t, a, b, **props)
                    changed = True
                elif c == "set":
                    cid = cmd["cid"]
                    if cid in self.cir.components:
                        self.cir.components[cid].props.update(cmd.get("props", {}))
                        changed = True
                elif c == "delete":
                    cid = cmd["cid"]
                    if cid in self.cir.components:
                        del self.cir.components[cid]
                        changed = True
                elif c == "solve":
                    changed = True
                elif c == "save":
                    self.save()
                elif c == "load":
                    self.load()
            except Exception:
                pass
        if changed:
            self.history.record(self.cir)
            self.solve()

    def save(self):
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cir.to_json(), f, ensure_ascii=False, indent=2)
        self.status = f"已保存到 {SAVE_FILE}"

    def load(self):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                obj = json.load(f)
            self.cir = Circuit.from_json(obj)
            self.history.clear()
            self.history.record(self.cir)
            self.solve()
            self.status = f"已加载 {SAVE_FILE}"
        except Exception as e:
            self.status = f"加载失败：{e}"

    def prompt_edit(self, comp: Component):
        fields = []
        t = comp.ctype
        if t == "socket":
            fields = [("V", "电压(V)", 5.0), ("Iwarn", "短路告警阈值(A)", 5.0)]
        elif t == "resistor":
            fields = [("R", "电阻(Ω)", 100.0)]
        elif t == "bulb":
            fields = [("Vr", "额定电压(V)", 6.0), ("Wr", "额定功率(W)", 3.0)]
        elif t == "rheostat":
            fields = [("R", "当前电阻(Ω)", 100.0)]
        elif t == "switch_spst":
            fields = [("state", "状态(1闭合/0断开)", 1)]
        elif t == "switch_spdt":
            fields = [("throw", "拨到(0->b / 1->c2)", 0), ("c_x", "c2.x", comp.b[0]), ("c_y", "c2.y", comp.b[1]+2)]
        elif t == "switch_sp3t":
            fields = [("throw", "拨到(0/1/2)", 0), ("c_x", "t1.x", comp.b[0]), ("c_y", "t1.y", comp.b[1]+2), ("d_x", "t2.x", comp.b[0]), ("d_y", "t2.y", comp.b[1]+4)]
        elif t == "switch_dpst":
            fields = [("state", "状态(1闭合/0断开)", 1), ("c_x", "p2.a.x", comp.a[0]), ("c_y", "p2.a.y", comp.a[1]+2), ("d_x", "p2.b.x", comp.b[0]), ("d_y", "p2.b.y", comp.b[1]+2)]
        elif t == "switch_dpdt":
            fields = [("throw", "throw(0/1)", 0), ("c_x", "p1.t1.x", comp.b[0]), ("c_y", "p1.t1.y", comp.b[1]+2), ("d_x", "p2.com.x", comp.a[0]), ("d_y", "p2.com.y", comp.a[1]+4), ("e_x", "p2.t0.x", comp.a[0]+6), ("e_y", "p2.t0.y", comp.a[1]+4), ("f_x", "p2.t1.x", comp.a[0]+6), ("f_y", "p2.t1.y", comp.a[1]+6)]
        elif t == "button_momentary":
            fields = [("pressed", "按下(1)/松开(0)", 0)]
        elif t == "ammeter":
            fields = [("range", "量程档位(index)", 0), ("burden_V", "表压降(V@满量程)", 0.05)]
        elif t == "voltmeter":
            fields = [("range", "量程档位(index)", 0), ("ohm_per_V", "灵敏度(Ω/V)", 20000.0)]
        elif t == "galvanometer":
            fields = [("range", "量程档位(index)", 0), ("Rcoil", "线圈电阻(Ω)", 50.0), ("Ifs", "满偏电流(A)", 50e-6)]
        else:
            fields = list(comp.props.items())

        h, w = self.stdscr.getmaxyx()
        win_h = min(12, h-4)
        win_w = min(60, w-4)
        win = curses.newwin(win_h, win_w, (h-win_h)//2, (w-win_w)//2)
        win.keypad(True)
        sel = 0

        while True:
            win.erase()
            win.box()
            win.addstr(1, 2, f"编辑 {comp.display_name()}  (Enter修改, q退出)")
            for i, (k, label, default) in enumerate(fields):
                v = comp.props.get(k, default)
                mark = ">" if i == sel else " "
                win.addstr(3+i, 2, f"{mark} {label}: {v}")
            win.refresh()

            ch = win.getch()
            if ch == 27:
                if self.wire_start is not None:
                    self.cancel_wire()
                    continue
                break

            if ch == ord('q'):
                break
            if ch in (curses.KEY_UP, ord('k')):
                sel = (sel - 1) % len(fields)
            elif ch in (curses.KEY_DOWN, ord('j')):
                sel = (sel + 1) % len(fields)
            elif ch in (curses.KEY_ENTER, 10, 13):
                k, label, default = fields[sel]
                val = self.read_number(win, prompt=f"{label} = ", initial=str(comp.props.get(k, default)))
                if val is not None:
                    comp.props[k] = val
                    self.solve()
                    self.history.record(self.cir)

    def read_number(self, win, prompt: str, initial: str="") -> Optional[float]:
        win.addstr(win.getmaxyx()[0]-2, 2, " " * (win.getmaxyx()[1]-4))
        win.addstr(win.getmaxyx()[0]-2, 2, prompt + initial)
        curses.curs_set(1)
        s = initial
        while True:
            win.addstr(win.getmaxyx()[0]-2, 2+len(prompt), " " * (win.getmaxyx()[1]-4-len(prompt)))
            win.addstr(win.getmaxyx()[0]-2, 2+len(prompt), s)
            win.refresh()
            ch = win.getch()
            if ch in (27, ord('q')):
                curses.curs_set(0)
                return None
            if ch in (10, 13):
                try:
                    curses.curs_set(0)
                    return float(s)
                except Exception:
                    return None
            if ch in (curses.KEY_BACKSPACE, 127, 8):
                s = s[:-1]
            elif 32 <= ch <= 126:
                s += chr(ch)

    def read_text(self, win, prompt: str, initial: str="") -> Optional[str]:
        win.addstr(win.getmaxyx()[0]-2, 2, " " * (win.getmaxyx()[1]-4))
        win.addstr(win.getmaxyx()[0]-2, 2, prompt + initial)
        curses.curs_set(1)
        s = initial
        while True:
            win.addstr(win.getmaxyx()[0]-2, 2+len(prompt), " " * (win.getmaxyx()[1]-4-len(prompt)))
            win.addstr(win.getmaxyx()[0]-2, 2+len(prompt), s)
            win.refresh()
            ch = win.getch()
            if ch in (27, ord('q')):
                curses.curs_set(0)
                return None
            if ch in (10, 13):
                curses.curs_set(0)
                return s.strip()
            if ch in (curses.KEY_BACKSPACE, 127, 8):
                s = s[:-1]
            elif 32 <= ch <= 126:
                s += chr(ch)

    def resolve_cid(self, token: str) -> Optional[str]:
        t = (token or "").strip()
        if not t:
            return None
        if t.lower() in ("socket", "src", "source"):
            for c in self.cir.components.values():
                if c.ctype == "socket":
                    return c.cid
            return None
        if t in self.cir.components:
            return t
        matches = [cid for cid in self.cir.components.keys() if cid.startswith(t)]
        if len(matches) == 1:
            return matches[0]
        return None

    def prompt_goal_seek(self):
        h, w = self.stdscr.getmaxyx()
        win_h = 14
        win_w = min(72, w - 4)
        win = curses.newwin(win_h, win_w, max(1, (h - win_h) // 2), max(1, (w - win_w) // 2))
        win.keypad(True)

        near = self.cir.find_near(self.cursor)
        default_var = near.cid[:4] if near else ""
        default_prop = "R"
        if near and near.ctype == "socket":
            default_prop = "V"

        win.erase(); win.box()
        win.addstr(1, 2, "Goal Seek(反求)  - 输入 q/Esc 取消")
        win.addstr(2, 2, "变量: A电阻R / B电源V / C滑变R（变量元件在光标附近更方便）")
        win.refresh()

        var_tok = self.read_text(win, "Var cid(4位前缀/全cid/socket)=", initial=default_var)
        if var_tok is None:
            return
        var_cid = self.resolve_cid(var_tok)
        if var_cid is None:
            self.status = "反求失败：找不到变量元件 cid"
            return
        var_comp = self.cir.components.get(var_cid)
        if var_comp is None:
            self.status = "反求失败：变量元件不存在"
            return

        var_prop = self.read_text(win, "Var prop(R/V)=", initial=default_prop)
        if var_prop is None:
            return
        var_prop = (var_prop or "").strip() or default_prop

        kind = self.read_text(win, "Measure kind [c=comp/n=node]=", initial="c")
        if kind is None:
            return
        kind = (kind or "c").strip().lower()

        measure = {}
        if kind in ("n", "node"):
            nx = self.read_number(win, "Node x=", initial=str(self.cursor[0]))
            if nx is None:
                return
            ny = self.read_number(win, "Node y=", initial=str(self.cursor[1]))
            if ny is None:
                return
            ab = self.read_text(win, "abs? (0/1)=", initial="0")
            if ab is None:
                return
            measure = {"kind": "node", "node": [int(nx), int(ny)], "abs": (ab.strip() == "1")}
        else:
            sock = None
            for c in self.cir.components.values():
                if c.ctype == "socket":
                    sock = c
                    break
            default_meas = sock.cid[:4] if sock else var_cid[:4]
            meas_tok = self.read_text(win, "Measure cid(4位前缀/全cid/socket)=", initial=default_meas)
            if meas_tok is None:
                return
            meas_cid = self.resolve_cid(meas_tok)
            if meas_cid is None:
                self.status = "反求失败：找不到测量元件 cid"
                return
            field = self.read_text(win, "Field(Iab/Vab/Va/Vb/P/R)=", initial="Iab")
            if field is None:
                return
            field = (field or "Iab").strip() or "Iab"
            br = self.read_text(win, "Branch(optional, e.g. p1/t0)=", initial="")
            if br is None:
                return
            ab = self.read_text(win, "abs? (0/1)=", initial="1")
            if ab is None:
                return
            measure = {"kind": "comp", "cid": meas_cid, "field": field, "abs": (ab.strip() == "1")}
            if br.strip():
                measure["branch"] = br.strip()

        target = self.read_number(win, "Target=", initial="")
        if target is None:
            return

        reject_oc = self.read_text(win, "Reject overcurrent? (0/1)=", initial="0")
        if reject_oc is None:
            return
        auto_rng = self.read_text(win, "Auto-range meter? (0/1)=", initial="1")
        if auto_rng is None:
            return

        lo0 = "0"
        hi0 = "1000"
        if var_prop == "V":
            lo0, hi0 = "0", "30"
        if var_prop == "R" and var_comp.ctype == "rheostat":
            lo0 = str(var_comp.props.get("Rmin", 0.0))
            hi0 = str(var_comp.props.get("Rmax", max(float(var_comp.props.get("R", 100.0)), 100.0)))

        lo = self.read_number(win, "Lo=", initial=lo0)
        if lo is None:
            return
        hi = self.read_number(win, "Hi=", initial=hi0)
        if hi is None:
            return

        if auto_rng.strip() == "1" and measure.get("kind") == "comp" and measure.get("abs"):
            mcid = measure.get("cid")
            mcomp = self.cir.components.get(mcid) if mcid else None
            if mcomp and mcomp.ctype in ("ammeter", "voltmeter", "galvanometer"):
                rngs = meter_ranges(mcomp)
                if rngs:
                    tgt = abs(float(target))
                    idx = 0
                    while idx < len(rngs) and abs(float(rngs[idx])) < tgt:
                        idx += 1
                    if idx >= len(rngs):
                        idx = len(rngs) - 1
                    mcomp.props["range"] = int(idx)

        gs = goal_seek_parameter(
            self.cir,
            var_cid=var_cid,
            var_prop=var_prop,
            target=float(target),
            measure=measure,
            lo=float(lo),
            hi=float(hi),
            reject_if_overcurrent=(reject_oc.strip() == "1"),
        )
        if gs.ok:
            self.solve()
            self.history.record(self.cir)
            self.status = f"反求成功 {var_comp.display_name()} {var_prop}={gs.value:.6g}  达到={gs.achieved:.6g}"
        else:
            self.status = f"反求失败：{gs.message} (best={gs.value:.6g} 达到={gs.achieved:.6g})"

    def render(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        canvas: Dict[Tuple[int,int], str] = {}
        junction: Dict[Tuple[int,int], int] = {}

        for y in range(GRID_H):
            for x in range(GRID_W):
                if x % 2 == 0 and y % 2 == 0:
                    canvas[(x, y)] = "·"

        overcurrent_cids = {cid for cid, fl in self.result.comp_flags.items() if fl in ("source_overcurrent", "overcurrent")}

        for c in self.cir.components.values():
            pts = _path_points(c.a, c.b)
            open_like = False
            if self.result.comp_flags.get(c.cid) == "open":
                open_like = True
            if c.ctype == "switch_spst" and int(c.props.get("state", 1)) == 0:
                open_like = True
            if c.ctype == "button_momentary" and int(c.props.get("pressed", 0)) == 0:
                open_like = True

            cut_idx = None
            if open_like and len(pts) >= 4:
                cut_idx = len(pts) // 2

            for i in range(len(pts) - 1):
                if cut_idx is not None and (i == cut_idx or i == cut_idx - 1):
                    continue
                x1, y1 = pts[i]
                x2, y2 = pts[i+1]
                if x2 == x1 and y2 == y1:
                    continue
                if x2 == x1:
                    if y2 < y1:
                        junction[(x1, y1)] = junction.get((x1, y1), 0) | 1
                        junction[(x2, y2)] = junction.get((x2, y2), 0) | 4
                    else:
                        junction[(x1, y1)] = junction.get((x1, y1), 0) | 4
                        junction[(x2, y2)] = junction.get((x2, y2), 0) | 1
                elif y2 == y1:
                    if x2 > x1:
                        junction[(x1, y1)] = junction.get((x1, y1), 0) | 2
                        junction[(x2, y2)] = junction.get((x2, y2), 0) | 8
                    else:
                        junction[(x1, y1)] = junction.get((x1, y1), 0) | 8
                        junction[(x2, y2)] = junction.get((x2, y2), 0) | 2

            mx = (c.a[0] + c.b[0]) // 2
            my = (c.a[1] + c.b[1]) // 2
            canvas[(mx, my)] = comp_symbol(c)
            if cut_idx is not None:
                gx, gy = pts[cut_idx]
                canvas[(gx, gy)] = "⨯"

        if self.wire_start is not None:
            pts = _path_points(self.wire_start, self.cursor)
            for i in range(len(pts) - 1):
                x1, y1 = pts[i]
                x2, y2 = pts[i+1]
                if x1 == x2 and y1 == y2:
                    continue
                if (x1, y1) not in canvas or canvas.get((x1, y1)) == "·":
                    canvas[(x1, y1)] = "·"
                if (x2, y2) not in canvas or canvas.get((x2, y2)) == "·":
                    canvas[(x2, y2)] = "·"

        for (x, y), msk in junction.items():
            if (x, y) not in canvas or canvas[(x, y)] == "·":
                canvas[(x, y)] = _junction_char(msk)

        ox, oy = 2, 2
        for (x, y), ch in canvas.items():
            if 0 <= x < GRID_W and 0 <= y < GRID_H:
                sx, sy = ox + x, oy + y
                if 0 <= sy < h-6 and 0 <= sx < w-1:
                    try:
                        attr = 0
                        comp = self.cir.find_near((x, y))
                        if comp and comp.cid in overcurrent_cids:
                            attr = curses.A_BOLD
                            try:
                                attr |= curses.color_pair(1)
                            except Exception:
                                pass
                        self.stdscr.addstr(sy, sx, ch, attr)
                    except curses.error:
                        pass

        cx, cy = self.cursor
        sx, sy = ox + cx, oy + cy
        if 0 <= sy < h-6 and 0 <= sx < w-1:
            try:
                self.stdscr.addstr(sy, sx, "▣", curses.A_REVERSE)
            except curses.error:
                pass

        mode_name = ["导航", "放置", "布线"][self.mode]
        self.stdscr.addstr(h-5, 1, f"Mode:{mode_name}  Place:{self.place_type}  Cursor:{self.cursor}  Details:{'ON' if self.show_details else 'OFF'}")
        self.stdscr.addstr(h-4, 1, f"Socket: tcp://{HOST}:{PORT}  保存:{SAVE_FILE}  {self.status}")

        if self.result.warnings:
            warn = " | ".join(self.result.warnings[:2])
            self.stdscr.addstr(h-3, 1, f"⚠ {warn}"[:w-2], curses.A_BOLD)

        comp = self.cir.find_near(self.cursor)
        if comp:
            self.draw_inspector(comp, h, w)
        else:
            self.stdscr.addstr(h-2, 1, "无选中元件（靠近元件端点或中点以查看/编辑）")

        help_line = "Tab切模式 W布线 Esc取消布线 g反求 1电源 2导线 3电阻 4灯泡 5滑变 6SPST 7SPDT tSP3T pDPST oDPDT b按钮 8A表 9V表 0检流计 [+/-]调选中 u撤销 U重做 e编辑 i细节 d删除 s保存 l加载 r仿真 q退出"
        self.stdscr.addstr(h-1, 1, help_line[:w-2])

        self.stdscr.refresh()

    def draw_inspector(self, comp: Component, h, w):
        Va = self.result.node_v.get(comp.a, 0.0)
        Vb = self.result.node_v.get(comp.b, 0.0)
        Iab = self.result.comp_i.get(comp.cid, 0.0)
        Vab = Va - Vb

        line = f"选中: {comp.display_name()}  a={comp.a} b={comp.b}"
        if comp.ctype in ("socket", "resistor", "wire", "bulb", "rheostat", "switch_spst", "ammeter", "voltmeter", "galvanometer"):
            line += f" | Vab={format_si_safe(Vab,'V')} Iab={format_si_safe(Iab,'A')}"
        self.stdscr.addstr(h-2, 1, " " * (w-2))
        self.stdscr.addstr(h-2, 1, line[:w-2])

        if not self.show_details:
            return

        detail = []
        detail.append(f"节点电压: Va={Va:.6g}V, Vb={Vb:.6g}V, ΔV={Vab:.6g}V")
        t = comp.ctype
        if t == "bulb":
            Vr = float(comp.props.get("Vr", 6.0))
            Wr = float(comp.props.get("Wr", 3.0))
            R = bulb_resistance(Vr, Wr)
            detail.append(f"灯泡规格: Vr={Vr}V Wr={Wr}W => 等效R≈{R:.6g}Ω（教学模型）")
        elif t == "resistor":
            detail.append(f"电阻: R={comp.props.get('R', 100.0)}Ω")
        elif t == "rheostat":
            detail.append(f"滑变: R={comp.props.get('R', 100.0)}Ω（可调）")
        elif t == "switch_spst":
            st = int(comp.props.get("state", 1))
            detail.append(f"开关SPST: {'闭合' if st==1 else '断开'}")
        elif t == "socket":
            detail.append(f"电源: V={comp.props.get('V', 5.0)}V  Iwarn={comp.props.get('Iwarn', 5.0)}A")
        elif t == "ammeter":
            fs = meter_full_scale(comp)
            mfs = meter_native_full_scale(comp)
            reading = "OL" if (mfs is not None and abs(Iab) > abs(mfs) * 1.02) else format_si_safe(Iab, 'A')
            detail.append(f"电流表: 读数≈{reading}  量程={fs if fs is not None else 'custom'}")
        elif t == "voltmeter":
            fs = meter_full_scale(comp)
            mfs = meter_native_full_scale(comp)
            reading = "OL" if (mfs is not None and abs(Vab) > abs(mfs) * 1.02) else format_si_safe(Vab, 'V')
            detail.append(f"电压表: 读数≈{reading}  量程={fs if fs is not None else 'custom'}")
        elif t == "galvanometer":
            Ifs = float(comp.props.get("Ifs", 50e-6))
            mfs = meter_native_full_scale(comp)
            reading = "OL" if (mfs is not None and abs(Iab) > abs(mfs) * 1.02) else format_si_safe(Iab, 'A')
            detail.append(f"检流计: Rcoil={comp.props.get('Rcoil',50.0)}Ω  Ifs={Ifs}A  读数≈{reading}  满偏≈{abs(Iab)/Ifs:.3g}x")

        y = h-3
        for i, s in enumerate(detail[:2]):
            try:
                self.stdscr.addstr(y - (1-i), 1, s[:w-2])
            except curses.error:
                pass

    def place_component(self):
        x, y = self.cursor
        a = (x, y)
        b = (clamp(x+8, 0, GRID_W-1), y)
        t = self.place_type

        if t == "switch_spdt":
            cid = self.cir.add("switch_spdt", a, b, throw=0, c_x=b[0], c_y=clamp(y+4,0,GRID_H-1))
        elif t == "switch_sp3t":
            cid = self.cir.add("switch_sp3t", a, b, throw=0, c_x=b[0], c_y=clamp(y+4,0,GRID_H-1), d_x=b[0], d_y=clamp(y+8,0,GRID_H-1))
        elif t == "switch_dpst":
            cid = self.cir.add("switch_dpst", a, b, state=1, c_x=a[0], c_y=clamp(y+4,0,GRID_H-1), d_x=b[0], d_y=clamp(y+4,0,GRID_H-1))
        elif t == "switch_dpdt":
            cid = self.cir.add("switch_dpdt", a, b, throw=0, c_x=b[0], c_y=clamp(y+2,0,GRID_H-1), d_x=a[0], d_y=clamp(y+6,0,GRID_H-1), e_x=b[0], e_y=clamp(y+6,0,GRID_H-1), f_x=b[0], f_y=clamp(y+8,0,GRID_H-1))
        elif t == "button_momentary":
            cid = self.cir.add("button_momentary", a, b, pressed=0)
        elif t == "socket":
            cid = self.cir.add("socket", a, (x, clamp(y+6,0,GRID_H-1)), V=5.0, Iwarn=5.0)
        elif t == "wire":
            cid = self.cir.add("wire", a, b)
        elif t == "resistor":
            cid = self.cir.add("resistor", a, b, R=100.0)
        elif t == "bulb":
            cid = self.cir.add("bulb", a, b, Vr=6.0, Wr=3.0)
        elif t == "rheostat":
            cid = self.cir.add("rheostat", a, b, R=200.0)
        elif t == "switch_spst":
            cid = self.cir.add("switch_spst", a, b, state=1)
        elif t == "ammeter":
            cid = self.cir.add("ammeter", a, b, Rin=0.05)
        elif t == "voltmeter":
            cid = self.cir.add("voltmeter", a, b, Rin=1e6)
        elif t == "galvanometer":
            cid = self.cir.add("galvanometer", a, b, Rcoil=50.0, Ifs=50e-6)
        else:
            cid = self.cir.add(t, a, b)

        self.solve()
        self.status = f"已放置 {t} ({cid[:6]})"

    def toggle_wire(self):
        if self.wire_start is None:
            self.wire_start = self.cursor
            self.status = f"布线起点 {self.wire_start}"
        else:
            a = self.wire_start
            b = self.cursor
            self.cir.add("wire", a, b)
            self.wire_start = None
            self.solve()
            self.status = f"已布线 {a}->{b}"
            self.history.record(self.cir)

    def cancel_wire(self):
        self.wire_start = None
        self.status = "已取消布线"

    def adjust_selected(self, delta: int):
        comp = self.cir.find_near(self.cursor)
        if not comp:
            return
        if comp.ctype == "rheostat":
            step = float(comp.props.get("step", 5.0))
            comp.props["R"] = float(comp.props.get("R", 100.0)) + delta * step
            self.solve()
            self.status = f"滑变 R={comp.props.get('R', 0.0):.6g}Ω"
            self.history.record(self.cir)
            return
        if comp.ctype in ("ammeter", "voltmeter", "galvanometer"):
            cur = int(comp.props.get("range", 0))
            comp.props["range"] = max(cur + delta, 0)
            self.solve()
            self.status = f"量程 index={comp.props.get('range', 0)}"
            self.history.record(self.cir)
            return

    def undo(self):
        if self.history.undo(self.cir):
            self.solve()
            self.status = "撤销"
        else:
            self.status = "无可撤销"

    def redo(self):
        if self.history.redo(self.cir):
            self.solve()
            self.status = "重做"
        else:
            self.status = "无可重做"

    def run(self):
        curses.curs_set(0)
        self.init_colors()
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

        last = 0
        while True:
            self.handle_socket_commands()
            now = time.time()
            if now - last > 0.05:
                self.render()
                last = now

            try:
                ch = self.stdscr.getch()
            except Exception:
                ch = -1

            if ch == -1:
                time.sleep(0.01)
                continue

            if ch in (ord('q'), 27):
                break

            if ch in (curses.KEY_LEFT, ord('h')):
                self.cursor = (clamp(self.cursor[0]-1, 0, GRID_W-1), self.cursor[1])
            elif ch in (curses.KEY_RIGHT, ord('l')):
                self.cursor = (clamp(self.cursor[0]+1, 0, GRID_W-1), self.cursor[1])
            elif ch in (curses.KEY_UP, ord('k')):
                self.cursor = (self.cursor[0], clamp(self.cursor[1]-1, 0, GRID_H-1))
            elif ch in (curses.KEY_DOWN, ord('j')):
                self.cursor = (self.cursor[0], clamp(self.cursor[1]+1, 0, GRID_H-1))

            elif ch == ord('\t'):
                self.mode = (self.mode + 1) % 3
                self.status = f"切换模式: {['导航','放置','布线'][self.mode]}"

            elif ch in (ord('i'),):
                self.show_details = not self.show_details
                self.status = "详细信息 ON" if self.show_details else "详细信息 OFF"

            elif ch in (ord('r'),):
                self.solve()

            elif ch in (ord('s'),):
                self.save()

            elif ch in (ord('l'),):
                self.load()

            elif ch in (ord('d'),):
                deleted = self.cir.delete_at(self.cursor)
                if deleted:
                    self.solve()
                    self.history.record(self.cir)
                    self.status = f"已删除 {deleted[:6]}"
                else:
                    self.status = "未找到可删除元件"

            elif ch in (ord('e'),):
                comp = self.cir.find_near(self.cursor)
                if comp:
                    self.prompt_edit(comp)
                else:
                    self.status = "未选中元件"

            elif ch in (ord('g'), ord('G')):
                self.prompt_goal_seek()

            elif ch in (ord('W'), ord('w')):
                self.toggle_wire()

            elif ch in (ord('+'), ord('=')):
                self.adjust_selected(+1)
            elif ch in (ord('-'), ord('_')):
                self.adjust_selected(-1)

            elif ch == ord('u'):
                self.undo()
            elif ch == ord('U'):
                self.redo()

            elif ch == ord('1'):
                self.place_type = "socket"
            elif ch == ord('2'):
                self.place_type = "wire"
            elif ch == ord('3'):
                self.place_type = "resistor"
            elif ch == ord('4'):
                self.place_type = "bulb"
            elif ch == ord('5'):
                self.place_type = "rheostat"
            elif ch == ord('6'):
                self.place_type = "switch_spst"
            elif ch == ord('7'):
                self.place_type = "switch_spdt"
            elif ch in (ord('t'), ord('T')):
                self.place_type = "switch_sp3t"
            elif ch in (ord('p'), ord('P')):
                self.place_type = "switch_dpst"
            elif ch in (ord('o'), ord('O')):
                self.place_type = "switch_dpdt"
            elif ch in (ord('b'), ord('B')):
                self.place_type = "button_momentary"
            elif ch == ord('8'):
                self.place_type = "ammeter"
            elif ch == ord('9'):
                self.place_type = "voltmeter"
            elif ch == ord('0'):
                self.place_type = "galvanometer"

            elif ch in (10, 13):
                if self.mode == 1:
                    self.place_component()
                elif self.mode == 2:
                    self.toggle_wire()

            elif ch == ord(' '):
                comp = self.cir.find_near(self.cursor)
                if comp and comp.ctype == "switch_spst":
                    st = int(comp.props.get("state", 1))
                    comp.props["state"] = 0 if st == 1 else 1
                    self.solve()
                    self.history.record(self.cir)
                    self.status = f"开关 {'断开' if comp.props['state']==0 else '闭合'}"
                elif comp and comp.ctype == "switch_spdt":
                    th = int(comp.props.get("throw", 0))
                    comp.props["throw"] = 1 - th
                    self.solve()
                    self.history.record(self.cir)
                    self.status = f"SPDT throw={comp.props['throw']}"
                elif comp and comp.ctype == "switch_sp3t":
                    th = int(comp.props.get("throw", 0))
                    comp.props["throw"] = (th + 1) % 3
                    self.solve()
                    self.history.record(self.cir)
                    self.status = f"SP3T throw={comp.props['throw']}"
                elif comp and comp.ctype == "switch_dpst":
                    st = int(comp.props.get("state", 1))
                    comp.props["state"] = 0 if st == 1 else 1
                    self.solve()
                    self.history.record(self.cir)
                    self.status = f"DPST {'断开' if comp.props['state']==0 else '闭合'}"
                elif comp and comp.ctype == "switch_dpdt":
                    th = int(comp.props.get("throw", 0))
                    comp.props["throw"] = 1 - th
                    self.solve()
                    self.history.record(self.cir)
                    self.status = f"DPDT throw={comp.props['throw']}"
                elif comp and comp.ctype == "button_momentary":
                    pr = int(comp.props.get("pressed", 0))
                    comp.props["pressed"] = 0 if pr == 1 else 1
                    self.solve()
                    self.history.record(self.cir)
                    self.status = f"按钮 {'松开' if comp.props['pressed']==0 else '按下'}"

        self.stop()

def main_tui(stdscr):
    app = TUIApp(stdscr)
    try:
        app.run()
    finally:
        app.stop()
