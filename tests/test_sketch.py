import numpy as np
from pint import Quantity
import pytest

from ansys.geometry.core.math import Point2D
from ansys.geometry.core.math.constants import ZERO_POINT2D
from ansys.geometry.core.math.vector import Vector2D
from ansys.geometry.core.misc.measurements import UNIT_LENGTH, Distance
from ansys.geometry.core.misc.units import UNITS
from ansys.geometry.core.sketch.box import Box
from ansys.geometry.core.sketch.circle import Circle
from ansys.geometry.core.sketch.ellipse import Ellipse
from ansys.geometry.core.sketch.polygon import Polygon
from ansys.geometry.core.sketch.segment import Segment
from ansys.geometry.core.sketch.sketch import Sketch
from ansys.geometry.core.sketch.slot import Slot

DOUBLE_EPS = np.finfo(float).eps


def test_errors_segment():
    """Check errors when handling a ``Segment``."""
    with pytest.raises(TypeError, match="Provided type"):
        Segment("a", "b")
    with pytest.raises(
        ValueError, match="The numpy.ndarray 'start' should not be a nan numpy.ndarray."
    ):
        Segment(Point2D(), "b")
    with pytest.raises(TypeError, match="Provided type"):
        Segment(Point2D([10, 20], unit=UNITS.meter), "b")
    with pytest.raises(
        ValueError, match="The numpy.ndarray 'end' should not be a nan numpy.ndarray."
    ):
        Segment(Point2D([10, 20]), Point2D())
    with pytest.raises(
        ValueError,
        match="Parameters 'start' and 'end' have the same values. No segment can be created.",
    ):
        Segment(Point2D([10, 20]), Point2D([10, 20]))


def test_sketch_segment_edge():
    """Test Segment SketchEdge sketching."""

    # Create a Sketch instance
    sketch = Sketch()

    # fluent api has 0, 0 origin as default start position
    assert len(sketch.edges) == 0
    sketch.segment_to_point(Point2D([2, 3]), "Segment1")
    assert len(sketch.edges) == 1
    assert sketch.edges[0].start == ZERO_POINT2D
    assert sketch.edges[0].end == Point2D([2, 3])
    assert sketch.edges[0].length.m == pytest.approx(3.60555128, rel=1e-7, abs=1e-8)

    # fluent api keeps last edge endpoint as context for new edge
    sketch.segment_to_point(Point2D([3, 3]), "Segment2").segment_to_point(
        Point2D([3, 2]), "Segment3"
    )
    assert len(sketch.edges) == 3
    assert sketch.edges[1].start == Point2D([2, 3])
    assert sketch.edges[1].end == Point2D([3, 3])
    assert sketch.edges[2].start == Point2D([3, 3])
    assert sketch.edges[2].end == Point2D([3, 2])

    # sketch api allows segment defined by two points
    sketch.segment(Point2D([3, 2]), Point2D([2, 0]), "Segment4")
    assert len(sketch.edges) == 4
    assert sketch.edges[3].start == Point2D([3, 2])
    assert sketch.edges[3].end == Point2D([2, 0])

    # sketch api allows segment defined by vector magnitude
    sketch.segment_from_point_and_vector(Point2D([2, 0]), Vector2D([-1, 1]), "Segment5")
    assert len(sketch.edges) == 5
    assert sketch.edges[4].start == Point2D([2, 0])
    assert sketch.edges[4].end == Point2D([1, 1])

    sketch.segment_from_vector(Vector2D([-1, -1]), "Segment6")
    assert len(sketch.edges) == 6
    assert sketch.edges[5].start == Point2D([1, 1])
    assert sketch.edges[5].end == Point2D([0, 0])

    segment1_retrieved = sketch.get("Segment1")
    assert len(segment1_retrieved) == 1
    assert segment1_retrieved[0] == sketch.edges[0]

    segment2_retrieved = sketch.get("Segment2")
    assert len(segment2_retrieved) == 1
    assert segment2_retrieved[0] == sketch.edges[1]

    segment3_retrieved = sketch.get("Segment3")
    assert len(segment3_retrieved) == 1
    assert segment3_retrieved[0] == sketch.edges[2]

    segment4_retrieved = sketch.get("Segment4")
    assert len(segment4_retrieved) == 1
    assert segment4_retrieved[0] == sketch.edges[3]

    segment5_retrieved = sketch.get("Segment5")
    assert len(segment5_retrieved) == 1
    assert segment5_retrieved[0] == sketch.edges[4]

    segment6_retrieved = sketch.get("Segment6")
    assert len(segment6_retrieved) == 1
    assert segment6_retrieved[0] == sketch.edges[5]

    with pytest.raises(
        ValueError,
        match="Parameters 'start' and 'end' have the same values. No segment can be created.",
    ):
        sketch.segment(Point2D([3, 2]), Point2D([3, 2]), "Segment4")


