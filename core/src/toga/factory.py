from importlib.metadata import entry_points


class Factory:
    def __init__(self, project_name: str = "core"):
        self.project_name = project_name
        self._backend_name = None
        self._entrypoints = {}

    @property
    def backend(self) -> str:
        if self._backend_name is None:
            import toga.platform

            self._backend_name = toga.platform.backend
            self._load_entrypoints()
        return self._backend_name

    @backend.setter
    def backend(self, value: str):
        if self._backend_name is None:
            self._backend_name = value
            self._load_entrypoints()
        else:
            raise RuntimeError(
                "Factory backend is already set to {self._backend_name!r}"
            )

    def _load_entrypoints(self):
        group = f"toga.{self.project_name}.backend.{self.backend}"
        self._entrypoints.update(
            {entrypoint.name: entrypoint for entrypoint in entry_points(group=group)}
        )

    def __getattr__(self, name):
        if name in self._entrypoints:
            value = self._entrypoints[name].load()
            setattr(self, name, value)
            return value
        else:
            return super().__getattr__(name)
