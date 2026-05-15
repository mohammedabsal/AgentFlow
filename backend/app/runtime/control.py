from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeControl:
    max_depth: int = 32
    default_timeout_seconds: int = 600
    allow_resume: bool = True

    def can_continue(self, depth: int) -> bool:
        return depth < self.max_depth
