import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pytest
from file_reader import load_context

@pytest.fixture(scope="module")
def ctx():
    return load_context()