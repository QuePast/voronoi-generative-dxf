import io
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
import ezdxf


def _build_geometry(params):
    space_between_cells = float(params.get("space_between_cells", 10))
    outline_margin = float(params.get("outline_margin", 10))
    num_seeds = int(params.get("num_seeds", 20))
    triangle_size = float(params.get("triangle_size", 476))
    corner_radius = float(params.get("corner_radius", 10))
    simplification_tolerance = float(params.get("simplification_tolerance", 0.1))
    logo_size = float(params.get("logo_size", 130))
    logo_x = float(params.get("logo_x", 74.5))
    logo_y = float(params.get("logo_y", 74.5))
    logo_radius = float(params.get("logo_radius", 5))

    triangle = Polygon([(0, 0), (triangle_size, 0), (0, triangle_size)])
    sharp_logo = Polygon([
        (logo_x, logo_y),
        (logo_x + logo_size, logo_y),
        (logo_x + logo_size, logo_y + logo_size),
        (logo_x, logo_y + logo_size),
    ])
    logo_shape = sharp_logo.buffer(-logo_radius).buffer(logo_radius, join_style=1)

    base_shrink = space_between_cells / 2.0
    inner_triangle = triangle.buffer(-(outline_margin - base_shrink), join_style=2)
    logo_cutout = logo_shape.buffer(-base_shrink, join_style=1)
    valid_area = inner_triangle.difference(logo_cutout)

    np.random.seed(42)
    forced_corners = [
        Point(30, 30),
        Point(triangle_size - 50, 20),
        Point(20, triangle_size - 50),
    ]
    points = [[fc.x, fc.y] for fc in forced_corners if valid_area.contains(fc)]

    attempts = 0
    min_dist = max(20, triangle_size / num_seeds * 0.8)
    while len(points) < num_seeds and attempts < 10000:
        p = Point(np.random.rand() * triangle_size, np.random.rand() * triangle_size)
        if valid_area.contains(p):
            if all(np.hypot(p.x - pt[0], p.y - pt[1]) > min_dist for pt in points):
                points.append([p.x, p.y])
        attempts += 1

    dummy_points = [[-2000, -2000], [2000, -2000], [2000, 2000], [-2000, 2000]]
    all_points = np.vstack([points, dummy_points])
    vor = Voronoi(all_points)

    cells = []
    for i, region_idx in enumerate(vor.point_region[: len(points)]):
        region = vor.regions[region_idx]
        if -1 in region or len(region) == 0:
            continue
        verts = [vor.vertices[v] for v in region]
        cell_poly = Polygon(verts)
        clipped = cell_poly.intersection(valid_area)
        if clipped.is_empty:
            continue

        geoms = (
            list(clipped.geoms)
            if isinstance(clipped, MultiPolygon)
            else [clipped]
        )
        for g in geoms:
            if g.area < 1:
                continue
            if corner_radius > 0:
                g = g.buffer(-corner_radius).buffer(corner_radius, join_style=1)
            if g.is_empty:
                continue
            g = g.simplify(simplification_tolerance, preserve_topology=True)
            if not g.is_empty and g.geom_type == "Polygon":
                cells.append(g)

    return triangle, logo_shape, valid_area, cells


def _poly_to_coords(poly):
    coords = list(poly.exterior.coords)
    return [[round(x, 4), round(y, 4)] for x, y in coords]


def generate_preview_geometry(params):
    triangle, logo_shape, valid_area, cells = _build_geometry(params)

    shapes = []

    # Triangle outline
    shapes.append({
        "type": "outline",
        "coords": _poly_to_coords(triangle),
    })

    # Logo box
    shapes.append({
        "type": "logo",
        "coords": _poly_to_coords(logo_shape),
    })

    # Voronoi cells
    for cell in cells:
        shapes.append({
            "type": "cell",
            "coords": _poly_to_coords(cell),
        })

    return shapes


def generate_voronoi(params):
    triangle, logo_shape, valid_area, cells = _build_geometry(params)

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Triangle outline layer
    doc.layers.add("OUTLINE", color=7)
    doc.layers.add("LOGO", color=3)
    doc.layers.add("CELLS", color=5)

    tri_coords = list(triangle.exterior.coords)
    msp.add_lwpolyline(tri_coords, close=True, dxfattribs={"layer": "OUTLINE"})

    logo_coords = list(logo_shape.exterior.coords)
    msp.add_lwpolyline(logo_coords, close=True, dxfattribs={"layer": "LOGO"})

    for cell in cells:
        coords = list(cell.exterior.coords)
        msp.add_lwpolyline(coords, close=True, dxfattribs={"layer": "CELLS"})

    # ezdxf writes text; wrap in StringIO then encode
    text_buf = io.StringIO()
    doc.write(text_buf)
    return text_buf.getvalue().encode("utf-8")
