import sys
from pathlib import Path

# "from app.nlu import ..." calissin diye proje kokunu yola ekle.
sys.path.insert(0, str(Path(__file__).resolve().parent))
