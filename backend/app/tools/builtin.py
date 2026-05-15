from dataclasses import dataclass


@dataclass(slots=True)
class HttpTool:
    name: str = "http_request"

    def run(self, input_payload: dict[str, object]) -> dict[str, object]:
        return {"ok": True, "tool": self.name, "input": input_payload}


@dataclass(slots=True)
class FilesystemTool:
    name: str = "filesystem"

    def run(self, input_payload: dict[str, object]) -> dict[str, object]:
        return {"ok": True, "tool": self.name, "input": input_payload}
