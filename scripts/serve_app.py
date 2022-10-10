import lightning as L


class ServeBuildConfig(L.BuildConfig):
    def build_commands(self):
        return ["pip install dummy-package==0.0.1"]


class ServeWork(L.LightningWork):
    def __init__(self) -> None:
        super().__init__(cloud_build_config=ServeBuildConfig())

    def run(self):
        pass


class ServeFlow(L.LightningFlow):
    def __init__(self):
        super().__init__()
        self.serve_work = ServeWork()

    def run(self):
        self.serve_work.run()
        self._exit()


app = L.LightningApp(ServeFlow())
