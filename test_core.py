#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for core circuit functionality
"""

from core import Circuit, solve_circuit, format_si, goal_seek_parameter

def test_simple_circuit():
    """Test a simple voltage divider circuit"""
    print("Testing simple circuit...")
    
    cir = Circuit()
    cir.add("socket", (0, 0), (0, 10), V=10.0, Iwarn=5.0)
    cir.add("resistor", (0, 0), (10, 0), R=100.0)
    cir.add("resistor", (10, 0), (10, 10), R=100.0)
    cir.add("wire", (10, 10), (0, 10))
    
    result = solve_circuit(cir)
    
    if result.ok:
        print("✓ Circuit solved successfully")
        print(f"  Node voltages: {len(result.node_v)} nodes")
        print(f"  Component currents: {len(result.comp_i)} components")
        
        for cid, current in result.comp_i.items():
            comp = cir.components[cid]
            print(f"  {comp.ctype}: I = {format_si(current, 'A')}")
    else:
        print("✗ Circuit solve failed")
        if result.warnings:
            for w in result.warnings:
                print(f"  Warning: {w}")
    
    return result.ok

def test_goal_seek_resistor():
    """Goal-seek an unknown resistor so that the circuit current hits a target"""
    print("\nTesting goal seek (solve R for target I)...")

    cir = Circuit()
    sid = cir.add("socket", (0, 0), (0, 6), V=10.0, Iwarn=5.0)
    rid_fixed = cir.add("resistor", (0, 0), (6, 0), R=100.0)
    rid_var = cir.add("resistor", (6, 0), (12, 0), R=50.0)
    cir.add("wire", (12, 0), (12, 6))
    cir.add("wire", (12, 6), (0, 6))

    target_I = 0.05
    gs = goal_seek_parameter(
        cir,
        var_cid=rid_var,
        var_prop="R",
        target=target_I,
        measure={"kind": "comp", "cid": sid, "field": "Iab", "abs": True},
        lo=1.0,
        hi=1000.0,
        tol_rel=1e-4,
        max_iter=80,
    )

    if not gs.ok:
        print(f"✗ Goal seek failed: {gs.message} | best={gs.value} achieved={gs.achieved}")
        return False

    solved_R = float(cir.components[rid_var].props.get("R", 0.0))
    expected_R = (10.0 / target_I) - 100.0
    err = abs(solved_R - expected_R) / max(1e-9, abs(expected_R))
    if err < 1e-2:
        print(f"✓ Solved R≈{solved_R:.6g}Ω (expected≈{expected_R:.6g}Ω)")
        return True
    print(f"✗ R mismatch: got {solved_R:.6g}Ω expected {expected_R:.6g}Ω")
    return False

def test_series_circuit():
    """Test series resistors"""
    print("\nTesting series circuit...")
    
    cir = Circuit()
    cir.add("socket", (0, 0), (0, 6), V=12.0, Iwarn=5.0)
    cir.add("resistor", (0, 0), (6, 0), R=10.0)
    cir.add("resistor", (6, 0), (12, 0), R=20.0)
    cir.add("resistor", (12, 0), (12, 6), R=30.0)
    cir.add("wire", (12, 6), (0, 6))
    
    result = solve_circuit(cir)
    
    if result.ok:
        print("✓ Series circuit solved")
        total_current = None
        for cid, current in result.comp_i.items():
            comp = cir.components[cid]
            if comp.ctype == "socket":
                total_current = abs(current)
                print(f"  Total current: {format_si(total_current, 'A')}")
                expected = 12.0 / (10.0 + 20.0 + 30.0)
                error = abs(total_current - expected) / expected
                if error < 0.01:
                    print(f"  ✓ Current matches expected: {format_si(expected, 'A')}")
                else:
                    print(f"  ✗ Current mismatch: expected {format_si(expected, 'A')}")
    else:
        print("✗ Series circuit solve failed")
    
    return result.ok

def test_bulb():
    """Test bulb component"""
    print("\nTesting bulb circuit...")
    
    cir = Circuit()
    cir.add("socket", (0, 0), (0, 6), V=6.0, Iwarn=5.0)
    cir.add("bulb", (0, 0), (6, 0), Vr=6.0, Wr=3.0)
    cir.add("wire", (6, 0), (6, 6))
    cir.add("wire", (6, 6), (0, 6))
    
    result = solve_circuit(cir)
    
    if result.ok:
        print("✓ Bulb circuit solved")
        for cid, current in result.comp_i.items():
            comp = cir.components[cid]
            if comp.ctype == "bulb":
                power = abs(current) * 6.0
                print(f"  Bulb current: {format_si(current, 'A')}")
                print(f"  Bulb power: {format_si(power, 'W')}")
    else:
        print("✗ Bulb circuit solve failed")
    
    return result.ok

if __name__ == "__main__":
    print("=" * 50)
    print("Circuit Simulator Core Tests")
    print("=" * 50)
    
    tests = [
        test_simple_circuit,
        test_series_circuit,
        test_bulb,
        test_goal_seek_resistor,
    ]
    
    passed = sum(1 for test in tests if test())
    total = len(tests)
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)
