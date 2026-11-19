"""Analytic front supports and mating recesses of the snap-hinged enclosure.

Only dimensional primitives are evaluated. There is no reference asset or mesh
lookup. The four supports extend 0.02 mm into the main shell to avoid an internal
zero-valued membrane when implicit solids are united before extraction.
"""

from __future__ import annotations

import math


def front_fitting_dimensions(p):
    """Return the common assembly frame and the measured primitive dimensions."""
    from .rugged_geometry import rugged_dimensions

    q = rugged_dimensions(p)
    return {
        "centers": q["fitting_centers"],
        "front": -q["depth"] / 2,
        "base_height": q["base_height"],
        "lid_height": q["lid_height"],
        "clearance": q["clearance"],
        "outer_half_span": 20.75,
        "inner_half_span": 12.75,
        "projection": 8.0,
        "corner_radius": 2.0,
        "cam_center_z": q["base_height"] - 8.19694,
        "cam_socket_radius": 5 + q["clearance"],
        "cam_socket_half_height": 2.96313,
        "cam_socket_chamfer": 0.9,
        "ball_radius": 3.75 + q["clearance"],
        "ball_center_z": q["base_height"] + q["lid_height"] - 10,
    }


def _round_intersection(a, b, cosine, radius):
    """Convex rolling-circle blend between two oriented surface constraints.

    For planes this is the exact cylindrical fillet, including their actual
    included angle. The curved profile branches provide their local unit normal.
    """
    from .mesh_generator import np

    dot = np.clip(cosine, -0.999, 0.999)
    u, v = a + radius, b + radius
    first = (u - dot * v) / (1 - dot * dot)
    second = (v - dot * u) / (1 - dot * dot)
    distance = np.sqrt(
        np.maximum((u * u - 2 * dot * u * v + v * v) / (1 - dot * dot), 0)
    )
    return np.where((first >= 0) & (second >= 0), distance - radius, np.maximum(a, b))


def _front_profile_distance(s, z, h, lid_height, part):
    """Exact distance/normal of the tangent half-line, R10 arc and front ray.

    The half-line and bounded arc are projected independently and the closest
    point determines both distance and normal. The arc continues tangentially
    into the vertical front ray, so endpoint normals remain continuous on both
    sides of the front face. Using a clipped full-circle field
    would introduce an internal medial-plane switch unrelated to this profile,
    making its downstream fillet discontinuous.
    """
    from .mesh_generator import np

    if part == "base":
        center_z = h - 5.4921894
        theta_min, theta_max = -math.atan(1 / 1.25), 0.0
        tangent_theta = theta_min
        slope = 1.25
        direction = -1.0
    else:
        center_z = h + lid_height - (30 - 10 * math.sqrt(3))
        theta_min, theta_max = 0.0, math.pi / 6
        tangent_theta = theta_max
        slope = -math.sqrt(3)
        direction = 1.0
    tangent_s = -2 + 10 * math.cos(tangent_theta)
    tangent_z = center_z + 10 * math.sin(tangent_theta)
    norm = math.sqrt(1 + slope * slope)
    ts, tz = 1 / norm, slope / norm
    parameter = np.minimum((s - tangent_s) * ts + (z - tangent_z) * tz, 0)
    line_s, line_z = tangent_s + parameter * ts, tangent_z + parameter * tz
    angle = np.clip(np.arctan2(z - center_z, s + 2), theta_min, theta_max)
    arc_s, arc_z = -2 + 10 * np.cos(angle), center_z + 10 * np.sin(angle)
    line_squared = (s - line_s) ** 2 + (z - line_z) ** 2
    arc_squared = (s - arc_s) ** 2 + (z - arc_z) ** 2
    use_arc = arc_squared <= line_squared
    nearest_s = np.where(use_arc, arc_s, line_s)
    nearest_z = np.where(use_arc, arc_z, line_z)
    squared = np.minimum(line_squared, arc_squared)
    # At theta=0 the bounded arc meets the same vertical front face already
    # present in the XY constraints. Including this C1 continuation prevents a
    # signed-distance/normal flip immediately outside S=8.
    ray_z = center_z + direction * np.minimum(direction * (z - center_z), 0)
    ray_squared = (s - 8) ** 2 + (z - ray_z) ** 2
    use_ray = ray_squared <= squared
    nearest_s = np.where(use_ray, 8.0, nearest_s)
    nearest_z = np.where(use_ray, ray_z, nearest_z)
    distance = np.sqrt(np.minimum(squared, ray_squared))
    graph = np.where(
        s <= tangent_s,
        tangent_z + slope * (s - tangent_s),
        center_z + direction * np.sqrt(np.maximum(100 - (s + 2) ** 2, 0)),
    )
    outside = (s > 8) | (direction * (z - graph) > 0)
    sign = np.where(outside, 1.0, -1.0)
    fallback_normal = np.where(
        use_arc, np.cos(angle), (slope if part == "base" else -slope) / norm
    )
    fallback_normal = np.where(use_ray, 1.0, fallback_normal)
    normal_s = np.where(
        distance > 1e-12,
        sign * (s - nearest_s) / np.maximum(distance, 1e-12),
        fallback_normal,
    )
    return sign * distance, normal_s


