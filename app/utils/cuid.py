from cuid2 import Cuid

CUID_GENERATOR: Cuid = Cuid(length=16)


def generate_cuid() -> str:
    return CUID_GENERATOR.generate()
