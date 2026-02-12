from PySide6.QtCore import QLocationPermission
from PySide6.QtPositioning import QGeoPositionInfoSource

import toga

from ._permissions import Permission

AVAILABILITY = {
    "normal": QLocationPermission.Availability.WhenInUse,
    "background": QLocationPermission.Availability.Always,
}


class LocationPermission(Permission):
    def __init__(self, native_app, availability="normal"):
        super().__init__(native_app)
        self.availability = availability

    def create(self):
        permission = QLocationPermission()
        permission.setAvailability(AVAILABILITY[self.availability])
        return permission


class LocationContext:
    def __init__(self, impl, location):
        self.impl = impl
        self.location = location
        self.impl.native.positionUpdated.connect(self.qt_position_updated)
        self.impl.native.errorOccurred.connect(self.qt_error_occurred)

    def qt_position_updated(self, position):
        coords = position.coordinate()
        self.location.set_result(toga.LatLong(coords.latitude(), coords.longitude()))
        self.disconnect()

    def qt_error_occurred(self, error):
        if error == QGeoPositionInfoSource.Error.NoError:
            return
        elif error == QGeoPositionInfoSource.Error.AccessError:
            message = "Location permission is no longer available for app."
        elif error == QGeoPositionInfoSource.Error.ClosedError:
            message = "Location service is no longer available."
        elif error == QGeoPositionInfoSource.Error.UpdateTimeoutError:
            message = "Finding current location took too long."
        else:
            message = "An unknown error has occurred in the location service. "
        self.location.set_error(RuntimeError(message))
        self.disconnect()

    def disconnect(self):
        self.impl.native.positionUpdated.disconnect(self.qt_position_updated)
        self.impl.native.errorOccurred.disconnect(self.qt_error_occurred)
        self.impl._location_contexts.discard(self)


class Location:
    native: QGeoPositionInfoSource

    def __init__(self, interface):
        self.interface = interface
        native_app = interface.app._impl.native
        self._permission = LocationPermission(native_app)
        self._background_permission = LocationPermission(native_app, "background")
        self.native = QGeoPositionInfoSource.createDefaultSource(native_app)
        self.native.positionUpdated.connect(self.qt_position_updated)
        self._location_contexts = set()

    def qt_position_updated(self, position):
        coords = position.coordinate()
        self.interface.on_change(
            self,
            toga.LatLong(coords.latitude(), coords.longitude()),
            coords.altitude(),
        )

    def has_permission(self):
        return self._permission.has_permission()

    def request_permission(self, future):
        self._permission.request_permission(future)

    def has_background_permission(self):
        return self._background_permission.has_permission()

    def request_background_permission(self, future):
        self._background_permission.request_permission(future)

    def start_tracking(self):
        self.native.startUpdates()

    def stop_tracking(self):
        self.native.stopUpdates()

    def current_location(self, location):
        self._location_contexts.add(LocationContext(self, location))