def _raw_front_field(p, part):
    from .mesh_generator import np
    from .rugged_geometry import rugged_outer_body_y

    if part not in ("base", "lid"):
        raise ValueError("Somente base/tampa / only base/lid have front supports.")
    q = front_fitting_dimensions(p)
    h, lh = q["base_height"], q["lid_height"]
    cos15, sin15 = math.cos(math.radians(15)), math.sin(math.radians(15))
    tan15 = math.tan(math.radians(15))
    tan50, cos50 = math.tan(math.radians(50)), math.cos(math.radians(50))
    outer_start = 0.5358983848622456

    def field(points):
        x, y, z = np.asarray(points, dtype=float).T
        s = q["front"] - y
        # The lid's attachment face recedes along its outer chamfer. A fixed
        # global-Y cut would disconnect the upper support from that face.
        attachment = y - rugged_outer_body_y(p, part, 0, z) - 0.02
        results = []
        for center in q["centers"]:
            a = np.abs(x - center)
            taper = (a - 20.75 + tan15 * (s - outer_start)) * cos15
            # Exact R2 fillet of the tapered side and the front plane. Its
            # tangent starts at 15 degrees, rather than at S=6 for every X.
            outer = _round_intersection(taper, s - 8, sin15, 2)
            outer = np.maximum(outer, a - 20.75)
            rho = np.hypot(s - 3, z - h - 4)
            if part == "base":
                inner = np.minimum(12.75 - a, (rho + 6.36396103 - tan50 * a) * cos50)
                bottom, normal = _front_profile_distance(s, z, h, lh, part)
                rounded = _round_intersection(taper, bottom, sin15 * normal, 2)
                vertical = z - h + np.maximum(s - 7, 0)
            else:
                # Only the lower branch of the complementary cone belongs to
                # the seam-side horn. Its upper branch would fill the opening
                # between the two journal supports near the lid roof.
                inner = np.minimum(
                    12.75 - a,
                    np.maximum((20.36396103 - tan50 * a - rho) * cos50, z - h - 4),
                )
                top, normal = _front_profile_distance(s, z, h, lh, part)
                rounded = _round_intersection(taper, top, sin15 * normal, 2)
                vertical = np.maximum(h - z + np.maximum(s - 7, 0), z - h - lh)
            results.append(
                np.maximum.reduce((outer, rounded, inner, vertical, attachment))
            )
        return np.minimum.reduce(results)

    return field


def front_socket_field(p, part):
    """Return negative INSIDE the cavities, for subtraction AFTER shell union.

    Only the outward spherical/conical caps cut the supports. The corresponding
    full sphere/cylinder must not drill the enclosure wall behind the latch gap.
    Axial bounding-box overlap alone does not establish elastic contact.
    """
    from .mesh_generator import np
    from .rugged_geometry import rugged_outer_body_y

    if part not in ("base", "lid"):
        raise ValueError("Somente base/tampa / only base/lid have front sockets.")
    q = front_fitting_dimensions(p)

    def field(points):
        x, y, z = np.asarray(points, dtype=float).T
        values = []
        for center in q["centers"]:
            if part == "base":
                radius = np.hypot(np.abs(x - center) - 8.5, y - q["front"] + 3)
                cap = np.abs(z - q["cam_center_z"])
                r, hc, chamfer = (
                    q["cam_socket_radius"],
                    q["cam_socket_half_height"],
                    q["cam_socket_chamfer"],
                )
                cavity = np.maximum.reduce(
                    (radius - r, cap - hc, radius + cap - r - hc + chamfer)
                )
            else:
                cavity = (
                    np.sqrt(
                        (np.abs(x - center) - 10.25) ** 2
                        + (y - q["front"] + 3) ** 2
                        + (z - q["ball_center_z"]) ** 2
                    )
                    - q["ball_radius"]
                )
            # Extend the artificial clipping plane by 2 micrometres only into
            # empty space outside the shell. At an exactly coincident mouth
            # both raw support and clipped cavity would otherwise be zero on a
            # disk with void on BOTH sides, producing an internal iso membrane.
            # The physical spherical/conical surfaces and radii do not move.
            gap = rugged_outer_body_y(p, part, 0, z) - y
            extension = np.minimum(0.002, np.maximum(gap, 0.0))
            values.append(np.maximum.reduce((cavity,
                          12.75 - np.abs(x - center) - extension,
                          y - rugged_outer_body_y(p, part, 0, z))))
        return np.minimum.reduce(values)

    return field


