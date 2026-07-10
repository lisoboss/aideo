"""Abstract interface for image edit / upscale providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from aideo_runtime.provider import BaseProvider, ProgressStatus

PROVIDERS: dict[str, type[BaseProvider]] = {}


class ImageProvider(BaseProvider):
    """A provider that edits or super-resolves images.

    Handles two task families dispatched from aideo-serv (both routed to
    the ``image`` category):

    - **edit** — ``params["mode"]`` ∈ ``composite`` / ``replace_character`` /
      ``inpainting`` / ``style_transfer``. Edits ``input_files[0]``
      (``role="base"``) using the reference images (``role="reference"``) and
      ``params["mask_regions"]``.
    - **upscale** — ``params["scale"]`` ∈ {2, 4}. Super-resolves
      ``input_files[0]`` (``role="source"``).

    Both receive the aideo-serv ``_submit_to_inference`` payload: ``prompt``,
    ``params``, ``input_files``, ``task_id``, plus ``output_root`` / ``input_root``.
    """

    @abstractmethod
    async def run(
        self,
        prompt: str = "",
        params: dict | None = None,
        input_files: list[dict] | None = None,
        task_id: str | None = None,
        output_root: str | None = None,
        input_root: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[ProgressStatus, None]:
        """Edit or upscale an image, yielding progress then the final result.

        The final yield MUST populate ``result_data`` (e.g. the output asset
        path / url). Long operations should check ``self.is_cancelled``.
        """
        ...


def register_provider(provider_cls: type[ImageProvider]) -> None:
    """Register an image provider class."""
    if not issubclass(provider_cls, ImageProvider):
        raise TypeError(f"{provider_cls} is not a subclass of ImageProvider")
    name = getattr(provider_cls, "provider_name", None)
    if not name:
        raise ValueError(f"{provider_cls} must define provider_name")
    PROVIDERS[name] = provider_cls


def get_provider(name: str) -> type[ImageProvider]:
    """Get an image provider class by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Provider {name} is not registered")
    return PROVIDERS[name]
