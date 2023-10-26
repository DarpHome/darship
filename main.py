import asyncio
import boticordpy
import dotenv
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Callable
from darship.database import DatabaseManager
from darship.core import PartnershipBot
import traceback

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

bot = PartnershipBot(mongo_uri=os.getenv('MONGODB_URI'), loop=loop)


async def get_stats():
    return {"servers": len(bot.guilds), "shards": len(bot.shard_count or []) or None, "members": len(bot.users)}


async def amain() -> None:
    try:
        await bot.login(os.getenv("DISCORD_BOT_TOKEN"))
        boticord_client = boticordpy.BoticordClient(
            os.getenv("BOTICORD_API_TOKEN"),
            version=3,
        )
        (boticord_client.autopost()
            .init_stats(get_stats)
            .start(str(bot.user.id)))
        bot.i18n.load("locales/")
        bot.load_extensions("darship/cogs")
        bot.presence_updater.start()
        await bot.connect()
    except Exception as exception:
        traceback.print_exception(exception)


async def aexit() -> None:
    await bot.close()
    bot.presence_updater.cancel()


async def ahandle_exception(raiser: Callable[[], None]) -> None:
    try:
        raiser() # always raises
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        traceback.print_exception(exception)
    else:
        print("something went wrong!!!")


def make_raiser(exception: Exception) -> None:
    def raiser() -> None:
        raise exception
    return raiser


if __name__ == '__main__':
    try:
        loop.run_until_complete(amain())
    except Exception as exception:
        loop.run_until_complete(ahandle_exception(make_raiser(exception)))
    finally:
        if not bot.is_closed:
          loop.run_until_complete(aexit())
        loop.close()