"""PyGeometry-specific errors."""

from functools import wraps
import signal
import threading

from grpc._channel import _InactiveRpcError, _MultiThreadedRendezvous

from ansys.geometry.core import LOG as logger

SIGINT_TRACKER = []


class GeometryRuntimeError(RuntimeError):
    """Provides the error message to raise when the Geometry Service passes a runtime error."""

    pass


class GeometryExitedError(RuntimeError):
    """
    Provides the error message to raise when the Geometry Service has exited.

    Parameters
    ----------
    msg : str, optional
        Message to raise. The default is ``"Geometry Service has exited."``.
    """

    def __init__(self, msg="Geometry Service has exited."):
        """Initializer for ``GeometryExitedError``."""
        RuntimeError.__init__(self, msg)  # pragma: no cover


# handler for protect_grpc
def handler(sig, frame):  # pragma: no cover
    """Pass signal to the custom interrupt handler."""
    logger.info("KeyboardInterrupt received. Waiting until Geometry Service execution finishes.")
    SIGINT_TRACKER.append(True)


def protect_grpc(func):
    """Capture gRPC exceptions and raise a more succinct error message.

    This method captures the ``KeyboardInterrupt`` exception to avoid
    segfaulting the Geometry Service.

    While this works some of the time, it does not all of the time. For some
    reason, gRPC still captures SIGINT.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Capture gRPC exceptions and KeyboardInterrupt.

        Returns
        -------
        out
            The result of the function wrapped.

        Raises
        ------
        GeometryExitedError
            In case a gRPC error of type InactiveRpcError, MultiThreadedRendezvous.
        KeyboardInterrupt
            In case of KeyboardInterrupt error is observed.
        """

        # capture KeyboardInterrupt
        old_handler = None
        if threading.current_thread().__class__.__name__ == "_MainThread":
            if threading.current_thread().is_alive():
                old_handler = signal.signal(signal.SIGINT, handler)

        # Capture gRPC exceptions
        try:
            out = func(*args, **kwargs)
        except (_InactiveRpcError, _MultiThreadedRendezvous) as error:  # pragma: no cover
            raise GeometryExitedError(
                f"Geometry Service connection terminated: {error.details()}"
            ) from None

        if threading.current_thread().__class__.__name__ == "_MainThread":
            received_interrupt = bool(SIGINT_TRACKER)

            # always clear and revert to old handler
            SIGINT_TRACKER.clear()
            if old_handler:
                signal.signal(signal.SIGINT, old_handler)

            if received_interrupt:  # pragma: no cover
                raise KeyboardInterrupt("Interrupted during Geometry Service execution")

        return out

    return wrapper