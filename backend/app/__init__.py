import sys
from pathlib import Path

# Add OpenOriginJSON to path so we can import ooj_client
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "OpenOriginJSON"))
