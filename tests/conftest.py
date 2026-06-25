import sys
from pathlib import Path

# Make the repo root importable (e.g. `import api.enhanced_main`) regardless
# of how pytest is invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
