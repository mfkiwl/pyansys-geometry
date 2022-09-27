"""``Edge`` class module."""

from enum import Enum, unique
from typing import TYPE_CHECKING, List

from ansys.api.geometry.v0.edges_pb2 import EdgeIdentifier
from ansys.api.geometry.v0.edges_pb2_grpc import EdgesStub
from pint import Quantity

from ansys.geometry.core.connection import GrpcClient
from ansys.geometry.core.misc import SERVER_UNIT_LENGTH

if TYPE_CHECKING:
    from ansys.geometry.core.designer.body import Body  # pragma: no cover
    from ansys.geometry.core.designer.face import Face  # pragma: no cover


@unique
class CurveType(Enum):
    """Enum holding the possible values for curve types by the geometry service."""

    CURVETYPE_UNKNOWN = 0
    CURVETYPE_LINE = 1
    CURVETYPE_CIRCLE = 2
    CURVETYPE_ELLIPSE = 3
    CURVETYPE_NURBS = 4
    CURVETYPE_PROCEDURAL = 5


class Edge:
    """
    Represents a single edge of a body within the design assembly.

    Synchronizes to a design within a supporting geometry service instance.

    Parameters
    ----------
    id : str
        A server defined identifier for the body.
    curve_type : CurveType
        Specifies what type of curve the edge forms.
    body : Body
        The parent body the edge constructs.
    grpc_client : GrpcClient
        An active supporting geometry service instance for design modeling.
    """

    def __init__(self, id: str, curve_type: CurveType, body: "Body", grpc_client: GrpcClient):
        """Constructor method for ``Edge``."""
        self._id = id
        self._curve_type = curve_type
        self._body = body
        self._grpc_client = grpc_client
        self._edges_stub = EdgesStub(grpc_client.channel)

    @property
    def id(self) -> str:
        """ID of the edge."""
        return self._id

    @property
    def length(self) -> Quantity:
        """Calculated length of the edge."""
        length_response = self._edges_stub.GetEdgeLength(EdgeIdentifier(id=self.id))
        return Quantity(length_response.length, SERVER_UNIT_LENGTH)

    @property
    def curve_type(self) -> CurveType:
        """Curve type of the edge."""
        return self._curve_type

    @property
    def faces(self) -> List["Face"]:
        """Get the ``Face`` objects that contain this ``Edge``."""
        from ansys.geometry.core.designer.face import Face, SurfaceType

        grpc_faces = self._edges_stub.GetEdgeFaces(EdgeIdentifier(id=self.id)).faces
        return [
            Face(grpc_face.id, SurfaceType(grpc_face.surface_type), self._body, self._grpc_client)
            for grpc_face in grpc_faces
        ]