def test_sketch_arc_edge():
    """Test Arc SketchEdge sketching."""

    # Create a Sketch instance
    sketch = Sketch()

    # fluent API has (0, 0) origin as default start position
    #
    #                       ^
    #                       |
    #                       |
    #                       |        (3,3)
    #                       |---------E
    #                       |         |
    #                       |         |
    #                       |         |
    #                 (0,0) S---------O------------->
    #                                  (3,0)
    #
    #
    # Since angle is counterclockwise by default, this will lead to a 270deg
    # angle starting on S and ending on E. This is also PI * 3 / 2 in rads
    #
    assert len(sketch.edges) == 0
    sketch.arc_to_point(Point2D([3, 3]), Point2D([3, 0]), False, "Arc1")
    assert len(sketch.edges) == 1
    assert sketch.edges[0].start == ZERO_POINT2D
    assert sketch.edges[0].end == Point2D([3, 3])
    assert sketch.edges[0].angle == np.pi * 3 / 2

    # Fluent api keeps last edge endpoint as context for new edge
    #
    #
    # In this case, following the previous drawing, we are going from E to S with center
    # at 'O' again, but in clockwise direction. This will lead to 270 degs (PI * 3 / 2 in rads).
    #
    sketch.arc_to_point(Point2D([0, 0]), Point2D([3, 0]), clockwise=True, tag="Arc2")
    assert len(sketch.edges) == 2
    assert sketch.edges[1].start == Point2D([3, 3])
    assert sketch.edges[1].end == Point2D([0, 0])
    assert sketch.edges[1].angle == np.pi * 3 / 2

    sketch.arc(Point2D([10, 10]), Point2D([10, -10]), Point2D([10, 0]), tag="Arc3")
    assert len(sketch.edges) == 3
    assert sketch.edges[2].start == Point2D([10, 10])
    assert sketch.edges[2].end == Point2D([10, -10])
    assert sketch.edges[2].angle == np.pi

    arc1_retrieved = sketch.get("Arc1")
    assert len(arc1_retrieved) == 1
    assert arc1_retrieved[0] == sketch.edges[0]

    arc2_retrieved = sketch.get("Arc2")
    assert len(arc2_retrieved) == 1
    assert arc2_retrieved[0] == sketch.edges[1]

    arc3_retrieved = sketch.get("Arc3")
    assert len(arc3_retrieved) == 1
    assert arc3_retrieved[0] == sketch.edges[2]


def test_sketch_triangle_face():
    """Test Triangle SketchFace sketching."""

    # Create a Sketch instance
    sketch = Sketch()

    # Create the sketch face with triangle
    sketch.triangle(Point2D([10, 10]), Point2D([2, 1]), Point2D([10, -10]), tag="triangle1")
    assert len(sketch.faces) == 1
    assert sketch.faces[0].point1 == Point2D([10, 10])
    assert sketch.faces[0].point2 == Point2D([2, 1])
    assert sketch.faces[0].point3 == Point2D([10, -10])

    sketch.triangle(Point2D([-10, 10]), Point2D([5, 6]), Point2D([-10, -10]), tag="triangle2")
    assert len(sketch.faces) == 2
    assert sketch.faces[1].point1 == Point2D([-10, 10])
    assert sketch.faces[1].point2 == Point2D([5, 6])
    assert sketch.faces[1].point3 == Point2D([-10, -10])

    triangle1_retrieved = sketch.get("triangle1")
    assert len(triangle1_retrieved) == 1
    assert triangle1_retrieved[0] == sketch.faces[0]

    triangle2_retrieved = sketch.get("triangle2")
    assert len(triangle2_retrieved) == 1
    assert triangle2_retrieved[0] == sketch.faces[1]


