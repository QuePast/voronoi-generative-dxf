# Voronoi DXF Configurator

A browser-based parametric Voronoi diagram generator that exports production-ready DXF files for laser cutting, CNC machining, and CAD import (Creo, SolidWorks, AutoCAD).

![screenshot](screenshot.png)

---

## Install & Run

```bash
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Parameters

| Parameter | Range | Default | Description |
|---|---|---|---|
| Seeds | 5 – 60 | 20 | Number of Voronoi seed points |
| Cell Gap | 2 – 30 mm | 10 | Space between adjacent cells (kerf compensation) |
| Outline Margin | 5 – 40 mm | 10 | Inset from the triangle boundary |
| Triangle Size | 200 – 700 mm | 476 | Right-triangle leg length |
| Corner Radius | 0 – 30 mm | 10 | Rounding on cell vertices |
| Simplify Tolerance | 0.05 – 2.0 | 0.10 | Douglas-Peucker tolerance for polyline simplification |

---

## Tech Stack

- **Python** — core language
- **Flask** — lightweight HTTP server (preview + DXF download endpoints)
- **NumPy** — random seed placement, distance calculations
- **SciPy** — Voronoi tessellation (`scipy.spatial.Voronoi`)
- **Shapely** — 2D geometry: clipping, buffering, boolean ops, simplification
- **ezdxf** — DXF R2010 file generation (layers: OUTLINE, LOGO, CELLS)
- **Vanilla JS + Canvas** — zero-dependency browser UI with live preview

---

## What is DXF used for?

DXF (Drawing Exchange Format) is the standard interchange format for 2D CAD geometry.  
The exported file contains three named layers that map directly to machine operations:

- **OUTLINE** — outer triangle boundary (cut line)
- **LOGO** — logo cutout pocket
- **CELLS** — individual Voronoi cell profiles (engrave or cut through)

Compatible with laser cutters (LightBurn, RDWorks), CNC routers (Mach3, LinuxCNC), and parametric CAD tools (PTC Creo, SolidWorks, Fusion 360).
