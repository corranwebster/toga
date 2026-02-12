from PySide6.QtCore import Qt


class PermissionContext:
    def __init__(self, future):
        super().__init__()
        self.future = future

    def permission_complete(self, permission):
        self.future.set_result(permission == Qt.PermissionStatus.Granted)


class Permission:
    def __init__(self, native_app):
        self._native_app = native_app

    def create(self):
        raise NotImplementedError()

    def has_permission(self):
        permission = self.create()
        status = self._native_app.checkPermission(permission)
        return status == Qt.PermissionStatus.Granted

    def request_permission(self, future):
        # This functor is invoked when the permission is granted; however, permission is
        # granted from a different (inaccessible) thread, so it isn't picked up by
        # coverage.
        permission_context = PermissionContext(future)

        permission = self.create()
        self._native_app.requestPermission(
            permission,
            self._native_app,
            permission_context.permission_complete,
        )