def test_sketch_trapezoidal_face():
    """Test Trapezoidal Sketchface sketching."""

    # Create a Sketch instance
    sketch = Sketch()

    # Create the sketch face with trapezoid
    sketch.trapezoid(10, 8, np.pi / 4, np.pi / 8, Point2D([10, -10]), tag="trapezoid1")
    assert len(sketch.faces) == 1
    assert sketch.faces[0].width.m == 10
    assert sketch.faces[0].height.m == 8
    assert sketch.faces[0].center == Point2D([10, -10])

    sketch.trapezoid(20, 10, np.pi / 8, np.pi / 16, Point2D([10, -10]), np.pi / 2, tag="trapezoid2")
    assert len(sketch.faces) == 2
    assert sketch.faces[1].width.m == 20
    assert sketch.faces[1].height.m == 10
    assert sketch.faces[1].center == Point2D([10, -10])

    trapezoid1_retrieved = sketch.get("trapezoid1")
    assert len(trapezoid1_retrieved) == 1
    assert trapezoid1_retrieved[0] == sketch.faces[0]

    trapezoid2_retrieved = sketch.get("trapezoid2")
    assert len(trapezoid2_retrieved) == 1
    assert trapezoid2_retrieved[0] == sketch.faces[1]

    # Test the trapezoid errors
    with pytest.raises(ValueError, match="Width must be a real positive value."):
        sketch.trapezoid(
            0, 10, np.pi / 8, np.pi / 16, Point2D([10, -10]), np.pi / 2, tag="trapezoid3"
        )

    with pytest.raises(ValueError, match="Height must be a real positive value."):
        sketch.trapezoid(
            10, -10, np.pi / 8, np.pi / 16, Point2D([10, -10]), np.pi / 2, tag="trapezoid3"
        )


def test_circle_instance():
    """Test circle instance."""
    center, radius = (
        Point2D([0, 0], UNIT_LENGTH),
        (1 * UNIT_LENGTH),
    )
    circle = Circle(center, radius)

    # Check attributes are expected ones
    assert circle.center == center
    assert circle.radius == radius
    assert circle.diameter == 2 * radius
    assert circle.area == np.pi * radius**2
    assert circle.perimeter == 2 * np.pi * radius


def test_circle_instance_errors():
    """Test various circle instantiation errors."""

    with pytest.raises(
        TypeError, match=r"The pint.Unit provided as input should be a \[length\] quantity."
    ):
        Circle(Point2D([10, 20]), 1 * UNITS.fahrenheit)

    with pytest.raises(ValueError, match="Radius must be a real positive value."):
        Circle(Point2D([10, 20]), -10 * UNITS.mm)


def test_sketch_circle_face():
    """Test circle shape creation in a sketch."""

    # Create a Sketch instance
    sketch = Sketch()

    assert len(sketch.faces) == 0

    # Draw a circle in previous sketch
    center, radius = (
        Point2D([10, -10], UNIT_LENGTH),
        (1 * UNIT_LENGTH),
    )
    sketch.circle(center, radius, "Circle")

    # Check attributes are expected ones
    assert len(sketch.faces) == 1
    assert sketch.faces[0].radius == radius
    assert sketch.faces[0].diameter == 2 * radius
    assert sketch.faces[0].area == np.pi * radius**2
    assert sketch.faces[0].perimeter == 2 * np.pi * radius
    assert sketch.faces[0].center == Point2D([10, -10])

    circle_retrieved = sketch.get("Circle")
    assert len(circle_retrieved) == 1
    assert circle_retrieved[0] == sketch.faces[0]


def test_ellipse_instance():
    """Test ellipse instance."""

    semi_major, semi_minor, origin = 2 * UNITS.m, 1 * UNITS.m, Point2D([0, 0], UNITS.m)
    ecc = np.sqrt(1 - (semi_minor / semi_major) ** 2)
    ellipse = Ellipse(origin, semi_major, semi_minor)

    # Check attributes are expected ones
    assert ellipse.semi_major_axis == semi_major
    assert ellipse.semi_minor_axis == semi_minor
    assert abs(ellipse.eccentricity - ecc.m) <= DOUBLE_EPS
    assert ellipse.linear_eccentricity == np.sqrt(semi_major**2 - semi_minor**2)
    assert ellipse.semi_latus_rectum == semi_minor**2 / semi_major
    assert abs((ellipse.perimeter - 9.6884482205477 * UNITS.m).m) <= 5e-14
    assert abs((ellipse.area - 6.28318530717959 * UNITS.m * UNITS.m).m) <= 5e-14


def test_ellipse_instance_errors():
    """Test various ellipse instantiation errors."""
    with pytest.raises(
        TypeError, match=r"The pint.Unit provided as input should be a \[length\] quantity."
    ):
        Ellipse(
            Point2D([10, 20]),
            Quantity(1, UNITS.fahrenheit),
            Quantity(56, UNITS.fahrenheit),
        )

    with pytest.raises(
        TypeError, match=r"The pint.Unit provided as input should be a \[length\] quantity."
    ):
        Ellipse(Point2D([10, 20]), 1 * UNITS.m, Quantity(56, UNITS.fahrenheit))

    with pytest.raises(ValueError, match="Semi-major axis must be a real positive value."):
        Ellipse(
            Point2D([10, 20]),
            -1 * UNITS.m,
            -3 * UNITS.m,
        )

    with pytest.raises(ValueError, match="Semi-minor axis must be a real positive value."):
        Ellipse(
            Point2D([10, 20]),
            1 * UNITS.m,
            -3 * UNITS.m,
        )

    with pytest.raises(ValueError, match="Semi-major axis cannot be shorter than semi-minor axis."):
        Ellipse(
            Point2D([10, 20]),
            1 * UNITS.m,
            3 * UNITS.m,
        )

    ellipse = Ellipse(
        Point2D([10, 20]),
        3 * UNITS.m,
        100 * UNITS.cm,
    )


