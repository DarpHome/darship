import asyncio
import boticordpy
import dotenv
import logging
import os
import sys
from typing import Callable, Optional, TypedDict
from darship.core import PartnershipBot
import traceback

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

mongo_uri = os.getenv("MONGODB_URI")
if mongo_uri is None:
    print("no mongo uri specified", file=sys.stderr)
    sys.exit(1)

bot = PartnershipBot(mongo_uri=mongo_uri, loop=loop)


class BoticordStatsPayload(TypedDict):
    members: Optional[int]
    servers: Optional[int]
    shards: Optional[int]


async def get_stats() -> BoticordStatsPayload:
    return {
        "members": len(bot.users) or None,
        "servers": len(bot.guilds) or None,
        "shards": bot.shard_count or None,
    }


async def amain() -> int:
    try:
        token = os.getenv("DISCORD_BOT_TOKEN")
        if token is None:
            print("no token specified", file=sys.stderr)
            return 1
        await bot.login(token)
        api_token = os.getenv("BOTICORD_API_TOKEN")
        if api_token is not None:
            boticord_client = boticordpy.BoticordClient(
                api_token,
                version=3,
            )
            (boticord_client.autopost().init_stats(get_stats).start(str(bot.user.id)))
        bot.i18n.load("locales/")
        bot.load_extensions("darship/cogs")
        bot.presence_updater.start()
        await bot.connect()
    except Exception as exc:
        traceback.print_exception(exc)
        raise
    return 0


async def aexit() -> None:
    await bot.close()
    bot.presence_updater.cancel()


async def ahandle_exception(raiser: Callable[[], None]) -> None:
    try:
        raiser()  # always raises
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        traceback.print_exception(exc)
    else:
        print("something went wrong!!!")


def make_raiser(exc: Exception) -> Callable[[], None]:
    def raiser() -> None:
        raise exc

    return raiser


if __name__ == "__main__":
    try:
        sys.exit(loop.run_until_complete(amain()))
    except Exception as exc:
        loop.run_until_complete(ahandle_exception(make_raiser(exc)))
    finally:
        if not bot.is_closed:
            loop.run_until_complete(aexit())
        loop.close()