def front_fittings_field(p, part):
    """Return four connected-to-shell supports, with their own recesses cut."""
    from .mesh_generator import np

    raw = _raw_front_field(p, part)
    cuts = front_socket_field(p, part)
    return lambda points: np.maximum(raw(points), -cuts(points))


def front_strip_bounds(p, part, z):
    """Return the exact S interval of one support's YZ chart at height Z.

    S is positive towards the front: Y=front-S. Heights belong between the
    first/last ``front_z_events`` values. Clamping only extends endpoint bounds
    continuously for numerical queries; it does not authorize extra material
    beyond those heights.
    """
    from .mesh_generator import np
    from .rugged_geometry import rugged_outer_body_y

    if part not in ("base", "lid"):
        raise ValueError("Use base/tampa / use base/lid.")
    q = front_fitting_dimensions(p)
    h, closed = q["base_height"], q["base_height"] + q["lid_height"]
    z = np.asarray(z, dtype=float)
    if not np.isfinite(z).all():
        raise ValueError("Altura não finita / non-finite chart height.")
    z = np.clip(z, h - 19 if part == "base" else h, h if part == "base" else closed)
    smin = q["front"] - rugged_outer_body_y(p, part, 0, z)
    if part == "base":
        center = h - 5.4921894
        tangent_z = center - 10 / math.sqrt(1 + 1.25**2)
        inverse = np.where(
            z <= tangent_z,
            (z - h + 19) / 1.25,
            np.where(
                z < center, -2 + np.sqrt(np.maximum(100 - (z - center) ** 2, 0)), 8
            ),
        )
        smax = np.minimum(np.minimum(8, inverse), h + 7 - z)
    else:
        center = closed - (30 - 10 * math.sqrt(3))
        inverse = np.where(
            z <= center,
            8,
            np.where(
                z <= center + 5,
                -2 + np.sqrt(np.maximum(100 - (z - center) ** 2, 0)),
                8 - 10 / math.sqrt(3) + (closed - z) / math.sqrt(3),
            ),
        )
        smax = np.minimum(np.minimum(8, inverse), 7 + z - h)
    return smin, np.maximum(smin, smax)


def _rounded_plane_limit(distance, cosine, radius=2.0):
    """Invert the rounded intersection for its monotonic plane constraint."""
    from .mesh_generator import np

    b = np.minimum(np.asarray(distance, dtype=float), 0)
    d = np.clip(cosine, -0.999, 0.999)
    v = b + radius
    curved = (
        d * v + np.sqrt(np.maximum((1 - d * d) * (radius * radius - v * v), 0)) - radius
    )
    return np.where(b <= -radius * (1 - d), 0, curved)


def front_interval(p, part, s, z):
    """Return inner/outer A bounds of one support, without a sampled mesh.

    A=abs(X-latch_center). Use S within ``front_strip_bounds``. Both surfaces
    share the SAME YZ chart, so their triangulations can be paired directly.
    Base recess caps retain their physical flat ends: for clearance above
    0.15 mm the one-sided inner bound has a real step at those cap heights.
    ``front_z_events`` includes them for adaptive or explicit cap treatment.
    """
    from .mesh_generator import np

    if part not in ("base", "lid"):
        raise ValueError("Use base/tampa / use base/lid.")
    q = front_fitting_dimensions(p)
    h, lh = q["base_height"], q["lid_height"]
    s, z = np.broadcast_arrays(np.asarray(s, dtype=float), np.asarray(z, dtype=float))
    if not (np.isfinite(s).all() and np.isfinite(z).all()):
        raise ValueError("Coordenada não finita / non-finite chart coordinate.")
    rho = np.hypot(s - 3, z - h - 4)
    slope = math.tan(math.radians(50))
    if part == "base":
        inner = np.minimum(12.75, (rho + 6.36396103) / slope)
        cap = np.abs(z - q["cam_center_z"])
        radius = np.minimum(
            q["cam_socket_radius"],
            q["cam_socket_radius"]
            + q["cam_socket_half_height"]
            - q["cam_socket_chamfer"]
            - cap,
        )
        squared = radius * radius - (s - 3) ** 2
        recess = np.where(
            (cap <= q["cam_socket_half_height"] + 1e-10) & (squared >= 0),
            8.5 + np.sqrt(np.maximum(squared, 0)),
            0,
        )
    else:
        horn = np.where(z <= h + 4, (20.36396103 - rho) / slope, 12.75)
        inner = np.minimum(12.75, horn)
        squared = q["ball_radius"] ** 2 - (s - 3) ** 2 - (z - q["ball_center_z"]) ** 2
        recess = 10.25 + np.sqrt(np.maximum(squared, 0))
    inner = np.maximum(inner, recess)
    profile, normal = _front_profile_distance(s, z, h, lh, part)
    sin15, cos15 = math.sin(math.radians(15)), math.cos(math.radians(15))
    limit = np.minimum(
        _rounded_plane_limit(s - 8, sin15),
        _rounded_plane_limit(profile, sin15 * normal),
    )
    outer = np.minimum(
        20.75,
        20.75 - math.tan(math.radians(15)) * (s - 0.5358983848622456) + limit / cos15,
    )
    return inner, outer


