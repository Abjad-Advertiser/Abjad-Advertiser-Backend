from typing import NewType

from cuid2 import Cuid

CUID_GENERATOR: Cuid = Cuid(length=16)

CUID = NewType("CUID", str)


def generate_cuid() -> CUID:
    return CUID(CUID_GENERATOR.generate())