def test_sketch_ellipse_face():
    """Test ellipse shape creation in a sketch."""

    # Create a Sketch instance
    sketch = Sketch()

    assert len(sketch.faces) == 0

    # Draw a circle in previous sketch
    semi_major, semi_minor, origin = 2 * UNITS.m, 1 * UNITS.m, Point2D([0, 0], UNITS.m)
    ecc = np.sqrt(1 - (semi_minor / semi_major) ** 2)
    sketch.ellipse(origin, semi_major, semi_minor, tag="Ellipse")

    # Check attributes are expected ones
    assert len(sketch.faces) == 1
    assert sketch.faces[0].semi_major_axis == semi_major
    assert sketch.faces[0].semi_minor_axis == semi_minor
    assert abs(sketch.faces[0].eccentricity - ecc.m) <= DOUBLE_EPS
    assert sketch.faces[0].linear_eccentricity == np.sqrt(semi_major**2 - semi_minor**2)
    assert sketch.faces[0].semi_latus_rectum == semi_minor**2 / semi_major
    assert abs((sketch.faces[0].perimeter - 9.6884482205477 * UNITS.m).m) <= 5e-14
    assert abs((sketch.faces[0].area - 6.28318530717959 * UNITS.m * UNITS.m).m) <= 5e-14

    ellipse_retrieved = sketch.get("Ellipse")
    assert len(ellipse_retrieved) == 1
    assert ellipse_retrieved[0] == sketch.faces[0]


def test_polygon_instance():
    """Test polygon instance."""

    radius, sides, center = (1 * UNITS.m), 5, Point2D([0, 0], UNITS.m)
    pentagon = Polygon(center, radius, sides)

    # Check attributes are expected ones
    side_length = 2 * radius * np.tan(np.pi / sides)
    assert pentagon.inner_radius == radius
    assert pentagon.n_sides == 5
    assert pentagon.length == side_length
    assert pentagon.perimeter == sides * side_length

    # Draw a square in previous sketch
    radius, sides, center = (1 * UNITS.m), 4, Point2D([0, 0], UNITS.m)
    square = Polygon(center, radius, sides)

    # Check attributes are expected ones
    side_length = 2 * radius * np.tan(np.pi / sides)  # 2.0 m
    assert square.inner_radius == radius
    assert square.n_sides == 4
    assert square.length == side_length
    assert square.perimeter == sides * side_length
    assert abs(square.area.m - 4.0) <= 1e-15

    with pytest.raises(
        ValueError, match="The minimum number of sides to construct a polygon should be 3."
    ):
        radius, sides, center = (1 * UNITS.m), 2, Point2D([0, 0], UNITS.m)
        Polygon(center, radius, sides)

    with pytest.raises(ValueError, match="Radius must be a real positive value."):
        radius, sides, center = (-1 * UNITS.m), 6, Point2D([0, 0], UNITS.m)
        Polygon(center, radius, sides)


def test_slot_instance():
    """Test slot instance."""

    center = Point2D([2, 3], unit=UNITS.meter)
    width = Distance(4, unit=UNITS.meter)
    height = Distance(2, unit=UNITS.meter)
    slot = Slot(center, width, height)

    # Validate Real inputs accepted
    Slot(center, 888, 88)

    # Check attributes are expected ones
    assert slot.area.m == pytest.approx(7.141592653589793, rel=1e-7, abs=1e-8)
    assert slot.area.units == UNITS.m * UNITS.m
    perimeter = slot.perimeter
    assert perimeter.m == pytest.approx(10.283185307179586, rel=1e-7, abs=1e-8)
    assert perimeter.units == UNITS.m


def test_box_instance():
    """Test box instance."""

    center = Point2D([3, 1], unit=UNITS.meter)
    width = Distance(4, unit=UNITS.meter)
    height = Distance(2, unit=UNITS.meter)
    box = Box(center, width, height)

    # Validate Real inputs accepted
    Box(center, 88, 888)

    # Check attributes are expected ones
    assert box.area.m == 8
    assert box.area.units == UNITS.m * UNITS.m
    assert box.perimeter.m == 12
    assert box.perimeter.units == UNITS.m