def front_z_events(p, part):
    """Physical height endpoints and constant-height crease/recess events."""
    from .mesh_generator import np

    if part not in ("base", "lid"):
        raise ValueError("Use base/tampa / use base/lid.")
    q = front_fitting_dimensions(p)
    h, lh = q["base_height"], q["lid_height"]
    if part == "base":
        low, high = h - 19, h
        center = h - 5.4921894
        horn_radius = math.tan(math.radians(50)) * 12.75 - 6.36396103
        values = [
            low,
            high,
            h - 1,
            center,
            center - 10 / math.sqrt(1 + 1.25**2),
            q["cam_center_z"],
            h + 4 - horn_radius,
            h + 4 - math.sqrt(horn_radius**2 - 9),
            h + 4 - math.sqrt(horn_radius**2 - 25),
        ]
        values.extend(
            q["cam_center_z"] + sign * (q["cam_socket_half_height"] - offset)
            for sign in (-1, 1)
            for offset in (0, q["cam_socket_chamfer"])
        )
    else:
        low, high = h, h + lh
        center = high - (30 - 10 * math.sqrt(3))
        mouth_radius = math.sqrt(q["ball_radius"] ** 2 - 2.5**2)
        horn_radius = 20.36396103 - math.tan(math.radians(50)) * 12.75
        values = [
            low,
            high,
            h + 1,
            h + 4,
            center,
            center + 5,
            q["ball_center_z"],
            q["ball_center_z"] - mouth_radius,
            q["ball_center_z"] + mouth_radius,
            h + 4 - math.sqrt(horn_radius**2 - 25),
        ]
    return sorted(set(float(np.clip(v, low, high)) for v in values))


def rugged_front_bounds(p, part):
    from .rugged_geometry import rugged_outer_body_y

    q = front_fitting_dimensions(p)
    span = max(abs(v) for v in q["centers"]) + 21
    low, high = (
        (q["base_height"] - 20, q["base_height"] + 0.1)
        if part == "base"
        else (q["base_height"] - 0.1, q["base_height"] + q["lid_height"] + 0.1)
    )
    top = q["base_height"] + (q["lid_height"] if part == "lid" else 0)
    attachment_max = float(rugged_outer_body_y(p, part, 0, top))
    return (-span, span, q["front"] - 8.1, attachment_max + 0.05, low, high)


def front_refinement_hints(p, part):
    """Primitive circles and crease levels for the prototype field extractor."""
    q = front_fitting_dimensions(p)
    circles = []
    planes = [[], [q["front"], q["front"] - 7, q["front"] - 8], []]
    levels = [
        q["base_height"],
        q["base_height"] - 19,
        q["base_height"] + q["lid_height"],
    ]
    for center in q["centers"]:
        for sign in (-1, 1):
            planes[0].extend([center + sign * 12.75, center + sign * 20.75])
            circles.append((0, 1, center + sign * 17.2153467, q["front"] - 6, 2))
            if part == "base":
                circles.append(
                    (0, 1, center + sign * 8.5, q["front"] - 3, q["cam_socket_radius"])
                )
            else:
                for a, b, ca, cb in (
                    (0, 1, center + sign * 10.25, q["front"] - 3),
                    (1, 2, q["front"] - 3, q["ball_center_z"]),
                ):
                    circles.append((a, b, ca, cb, q["ball_radius"]))
    if part == "base":
        circles.append((1, 2, q["front"] + 2, q["base_height"] - 5.4921894, 10))
        levels.extend(
            [
                q["cam_center_z"] + sign * (q["cam_socket_half_height"] - offset)
                for sign in (-1, 1)
                for offset in (0, 0.9)
            ]
        )
    else:
        circles.append(
            (
                1,
                2,
                q["front"] + 2,
                q["base_height"] + q["lid_height"] - (30 - 10 * math.sqrt(3)),
                10,
            )
        )
    return {"circles": circles, "planes": planes, "levels": levels, "rectangles": []}
