import asyncio
import disnake
from disnake.ext import commands, tasks
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from .database import DatabaseManager, Guild
from typing import Any, Callable, Optional


class PartnershipBot(commands.AutoShardedInteractionBot):
    def __init__(self, *, mongo_uri: str, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__(
            intents=disnake.Intents(
                guilds=True,
                members=True,
                webhooks=True,
            ),
            loop=loop,
        )
        self.database = DatabaseManager(
            AsyncIOMotorClient(mongo_uri, io_loop=self.loop)
        )
        self.logger = logging.getLogger("darship.core")

    async def update_presence(self) -> None:
        await self.change_presence(
            activity=disnake.Activity(
                name=f"{len(self.guilds)} servers",
                type=disnake.ActivityType.listening,
            )
        )

    @tasks.loop(seconds=60.0)
    async def presence_updater(self) -> None:
        await self.update_presence()

    def tr(self, locale: str, key: str) -> str:
        if locale == "international":
            if key == "LANGUAGE":
                return "International"
            locale = "en-US"
        try:
            ls = self.i18n.get(key)
            if ls:
                return ls.get(locale or "en-US") or ls.get("en-US") or key
            return key
        except:
            return key

    def make_tr(self, locale: str) -> Callable[[str], str]:
        return lambda key: self.tr(locale, key)

    async def begin_interaction(
        self,
        inter: disnake.Interaction,
        *,
        update: dict[str, Any] = {},
        raw_update: dict[str, Any] = {},
    ) -> tuple[Optional[Guild], Callable[[str], str]]:
        if inter.guild_id:
            guild = await self.database.guild(
                inter.guild_id,
                update={
                    "$set": update,
                }
                | raw_update,
            )
            return guild, self.make_tr(guild.language or "en-US")
        return None, self.make_tr("en-US")
