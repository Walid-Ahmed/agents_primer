"""Small logging helpers shared by the Anthropic examples."""

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Iterator, TextIO


def log_message(log_file: TextIO, role: str, content: object) -> None:
    """Write one clearly labelled message to the execution log."""
    # Anthropic response blocks are Python objects. Convert them to ordinary
    # dictionaries so their fields are easy to read in the text log.
    if isinstance(content, list):
        content = [
            block.model_dump() if hasattr(block, "model_dump") else block
            for block in content
        ]

    # Add a visible heading, then pretty-print long dictionaries across lines.
    log_file.write(f"\n{'=' * 70}\n{role.upper()}\n{'=' * 70}\n")
    log_file.write(f"{pformat(content, sort_dicts=False)}\n")
    # Write immediately instead of waiting for Python to fill its file buffer.
    log_file.flush()


# @contextmanager lets callers use this function with Python's `with` statement.
@contextmanager
def execution_log(script_file: str) -> Iterator[TextIO]:
    """Create a timestamped log and print its location when execution ends."""
    # script_file is __file__ from the calling script. Its parent is the
    # anthropic folder, so logs are stored in anthropic/logs/.
    log_directory = Path(script_file).parent / "logs"
    log_directory.mkdir(exist_ok=True)

    # The timestamp gives every execution its own log instead of overwriting one.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_directory / f"one_round_tool_use_{timestamp}.log"

    try:
        # `yield` gives the open file to the code inside the caller's with block.
        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"Anthropic tool-use execution: {datetime.now()}\n")
            yield log_file
    finally:
        # This runs when the with block ends, even if execution raises an error.
        print(f"\nFull execution log saved to: {log_path.resolve()}")
