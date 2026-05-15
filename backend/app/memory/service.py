from dataclasses import dataclass, field


@dataclass
class MemoryRecord:
    key: str
    value: dict[str, object]
    namespace: str


@dataclass
class MemoryService:
    records: list[MemoryRecord] = field(default_factory=list)

    def put(self, namespace: str, key: str, value: dict[str, object]) -> None:
        self.records.append(MemoryRecord(namespace=namespace, key=key, value=value))

    def get(self, namespace: str, key: str) -> dict[str, object] | None:
        for record in reversed(self.records):
            if record.namespace == namespace and record.key == key:
                return record.value
        return None
