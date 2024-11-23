from cuid2 import Cuid
from app.utils.worker import get_worker_id

CUID_GENERATOR: Cuid = Cuid(length=16)

def generate_cuid() -> str:
  return CUID_GENERATOR.generate()