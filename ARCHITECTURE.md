# Circuit Simulator Architecture

## Overview

The circuit simulator has been rewritten with a clean separation between core logic and user interfaces, following the **Model-View** pattern.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                    (Launcher/Router)                         │
│  - Parses command-line arguments                            │
│  - Routes to TUI or GUI                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│   tui.py     │  │   gui.py     │
│  (Terminal)  │  │ (Graphical)  │
│              │  │              │
│ - Curses UI  │  │ - Tkinter    │
│ - Keyboard   │  │ - Canvas     │
│ - TCP Server │  │ - Mouse      │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
        ┌──────────────┐
        │   core.py    │
        │   (Model)    │
        │              │
        │ - Circuit    │
        │ - Component  │
        │ - Solver     │
        │ - MNA        │
        └──────────────┘
```

## Module Responsibilities

### `core.py` - Pure Logic Layer
**No UI dependencies**

- **Data Models**:
  - `Component`: Circuit component with type, endpoints, properties
  - `Circuit`: Collection of components with add/delete/find operations
  - `SolveResult`: Analysis results with voltages, currents, warnings

- **Solver**:
  - `solve_circuit()`: Modified Nodal Analysis (MNA) implementation
  - `solve_linear()`: Gaussian elimination with partial pivoting
  - `effective_resistance()`: Component resistance calculation

- **Utilities**:
  - `format_si()`: SI unit formatting (mA, kΩ, etc.)
  - `comp_symbol()`: Component symbol lookup
  - `bulb_resistance()`: Bulb model calculation

### `tui.py` - Terminal User Interface
**Curses-based, keyboard-driven**

- **Features**:
  - Grid-based canvas with ASCII art rendering
  - Keyboard navigation (hjkl/arrows)
  - Modal editing (navigate/place/wire modes)
  - Component inspector with detailed readings
  - TCP socket server for remote control (port 9999)

- **Key Classes**:
  - `TUIApp`: Main application controller
  - `SocketServer`: TCP command server thread

- **Rendering**:
  - Grid dots for alignment
  - Line drawing for connections
  - Unicode symbols for components
  - Status bar and help text

### `gui.py` - Graphical User Interface
**Tkinter + Canvas, mouse-driven**

- **Features**:
  - Component palette (left panel)
  - Interactive canvas with grid
  - Mouse-based interaction
  - Visual feedback (bulb brightness, colors)
  - Property editor dialogs
  - Real-time meter readings

- **Key Classes**:
  - `CircuitGUI`: Main application window
  - `ComponentEditDialog`: Property editor popup

- **Visual Elements**:
  - Grid background
  - Color-coded components (selected/hover)
  - Animated bulb brightness based on voltage
  - Inline meter readings
  - Context menus

### `main.py` - Launcher
**Entry point with argument parsing**

- Routes to TUI or GUI based on command-line flags
- Default: GUI
- `--tui`: Terminal interface
- `--gui`: Graphical interface

## Data Flow

### Circuit Editing Flow
```
User Action (TUI/GUI)
    ↓
Circuit.add/delete/modify
    ↓
solve_circuit(cir)
    ↓
SolveResult
    ↓
UI Update (render/redraw)
```

### Solver Flow
```
Circuit Components
    ↓
Expand SPDT switches
    ↓
Build node list & index
    ↓
Stamp conductances (G = 1/R)
    ↓
Stamp voltage sources
    ↓
Solve linear system (Ax = b)
    ↓
Extract node voltages
    ↓
Calculate component currents
    ↓
Detect warnings (short/open)
    ↓
Return SolveResult
```

## Component Models

| Component | Model | Parameters |
|-----------|-------|------------|
| Wire | R ≈ 0 | None |
| Resistor | R = constant | R (Ω) |
| Bulb | R = V²/P | Vr (V), Wr (W) |
| Rheostat | R = adjustable | R (Ω) |
| Socket | V = constant | V (V), Iwarn (A) |
| Switch SPST | R = 0 or ∞ | state (0/1) |
| Switch SPDT | Connects a-b or a-c | throw (0/1) |
| Ammeter | R = small | Rin (Ω) |
| Voltmeter | R = large | Rin (Ω) |
| Galvanometer | R = medium | Rcoil (Ω), Ifs (A) |

## File Format

Circuits are saved as JSON:

```json
{
  "components": [
    {
      "cid": "unique-hex-id",
      "ctype": "resistor",
      "a": [x1, y1],
      "b": [x2, y2],
      "props": {
        "R": 100.0
      },
      "meta": {}
    }
  ]
}
```

## Benefits of This Architecture

1. **Separation of Concerns**: Core logic is independent of UI
2. **Testability**: Core can be tested without UI
3. **Flexibility**: Easy to add new UI (web, mobile, etc.)
4. **Maintainability**: Changes to UI don't affect solver
5. **Reusability**: Core can be used as a library

## Future Extensions

Possible additions that maintain this architecture:

- **Web UI**: Add `web.py` using Flask/FastAPI + JavaScript
- **CLI**: Add `cli.py` for batch processing
- **API**: Expose core as REST API
- **Plugins**: Component plugin system in core
- **Advanced Analysis**: AC analysis, transient simulation
