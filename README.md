# Circuit Simulator

Educational DC circuit simulator with multiple interfaces - Terminal UI (TUI) and Graphical UI (GUI).

## Features

- **DC Steady-State Analysis** using Modified Nodal Analysis (MNA)
- **Multiple Components**:
  - Socket (Voltage Source)
  - Wire
  - Resistor
  - Bulb (with rated voltage/power)
  - Rheostat (variable resistor)
  - Switch (SPST/SPDT)
  - Ammeter
  - Voltmeter
  - Galvanometer
- **Two User Interfaces**:
  - **TUI**: Terminal-based interface using curses
  - **GUI**: Modern graphical interface using tkinter + canvas
- **Circuit Solver**: Automatic DC analysis with short/open circuit detection
- **Save/Load**: JSON-based circuit persistence

## Architecture

The project is structured with clean separation of concerns:

```
circuit/
├── core.py      # Core circuit logic, solver, data models (no UI dependencies)
├── tui.py       # Terminal User Interface (curses-based)
├── gui.py       # Graphical User Interface (tkinter + canvas)
├── main.py      # Launcher to choose between TUI/GUI
└── README.md    # This file
```

### Core Module (`core.py`)
- Pure logic implementation
- Circuit data structures (`Component`, `Circuit`)
- MNA solver (`solve_circuit`)
- Linear algebra solver (Gaussian elimination)
- No UI dependencies

### TUI Module (`tui.py`)
- Curses-based terminal interface
- Keyboard-driven navigation
- TCP socket server for remote control (port 9999)
- Grid-based component placement

### GUI Module (`gui.py`)
- Tkinter + Canvas graphical interface
- Mouse-driven interaction
- Component palette
- Visual feedback (bulb brightness, etc.)
- Property editor dialogs

## Usage

### Launch GUI (default)
```bash
python main.py
# or explicitly
python main.py --gui
```

### Launch TUI
```bash
python main.py --tui
```

## GUI Controls

- **Left Panel**: Component palette - click to select component type
- **Canvas**: 
  - Left-click: Select/place component
  - Right-click: Context menu (edit/delete)
  - Double-click: Edit component properties
- **Actions**:
  - Solve Circuit: Re-run simulation
  - Save/Load: Persist circuit to `circuit.json`
  - Clear All: Remove all components

## TUI Controls

- **Navigation**: Arrow keys or `h`/`j`/`k`/`l`
- **Modes**: `Tab` to cycle through Navigate/Place/Wire modes
- **Components**: Number keys to select component type
  - `1`: Socket (power source)
  - `2`: Wire
  - `3`: Resistor
  - `4`: Bulb
  - `5`: Rheostat
  - `6`: Switch SPST
  - `7`: Switch SPDT
  - `8`: Ammeter
  - `9`: Voltmeter
  - `0`: Galvanometer
- **Actions**:
  - `Enter`: Place component (in Place mode) or set wire endpoint (in Wire mode)
  - `w`: Toggle wire mode
  - `e`: Edit selected component
  - `d`: Delete component at cursor
  - `Space`: Toggle switch state
  - `i`: Toggle detailed information
  - `s`: Save circuit
  - `l`: Load circuit
  - `r`: Re-solve circuit
  - `q`: Quit

## Circuit Analysis

The simulator uses Modified Nodal Analysis (MNA) to solve DC circuits:

1. **Node Voltage Method**: Solves for voltages at each node
2. **KCL/KVL**: Enforces Kirchhoff's laws
3. **Component Models**:
   - Resistors: Ohm's law (V = IR)
   - Bulbs: Simplified model (R = V²/P)
   - Voltage sources: Ideal voltage constraint
   - Meters: Modeled with internal resistance
   - Switches: Open (infinite R) or closed (near-zero R)

## File Format

Circuits are saved as JSON:

```json
{
  "components": [
    {
      "cid": "unique-id",
      "ctype": "resistor",
      "a": [x1, y1],
      "b": [x2, y2],
      "props": {"R": 100.0},
      "meta": {}
    }
  ]
}
```

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- curses (Unix/Linux/macOS - included; Windows requires windows-curses)

## Example Circuits

The simulator starts with a simple example circuit:
- 6V voltage source
- 20Ω resistor
- Wires completing the circuit

You can build more complex circuits with:
- Series/parallel resistor networks
- Multiple voltage sources
- Measurement instruments (ammeters, voltmeters)
- Switches for circuit control

## Educational Use

This simulator is designed for teaching:
- Basic circuit concepts
- Ohm's law and Kirchhoff's laws
- Series and parallel circuits
- Circuit measurement techniques
- Component behavior

## License

Educational use - feel free to modify and extend!
