from PySide6.QtCore import QCameraPermission, Qt
from PySide6.QtMultimedia import (
    QCamera,
    QImageCapture,
    QMediaCaptureSession,
    QMediaDevices,
)
from PySide6.QtMultimediaWidgets import QVideoWidget


class CameraDevice:
    def __init__(self, native):
        self.native = native

    def id(self):
        return bytes(self.native.id())

    def name(self):
        return self.native.description()

    def has_flash(self):
        return True


class PermissionContext:
    def __init__(self, future):
        super().__init__()
        self.future = future

    def permission_complete(self, permission):
        self.future.set_result(permission == Qt.PermissionStatus.Granted)


class Camera:
    def __init__(self, interface):
        self.interface = interface
        self.preview_windows = []

    def has_permission(self, allow_unknown=False):
        permission = QCameraPermission()
        status = self.interface.app._impl.native.checkPermission(permission)

        if allow_unknown:
            valid_values = {
                Qt.PermissionStatus.Granted,
                Qt.PermissionStatus.Undetermined,
            }
        else:
            valid_values = {Qt.PermissionStatus.Granted}

        return status in valid_values

    def request_permission(self, future):
        # This functor is invoked when the permission is granted; however, permission is
        # granted from a different (inaccessible) thread, so it isn't picked up by
        # coverage.
        permission_context = PermissionContext(future)

        permission = QCameraPermission()
        self.interface.app._impl.native.requestPermission(
            permission,
            self.interface.app._impl.native,
            permission_context.permission_complete,
        )

    def get_devices(self):
        return QMediaDevices.videoInputs()

    def take_photo(self, result, device, flash):
        if self.has_permission(allow_unknown=True):
            capture_session = QMediaCaptureSession()
            # Hook up the camera
            if device is None:
                camera = QCamera()
            else:
                camera = QCamera(device.native)
            capture_session.setCamera(camera)

            # live video view
            viewfinder = QVideoWidget()
            capture_session.setVideoOutput(viewfinder)

            # prepare for image capture
            image_capture = QImageCapture()
            capture_session.setImageCapture(image_capture)

            viewfinder.show()
            camera.start()

        else:
            raise PermissionError("App does not have permission to take photos")
