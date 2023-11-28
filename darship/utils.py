import disnake
from motor.motor_asyncio import AsyncIOMotorCollection
import sys
from typing import Any


def python_version(verbose: bool) -> str:
    if verbose:
        return sys.version
    vi = sys.version_info
    return f"{vi.major}.{vi.minor}.{vi.micro}{f'-{vi.releaselevel}' if vi.releaselevel != 'final' else ''}"


async def insert_and_return(coll: AsyncIOMotorCollection, doc: Any) -> Any:
    await coll.insert_one(doc)
    return doc


def list_permission_keys(permissions: disnake.Permissions) -> list[str]:
    table = {
        "create_instant_invite": "PERMISSION_CREATE_INSTANT_INVITE",
        "manage_webhooks": "PERMISSION_MANAGE_WEBHOOKS",
    }
    return [
        x
        for x in map(lambda p: table.get(p[0]) if p[1] else None, iter(permissions))
        if x is not None
    ]
