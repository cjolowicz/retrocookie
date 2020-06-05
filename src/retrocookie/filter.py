"""Interface for git-filter-repo."""
from pathlib import Path
from typing import Any
from typing import Container
from typing import Dict
from typing import Iterator
from typing import List
from typing import overload
from typing import Sequence
from typing import Tuple

from git_filter_repo import Blob
from git_filter_repo import FilteringOptions
from git_filter_repo import RepoFilter

from . import git
from . import utils


def get_replacements(
    context: Dict[str, str], whitelist: Container[str], blacklist: Container[str],
) -> List[Tuple[bytes, bytes]]:
    """Return replacements to be applied to commits from the template instance."""

    def ref(key: str) -> str:
        return f"{{{{ cookiecutter.{key} }}}}"

    return [
        (value.encode(), ref(key).encode())
        for key, value in context.items()
        if key not in blacklist and not (whitelist and key not in whitelist)
    ]


def quote_tokens(
    text: bytes, quotes: Tuple[bytes, bytes], tokens: Sequence[bytes]
) -> bytes:
    """Wrap tokens in ``<quotes[0]><token><quotes[1]>``."""

    def _generate() -> Iterator[bytes]:
        index = 0

        while index < len(text):
            for token in tokens:
                found = text.find(token, index)
                if found != -1:
                    break

            if found == -1:
                yield text[index:]
                break

            if found != 0:
                yield text[index:found]

            yield token.join(quotes)
            index = found + len(token)

    return b"".join(_generate())


@overload
def to_bytes(args: Tuple[str, str]) -> Tuple[bytes, bytes]:  # noqa: D103
    ...  # pragma: no cover


@overload
def to_bytes(args: Tuple[str, ...]) -> Tuple[bytes, ...]:  # noqa: D103
    ...  # pragma: no cover


def to_bytes(args: Tuple[str, ...]) -> Tuple[bytes, ...]:
    """Convert each str to bytes."""
    return tuple(arg.encode() for arg in args)


def escape_jinja(text: bytes) -> bytes:
    """Escape Jinja tokens."""
    quotes = to_bytes(('{{ "', '" }}'))
    tokens = to_bytes(("{{", "}}", "{%", "%}", "{#", "#}"))
    return quote_tokens(text, quotes, tokens)


class RepositoryFilter:
    """Perform path and blob replacements on a repository."""

    def __init__(
        self,
        repository: git.Repository,
        path: Path,
        context: Dict[str, str],
        whitelist: Container[str],
        blacklist: Container[str],
    ) -> None:
        """Initialize."""
        self.repository = repository
        self.path = str(path).encode()
        self.replacements = get_replacements(context, whitelist, blacklist)

    def filename_callback(self, filename: bytes) -> bytes:
        """Rewrite filenames."""
        for old, new in self.replacements:
            filename = filename.replace(old, new)
        return b"/".join((self.path, filename))

    def blob_callback(self, blob: Blob, metadata: Dict[str, Any]) -> None:
        """Rewrite blobs."""
        blob.data = escape_jinja(blob.data)
        for old, new in self.replacements:
            blob.data = blob.data.replace(old, new)

    def _create_filter(self) -> RepoFilter:
        """Create the filter."""
        args = FilteringOptions.parse_args(["--force"])
        return RepoFilter(
            args,
            filename_callback=self.filename_callback,
            blob_callback=self.blob_callback,
        )

    def run(self) -> None:
        """Run the filter."""
        with utils.chdir(self.repository.path):
            repofilter = self._create_filter()
            repofilter.run()
