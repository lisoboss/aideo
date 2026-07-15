"""Global filesystem paths shared by all local Runtime providers."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PathSettings:
    """ComfyUI-style global model, input, and output storage roots."""

    models_dir: Path
    input_dir: Path
    output_dir: Path

    def __post_init__(self) -> None:
        """Create and normalize the configured storage roots."""
        for path in (self.models_dir, self.input_dir, self.output_dir):
            path.mkdir(parents=True, exist_ok=True)
        object.__setattr__(self, "models_dir", self.models_dir.resolve())
        object.__setattr__(self, "input_dir", self.input_dir.resolve())
        object.__setattr__(self, "output_dir", self.output_dir.resolve())

    def model_path(self, relative: str) -> Path:
        """Resolve a model path safely below the global model root."""
        return self._resolve_under(self.models_dir, relative, create_parent=False)

    def input_path(self, relative: str) -> Path:
        """Resolve an input path safely below the global input root."""
        return self._resolve_under(self.input_dir, relative, create_parent=False)

    def output_path(self, relative: str) -> Path:
        """Resolve an output path safely below the global output root."""
        return self._resolve_under(self.output_dir, relative, create_parent=True)

    def output_uri(self, path: Path) -> str:
        """Encode an output-root path as the Runtime's portable URI."""
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(self.output_dir)
        except ValueError as error:
            raise ValueError("output path must be inside the output root") from error
        return f"runtime://output/{relative.as_posix()}"

    @staticmethod
    def _resolve_under(root: Path, relative: str, *, create_parent: bool) -> Path:
        """Resolve a relative path without allowing it to escape ``root``."""
        candidate = Path(relative)
        if candidate.is_absolute():
            raise ValueError("path must be a relative path")
        resolved = (root / candidate).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as error:
            raise ValueError("path must be a relative path inside its root") from error
        if create_parent:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved
