#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circuit Simulator Core
- DC steady-state solver via Modified Nodal Analysis (MNA)
- Components: Socket(Voltage Source), Wire, Resistor, Bulb, Rheostat, Switch(SPST/SPDT),
              Ammeter, Voltmeter, Galvanometer
- Pure logic, no UI dependencies
"""

import json
import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Point = Tuple[int, int]

R_NEAR_SHORT = 1e-9

def _parse_float_list(s: str) -> List[float]:
    s = (s or "").strip()
    if not s:
        return []
    try:
        obj = json.loads(s)
        if isinstance(obj, list):
            out: List[float] = []
            for it in obj:
                try:
                    out.append(float(it))
                except Exception:
                    continue
            return out
    except Exception:
        pass
    parts = [p.strip() for p in s.replace(";", ",").split(",")]
    out2: List[float] = []
    for p in parts:
        if not p:
            continue
        try:
            out2.append(float(p))
        except Exception:
            continue
    return out2

def meter_ranges(comp: "Component") -> List[float]:
    if comp.ctype == "ammeter":
        return _parse_float_list(str(comp.meta.get("ranges_I", comp.meta.get("ranges", ""))))
    if comp.ctype == "voltmeter":
        return _parse_float_list(str(comp.meta.get("ranges_V", comp.meta.get("ranges", ""))))
    if comp.ctype == "galvanometer":
        return _parse_float_list(str(comp.meta.get("ranges_I", comp.meta.get("ranges", ""))))
    return []

def meter_range_index(comp: "Component") -> int:
    try:
        return int(comp.props.get("range", 0))
    except Exception:
        return 0

def meter_full_scale(comp: "Component") -> Optional[float]:
    ranges = meter_ranges(comp)
    if not ranges:
        return None
    idx = meter_range_index(comp)
    if idx < 0:
        idx = 0
    if idx >= len(ranges):
        idx = len(ranges) - 1
    return float(ranges[idx])

def meter_effective_resistance(comp: "Component") -> float:
    if comp.ctype == "ammeter":
        fs = meter_full_scale(comp)
        if fs is None:
            return max(float(comp.props.get("Rin", 0.05)), R_NEAR_SHORT)
        burden_v = float(comp.props.get("burden_V", 0.05))
        return max(burden_v / max(abs(fs), 1e-15), R_NEAR_SHORT)
    if comp.ctype == "voltmeter":
        fs = meter_full_scale(comp)
        if fs is None:
            return max(float(comp.props.get("Rin", 1e6)), R_NEAR_SHORT)
        ohm_per_v = float(comp.props.get("ohm_per_V", comp.props.get("sens", 1e4)))
        return max(ohm_per_v * max(abs(fs), 1e-15), R_NEAR_SHORT)
    if comp.ctype == "galvanometer":
        fs = meter_full_scale(comp)
        if fs is None:
            return max(float(comp.props.get("Rcoil", 50.0)), R_NEAR_SHORT)
        Rcoil = float(comp.props.get("Rcoil", 50.0))
        Ifs = float(comp.props.get("Ifs", 50e-6))
        if abs(Ifs) < 1e-15:
            return max(Rcoil, R_NEAR_SHORT)
        ratio = abs(fs) / abs(Ifs)
        if ratio <= 1.0:
            return max(Rcoil, R_NEAR_SHORT)
        Rs = max(Rcoil / (ratio - 1.0), R_NEAR_SHORT)
        return max(1.0 / (1.0 / Rcoil + 1.0 / Rs), R_NEAR_SHORT)
    return 1e12

def solve_linear(A: List[List[float]], b: List[float]) -> Optional[List[float]]:
    """Solve Ax=b using Gaussian elimination with partial pivoting. Return None if singular."""
    n = len(A)
    M = [row[:] for row in A]
    x = b[:]
    eps = 1e-12

    for col in range(n):
        pivot = col
        best = abs(M[col][col])
        for r in range(col + 1, n):
            v = abs(M[r][col])
            if v > best:
                best = v
                pivot = r
        if best < eps:
            return None
        if pivot != col:
            M[col], M[pivot] = M[pivot], M[col]
            x[col], x[pivot] = x[pivot], x[col]

        piv = M[col][col]
        inv = 1.0 / piv
        for c in range(col, n):
            M[col][c] *= inv
        x[col] *= inv

        for r in range(n):
            if r == col:
                continue
            factor = M[r][col]
            if abs(factor) < eps:
                continue
            for c in range(col, n):
                M[r][c] -= factor * M[col][c]
            x[r] -= factor * x[col]

    return x

@dataclass
class Component:
    cid: str
    ctype: str
    a: Point
    b: Point
    props: Dict[str, float] = field(default_factory=dict)
    meta: Dict[str, str] = field(default_factory=dict)

    def display_name(self) -> str:
        return f"{self.ctype}:{self.cid[:4]}"

@dataclass
class Circuit:
    components: Dict[str, Component] = field(default_factory=dict)

    def add(self, ctype: str, a: Point, b: Point, **props) -> str:
        cid = uuid.uuid4().hex
        comp = Component(cid=cid, ctype=ctype, a=a, b=b, props=dict(props))
        self.components[cid] = comp
        return cid

    def delete_at(self, p: Point) -> Optional[str]:
        for cid, c in list(self.components.items()):
            if c.a == p or c.b == p:
                del self.components[cid]
                return cid
            mx = (c.a[0] + c.b[0]) / 2
            my = (c.a[1] + c.b[1]) / 2
            if int(round(mx)) == p[0] and int(round(my)) == p[1]:
                del self.components[cid]
                return cid
        return None

    def find_near(self, p: Point) -> Optional[Component]:
        best = None
        bestd = 10**9
        for c in self.components.values():
            pts = [c.a, c.b, ((c.a[0]+c.b[0])//2, (c.a[1]+c.b[1])//2)]
            for q in pts:
                d = abs(q[0]-p[0]) + abs(q[1]-p[1])
                if d < bestd:
                    bestd = d
                    best = c
        if bestd <= 1:
            return best
        return None

    def to_json(self) -> Dict:
        return {
            "components": [
                {
                    "cid": c.cid, "ctype": c.ctype,
                    "a": list(c.a), "b": list(c.b),
                    "props": c.props, "meta": c.meta
                } for c in self.components.values()
            ]
        }

    @staticmethod
    def from_json(obj: Dict) -> "Circuit":
        cir = Circuit()
        for it in obj.get("components", []):
            c = Component(
                cid=it["cid"],
                ctype=it["ctype"],
                a=tuple(it["a"]),
                b=tuple(it["b"]),
                props=dict(it.get("props", {})),
                meta=dict(it.get("meta", {})),
            )
            cir.components[c.cid] = c
        return cir

    def apply_json(self, obj: Dict) -> None:
        self.components.clear()
        for it in obj.get("components", []):
            c = Component(
                cid=it["cid"],
                ctype=it["ctype"],
                a=tuple(it["a"]),
                b=tuple(it["b"]),
                props=dict(it.get("props", {})),
                meta=dict(it.get("meta", {})),
            )
            self.components[c.cid] = c


@dataclass
class CircuitHistory:
    max_len: int = 200
    undo_stack: List[Dict] = field(default_factory=list)
    redo_stack: List[Dict] = field(default_factory=list)

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()

    def record(self, cir: Circuit) -> None:
        snap = cir.to_json()
        if self.undo_stack and self.undo_stack[-1] == snap:
            return
        self.undo_stack.append(snap)
        if len(self.undo_stack) > self.max_len:
            self.undo_stack = self.undo_stack[-self.max_len :]
        self.redo_stack.clear()

    def can_undo(self) -> bool:
        return len(self.undo_stack) >= 2

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def undo(self, cir: Circuit) -> bool:
        if not self.can_undo():
            return False
        cur = self.undo_stack.pop()
        self.redo_stack.append(cur)
        prev = self.undo_stack[-1]
        cir.apply_json(prev)
        return True

    def redo(self, cir: Circuit) -> bool:
        if not self.can_redo():
            return False
        nxt = self.redo_stack.pop()
        self.undo_stack.append(nxt)
        cir.apply_json(nxt)
        return True

@dataclass
class SolveResult:
    ok: bool
    node_v: Dict[Point, float] = field(default_factory=dict)
    comp_i: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    singular: bool = False
    comp_flags: Dict[str, str] = field(default_factory=dict)
    comp_branch_i: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class GoalSeekResult:
    ok: bool
    value: float = 0.0
    achieved: float = 0.0
    target: float = 0.0
    error: float = 0.0
    iterations: int = 0
    message: str = ""
    history: List[Tuple[float, float]] = field(default_factory=list)

def bulb_resistance(Vr: float, Wr: float) -> float:
    if Wr <= 1e-12:
        return 1e12
    return max((Vr * Vr) / Wr, 1e-6)

def effective_resistance(comp: Component) -> Optional[float]:
    t = comp.ctype
    if t in ("wire",):
        return R_NEAR_SHORT
    if t in ("resistor",):
        return max(float(comp.props.get("R", 100.0)), 1e-6)
    if t in ("bulb",):
        Vr = float(comp.props.get("Vr", 6.0))
        Wr = float(comp.props.get("Wr", 3.0))
        return bulb_resistance(Vr, Wr)
    if t in ("rheostat",):
        R = float(comp.props.get("R", 100.0))
        Rmin = float(comp.props.get("Rmin", 0.0))
        Rmax = float(comp.props.get("Rmax", max(R, 100.0)))
        if Rmax < Rmin:
            Rmin, Rmax = Rmax, Rmin
        R = max(min(R, Rmax), Rmin)
        comp.props["R"] = R
        return max(R, 1e-6)
    if t in ("ammeter",):
        return meter_effective_resistance(comp)
    if t in ("galvanometer",):
        return meter_effective_resistance(comp)
    if t in ("voltmeter",):
        return meter_effective_resistance(comp)
    if t in ("switch_spst",):
        state = int(comp.props.get("state", 1))
        return R_NEAR_SHORT if state == 1 else None
    if t in ("button_momentary",):
        pressed = int(comp.props.get("pressed", 0))
        return R_NEAR_SHORT if pressed == 1 else None
    return None

def solve_circuit(cir: Circuit) -> SolveResult:
    """MNA formulation for DC steady-state analysis"""
    res = SolveResult(ok=False)
    comps = list(cir.components.values())

    ground = None
    for c in comps:
        if c.ctype == "socket":
            ground = c.b
            break
    if ground is None:
        all_pts = []
        for c in comps:
            all_pts.extend([c.a, c.b])
        ground = min(all_pts) if all_pts else (0, 0)

    expanded: List[Component] = []
    solver_parent: Dict[str, str] = {}
    solver_label: Dict[str, str] = {}
    for c in comps:
        if c.ctype == "switch_spdt":
            throw = int(c.props.get("throw", 0))
            c2 = (int(c.props.get("c_x", c.b[0])), int(c.props.get("c_y", c.b[1] + 2)))
            if throw == 0:
                cc = Component(cid=f"{c.cid}:t0", ctype="switch_spst", a=c.a, b=c.b, props={"state": 1}, meta={"variant": "spdt->b"})
                solver_label[cc.cid] = "t0"
            else:
                cc = Component(cid=f"{c.cid}:t1", ctype="switch_spst", a=c.a, b=c2, props={"state": 1}, meta={"variant": "spdt->c2"})
                solver_label[cc.cid] = "t1"
            solver_parent[cc.cid] = c.cid
            expanded.append(cc)
            continue

        if c.ctype == "switch_sp3t":
            throw = int(c.props.get("throw", 0))
            t1 = c.b
            t2 = (int(c.props.get("c_x", c.b[0])), int(c.props.get("c_y", c.b[1] + 2)))
            t3 = (int(c.props.get("d_x", c.b[0])), int(c.props.get("d_y", c.b[1] + 4)))
            targets = [t1, t2, t3]
            if throw < 0:
                throw = 0
            if throw > 2:
                throw = 2
            cc = Component(cid=f"{c.cid}:t{throw}", ctype="switch_spst", a=c.a, b=targets[throw], props={"state": 1}, meta={"variant": f"sp3t->t{throw}"})
            solver_parent[cc.cid] = c.cid
            solver_label[cc.cid] = f"t{throw}"
            expanded.append(cc)
            continue

        if c.ctype == "switch_dpst":
            state = int(c.props.get("state", 1))
            p2a = (int(c.props.get("c_x", c.a[0])), int(c.props.get("c_y", c.a[1] + 2)))
            p2b = (int(c.props.get("d_x", c.b[0])), int(c.props.get("d_y", c.b[1] + 2)))
            c1 = Component(cid=f"{c.cid}:p1", ctype="switch_spst", a=c.a, b=c.b, props={"state": state}, meta={"variant": "dpst:p1"})
            c2 = Component(cid=f"{c.cid}:p2", ctype="switch_spst", a=p2a, b=p2b, props={"state": state}, meta={"variant": "dpst:p2"})
            for cc, lab in ((c1, "p1"), (c2, "p2")):
                solver_parent[cc.cid] = c.cid
                solver_label[cc.cid] = lab
                expanded.append(cc)
            continue

        if c.ctype == "switch_dpdt":
            throw = int(c.props.get("throw", 0))
            if throw < 0:
                throw = 0
            if throw > 1:
                throw = 1
            t1_0 = c.b
            t1_1 = (int(c.props.get("c_x", c.b[0])), int(c.props.get("c_y", c.b[1] + 2)))
            com2 = (int(c.props.get("d_x", c.a[0])), int(c.props.get("d_y", c.a[1] + 4)))
            t2_0 = (int(c.props.get("e_x", com2[0] + 6)), int(c.props.get("e_y", com2[1])))
            t2_1 = (int(c.props.get("f_x", t2_0[0])), int(c.props.get("f_y", t2_0[1] + 2)))
            pole1_target = t1_0 if throw == 0 else t1_1
            pole2_target = t2_0 if throw == 0 else t2_1
            c1 = Component(cid=f"{c.cid}:p1", ctype="switch_spst", a=c.a, b=pole1_target, props={"state": 1}, meta={"variant": f"dpdt:p1:t{throw}"})
            c2 = Component(cid=f"{c.cid}:p2", ctype="switch_spst", a=com2, b=pole2_target, props={"state": 1}, meta={"variant": f"dpdt:p2:t{throw}"})
            for cc, lab in ((c1, "p1"), (c2, "p2")):
                solver_parent[cc.cid] = c.cid
                solver_label[cc.cid] = lab
                expanded.append(cc)
            continue

        if c.ctype == "button_momentary":
            pressed = int(c.props.get("pressed", 0))
            cc = Component(cid=f"{c.cid}:m", ctype="switch_spst", a=c.a, b=c.b, props={"state": 1 if pressed == 1 else 0}, meta={"variant": "momentary"})
            solver_parent[cc.cid] = c.cid
            solver_label[cc.cid] = "m"
            expanded.append(cc)
            continue

        expanded.append(c)
        solver_parent[c.cid] = c.cid
        solver_label[c.cid] = "main"

    nodes: List[Point] = []
    node_set = set()
    for c in expanded:
        node_set.add(c.a); node_set.add(c.b)
    nodes = sorted(node_set)

    node_index: Dict[Point, int] = {}
    idx = 0
    for n in nodes:
        if n == ground:
            continue
        node_index[n] = idx
        idx += 1

    vsources = [c for c in expanded if c.ctype == "socket"]
    m = len(vsources)

    N = len(node_index) + m
    if N == 0:
        res.ok = True
        return res

    A = [[0.0] * N for _ in range(N)]
    bvec = [0.0] * N

    def v_idx(n: Point) -> Optional[int]:
        return node_index.get(n, None)

    warnings = []

    for c in expanded:
        if c.ctype == "socket":
            continue
        R = effective_resistance(c)
        if R is None:
            continue
        g = 1.0 / R
        ia = v_idx(c.a)
        ib = v_idx(c.b)
        if ia is not None:
            A[ia][ia] += g
        if ib is not None:
            A[ib][ib] += g
        if ia is not None and ib is not None:
            A[ia][ib] -= g
            A[ib][ia] -= g

    for k, c in enumerate(vsources):
        row = len(node_index) + k
        ia = v_idx(c.a)
        ib = v_idx(c.b)
        V = float(c.props.get("V", 5.0))
        if ia is not None:
            A[ia][row] += 1.0
            A[row][ia] += 1.0
        if ib is not None:
            A[ib][row] -= 1.0
            A[row][ib] -= 1.0
        bvec[row] = V

    sol = solve_linear(A, bvec)
    if sol is None:
        res.ok = False
        res.singular = True
        warnings.append("电路矩阵奇异：可能是完全断路、缺少参考地、或存在理想短路/冲突电压源。")
        res.warnings = warnings
        return res

    node_v: Dict[Point, float] = {ground: 0.0}
    for n, i in node_index.items():
        node_v[n] = sol[i]

    solver_comp_i: Dict[str, float] = {}
    for c in expanded:
        Va = node_v.get(c.a, 0.0)
        Vb = node_v.get(c.b, 0.0)
        if c.ctype == "socket":
            k = vsources.index(c)
            I = sol[len(node_index) + k]
            solver_comp_i[c.cid] = I
            continue
        R = effective_resistance(c)
        if R is None:
            solver_comp_i[c.cid] = 0.0
        else:
            solver_comp_i[c.cid] = (Va - Vb) / R

    comp_flags: Dict[str, str] = {}
    comp_branch_i: Dict[str, Dict[str, float]] = {}
    for scid, parent in solver_parent.items():
        lab = solver_label.get(scid, "main")
        comp_branch_i.setdefault(parent, {})[lab] = solver_comp_i.get(scid, 0.0)
        sc = next((x for x in expanded if x.cid == scid), None)
        if sc is not None and sc.ctype != "socket" and effective_resistance(sc) is None:
            comp_flags[parent] = "open"

    comp_i: Dict[str, float] = {}
    for oc in comps:
        if oc.ctype == "socket":
            comp_i[oc.cid] = solver_comp_i.get(oc.cid, 0.0)
            continue
        branches = comp_branch_i.get(oc.cid)
        if branches:
            if "main" in branches:
                comp_i[oc.cid] = branches["main"]
            else:
                first_key = sorted(branches.keys())[0]
                comp_i[oc.cid] = branches[first_key]
        else:
            comp_i[oc.cid] = solver_comp_i.get(oc.cid, 0.0)

    for c in vsources:
        I = solver_comp_i.get(c.cid, comp_i.get(c.cid, 0.0))
        if abs(I) > float(c.props.get("Iwarn", 5.0)):
            warnings.append(f"疑似短路：电源 {c.display_name()} 输出电流过大 |I|={abs(I):.3g}A")
            comp_flags[c.cid] = "source_overcurrent"

    max_iwarn = None
    for c in vsources:
        try:
            max_iwarn = max(float(c.props.get("Iwarn", 5.0)), max_iwarn or 0.0)
        except Exception:
            continue
    if max_iwarn is not None and any(comp_flags.get(c.cid) == "source_overcurrent" for c in vsources):
        thr = float(max_iwarn)
        for c in comps:
            if c.cid in comp_flags:
                continue
            if c.ctype == "socket":
                continue
            if abs(comp_i.get(c.cid, 0.0)) > thr:
                comp_flags[c.cid] = "overcurrent"
    if vsources and all(abs(comp_i.get(c.cid, 0.0)) < 1e-6 for c in vsources):
        warnings.append("疑似断路：电源几乎无输出电流（回路未闭合）。")

    res.ok = True
    res.node_v = node_v
    res.comp_i = comp_i
    res.warnings = warnings
    res.comp_flags = comp_flags
    res.comp_branch_i = comp_branch_i
    return res

def component_metrics(result: SolveResult, comp: Component) -> Dict[str, float]:
    Va = result.node_v.get(comp.a, 0.0)
    Vb = result.node_v.get(comp.b, 0.0)
    Vab = Va - Vb
    Iab = result.comp_i.get(comp.cid, 0.0)
    P = Vab * Iab
    out: Dict[str, float] = {
        "Va": Va,
        "Vb": Vb,
        "Vab": Vab,
        "Iab": Iab,
        "P": P,
    }
    R = effective_resistance(comp)
    if R is not None:
        out["R"] = float(R)
    return out


def meter_native_full_scale(comp: "Component") -> Optional[float]:
    fs = meter_full_scale(comp)
    if fs is not None:
        return fs
    if comp.ctype == "galvanometer":
        try:
            return float(comp.props.get("Ifs", 50e-6))
        except Exception:
            return None
    return None


def _is_finite(x: float) -> bool:
    if x != x:
        return False
    if x == float("inf") or x == float("-inf"):
        return False
    return True


def format_value(
    x: float,
    unit: str,
    *,
    style: str = "si",
    max_abs: float = 1e12,
    min_abs: float = 1e-15,
    sig: int = 3,
) -> str:
    try:
        xf = float(x)
    except Exception:
        return "?"
    if not _is_finite(xf):
        return f"∞{unit}"
    ax = abs(xf)
    if 0.0 < ax < float(min_abs):
        return f"~0{unit}"
    if ax > float(max_abs):
        if style == "sci":
            return f">{max_abs:.{sig}e}{unit}" if xf >= 0 else f">{-max_abs:.{sig}e}{unit}"
        return ">" + format_si(max_abs if xf >= 0 else -max_abs, unit)
    if style == "sci":
        return f"{xf:.{sig}e}{unit}"
    return format_si(xf, unit)


def format_si_safe(x: float, unit: str, *, max_abs: float = 1e12) -> str:
    return format_value(x, unit, style="si", max_abs=max_abs, min_abs=1e-15)


def _goal_measure(result: SolveResult, cir: Circuit, spec: Dict[str, Any]) -> Optional[float]:
    kind = str(spec.get("kind", "comp"))
    if kind == "node":
        node = spec.get("node")
        if node is None:
            return None
        n = tuple(node)
        v = float(result.node_v.get(n, 0.0))
        return abs(v) if spec.get("abs") else v

    cid = spec.get("cid")
    field_name = str(spec.get("field", "Iab"))
    if cid is None:
        return None
    branch = spec.get("branch")
    if branch is not None and field_name == "Iab":
        br = result.comp_branch_i.get(str(cid), {})
        if str(branch) in br:
            v = float(br[str(branch)])
            return abs(v) if spec.get("abs") else v
    comp = cir.components.get(str(cid))
    if comp is None:
        return None
    m = component_metrics(result, comp)
    if field_name not in m:
        return None
    v = float(m[field_name])
    return abs(v) if spec.get("abs") else v


def goal_seek_parameter(
    cir: Circuit,
    *,
    var_cid: str,
    var_prop: str,
    target: float,
    measure: Dict[str, Any],
    lo: float,
    hi: float,
    tol_abs: float = 1e-9,
    tol_rel: float = 1e-6,
    max_iter: int = 60,
    method: str = "auto",
    reject_if_overcurrent: bool = False,
) -> GoalSeekResult:
    comp = cir.components.get(var_cid)
    if comp is None:
        return GoalSeekResult(ok=False, message=f"unknown var_cid: {var_cid}")
    if lo == hi:
        return GoalSeekResult(ok=False, message="lo == hi")
    if lo > hi:
        lo, hi = hi, lo

    prev = comp.props.get(var_prop)
    if prev is None:
        prev = 0.0
    prev = float(prev)

    out = GoalSeekResult(ok=False, target=float(target))

    cache: Dict[float, Tuple[Optional[float], Optional[float]]] = {}

    def eval_err(x: float) -> Tuple[Optional[float], Optional[float]]:
        xf = float(x)
        if xf in cache:
            return cache[xf]
        comp.props[var_prop] = xf
        res = solve_circuit(cir)
        if not res.ok:
            cache[xf] = (None, None)
            return None, None
        if reject_if_overcurrent and any(v == "source_overcurrent" for v in res.comp_flags.values()):
            cache[xf] = (None, None)
            return None, None
        mv = _goal_measure(res, cir, measure)
        if mv is None:
            cache[xf] = (None, None)
            return None, None
        mvf = float(mv)
        if not math.isfinite(mvf):
            cache[xf] = (None, None)
            return None, None
        err = float(mvf - target)
        if not math.isfinite(err):
            cache[xf] = (None, None)
            return None, None
        cache[xf] = (err, mvf)
        return err, mvf

    e_lo, m_lo = eval_err(lo)
    e_hi, m_hi = eval_err(hi)

    if method == "auto" and (e_lo is None or e_hi is None):
        mid0 = 0.5 * (lo + hi)
        e_mid, m_mid = eval_err(mid0)
        if e_mid is not None and m_mid is not None:
            if e_lo is None:
                lo, e_lo, m_lo = mid0, e_mid, m_mid
            elif e_hi is None:
                hi, e_hi, m_hi = mid0, e_mid, m_mid

    if e_lo is None or e_hi is None:
        comp.props[var_prop] = prev
        return GoalSeekResult(ok=False, message="evaluation failed at bounds")

    out.history.append((float(lo), float(m_lo)))
    out.history.append((float(hi), float(m_hi)))

    def is_done(err: float, achieved: float) -> bool:
        tol = max(tol_abs, tol_rel * max(1.0, abs(target), abs(achieved)))
        return abs(err) <= tol

    bracketed = (e_lo == 0.0) or (e_hi == 0.0) or (e_lo < 0.0 < e_hi) or (e_hi < 0.0 < e_lo)

    if method == "auto" and not bracketed:
        lo0, hi0 = float(lo), float(hi)
        e_lo0, e_hi0 = float(e_lo), float(e_hi)
        m_lo0, m_hi0 = float(m_lo), float(m_hi)

        lo2, hi2 = float(lo0), float(hi0)
        for _ in range(12):
            if (e_lo0 == 0.0) or (e_hi0 == 0.0) or (e_lo0 < 0.0 < e_hi0) or (e_hi0 < 0.0 < e_lo0):
                lo, hi = float(lo2), float(hi2)
                e_lo, e_hi = float(e_lo0), float(e_hi0)
                m_lo, m_hi = float(m_lo0), float(m_hi0)
                bracketed = True
                break

            if lo2 > 0.0 and hi2 > 0.0 and str(var_prop).upper() == "R":
                lo2 = max(lo2 / 10.0, 1e-12)
                hi2 = hi2 * 10.0
            else:
                c = 0.5 * (lo2 + hi2)
                w = (hi2 - lo2)
                if abs(w) < 1e-15:
                    w = max(abs(c), 1.0)
                lo2 = c - 2.0 * w
                hi2 = c + 2.0 * w

            e_lo_t, m_lo_t = eval_err(lo2)
            e_hi_t, m_hi_t = eval_err(hi2)
            if e_lo_t is not None and m_lo_t is not None:
                e_lo0, m_lo0 = float(e_lo_t), float(m_lo_t)
            if e_hi_t is not None and m_hi_t is not None:
                e_hi0, m_hi0 = float(e_hi_t), float(m_hi_t)

        if not bracketed:
            lo, hi = float(lo0), float(hi0)
            e_lo, e_hi = float(e_lo), float(e_hi)
            m_lo, m_hi = float(m_lo), float(m_hi)

    use_bisect = (method in ("auto", "bisect")) and bracketed

    x0, x1 = float(lo), float(hi)
    y0, y1 = float(e_lo), float(e_hi)
    m0, m1 = float(m_lo), float(m_hi)
    a, b = lo, hi
    fa, fb = e_lo, e_hi
    best_x = float(lo)
    best_m = float(m_lo)
    best_err = float(e_lo)

    fail_reason = "failed"

    for it in range(int(max_iter)):
        out.iterations = it + 1
        if abs(y0) < abs(best_err):
            best_x, best_m, best_err = float(x0), float(m0), float(y0)
        if abs(y1) < abs(best_err):
            best_x, best_m, best_err = float(x1), float(m1), float(y1)

        if use_bisect:
            mid = 0.5 * (a + b)
            fm, mm = eval_err(mid)
            if fm is None or mm is None:
                fail_reason = "evaluation failed during bisection"
                break
            out.history.append((float(mid), float(mm)))
            if abs(fm) < abs(best_err):
                best_x, best_m, best_err = float(mid), float(mm), float(fm)
            if is_done(fm, mm):
                out.ok = True
                out.value = float(mid)
                out.achieved = float(mm)
                out.error = float(fm)
                out.message = "ok"
                return out
            if fa == 0.0:
                a = mid
                fa = fm
            elif fb == 0.0:
                b = mid
                fb = fm
            elif (fa < 0.0 and fm > 0.0) or (fa > 0.0 and fm < 0.0):
                b = mid
                fb = fm
            else:
                a = mid
                fa = fm
            continue

        if (y1 - y0) == 0.0:
            fail_reason = "secant slope is zero"
            break
        x2 = x1 - y1 * (x1 - x0) / (y1 - y0)
        if x2 < lo:
            x2 = lo
        if x2 > hi:
            x2 = hi
        if abs(x2 - x1) <= max(1e-15, 1e-12 * max(1.0, abs(x1))):
            x2 = 0.5 * (x0 + x1)
        y2, m2 = eval_err(x2)
        if y2 is None or m2 is None:
            fail_reason = "evaluation failed during secant"
            break
        out.history.append((float(x2), float(m2)))
        if abs(y2) < abs(best_err):
            best_x, best_m, best_err = float(x2), float(m2), float(y2)
        if is_done(y2, m2):
            out.ok = True
            out.value = float(x2)
            out.achieved = float(m2)
            out.error = float(y2)
            out.message = "ok"
            return out
        x0, y0, m0 = x1, y1, m1
        x1, y1, m1 = float(x2), float(y2), float(m2)

    comp.props[var_prop] = prev
    out.ok = False
    out.value = float(best_x)
    out.achieved = float(best_m if best_m is not None else 0.0)
    out.error = float(best_err)
    if method == "auto" and not bracketed:
        out.message = "failed: not bracketed"
    else:
        out.message = fail_reason
    return out

def format_si(x: float, unit: str) -> str:
    ax = abs(x)
    if ax >= 1e3:
        return f"{x/1e3:.3g}k{unit}"
    if ax >= 1:
        return f"{x:.3g}{unit}"
    if ax >= 1e-3:
        return f"{x*1e3:.3g}m{unit}"
    if ax >= 1e-6:
        return f"{x*1e6:.3g}μ{unit}"
    return f"{x:.3g}{unit}"

def comp_symbol(c: Component) -> str:
    t = c.ctype
    return {
        "socket": "⎍",
        "wire": "·",
        "resistor": "Ω",
        "bulb": "💡",
        "rheostat": "≋",
        "switch_spst": "⏻",
        "switch_spdt": "⇄",
        "switch_sp3t": "⤨",
        "switch_dpst": "⏻",
        "switch_dpdt": "⏻",
        "button_momentary": "⏺",
        "ammeter": "A",
        "voltmeter": "V",
        "galvanometer": "G",
    }.get(t, "?")
