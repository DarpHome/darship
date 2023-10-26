from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any, Optional, TypedDict, Union
from pymongo import ReturnDocument
from .utils import insert_and_return


class GuildDocument(TypedDict):
    id: int
    banned_for: Optional[str]
    banner: Optional[str]
    reminders_id: Optional[int]
    flags: int
    invite: Optional[str]
    language: Optional[str]
    color: Optional[int]
    description: Optional[str]
    last_bumped: Optional[int]
    partnership_channel: Optional[int]
    webhook_url: Optional[str]


class Guild:
    manager: Optional["DatabaseManager"]
    id: int
    banned_for: Optional[str]
    banner: Optional[str]
    reminders_id: Optional[int]
    flags: int
    invite: Optional[str]
    language: Optional[str]
    color: Optional[int]
    description: Optional[str]
    last_bumped: Optional[int]
    partnership_channel: Optional[int]
    webhook_url: Optional[str]
    def __init__(self, manager: "DatabaseManager", obj: Union[int, GuildDocument]) -> None:
        self.manager = manager
        if isinstance(obj, int):
            self.id = obj
        else:
            self.id = obj['_id']
            self.banned_for = obj['banned_for']
            self.banner = obj['banner']
            self.reminders_id = obj['reminders_id']
            self.flags = obj['flags']
            self.invite = obj['invite']
            self.language = obj['language']
            self.color = obj['color']
            self.description = obj['description']
            self.last_bumped = obj['last_bumped']
            self.partnership_channel = obj['partnership_channel']
            self.webhook_url = obj['webhook_url']


class DatabaseManager:
    def __init__(self, client: AsyncIOMotorClient) -> None:
        self.client = client
        self.database = self.client.darship


    def partial_guild(self, guild_id: int) -> Guild:
        return Guild(self, guild_id)


    async def guild(self, guild_id: int, *, update: dict[str, Any] = {}) -> Guild:
        if len(update):
            doc = await self.database.guilds.find_one_and_update({
                '_id': {'$eq': guild_id},
            }, update, return_document=ReturnDocument.AFTER)
            if doc:
                return Guild(self, doc)
            return Guild(self, await insert_and_return(self.database.guilds, {
                '_id': guild_id,
                'banned_for': None,
                'banner': None,
                'reminders_id': None,
                'flags': 0,
                'invite': None,
                'language': None,
                'color': None,
                'description': None,
                'last_bumped': None,
                'partnership_channel': None,
                'webhook_url': None,
            } | update.get('$set', {})))
        return Guild(self,
            await self.database.guilds.find_one({
                '_id': {'$eq': guild_id},
            }) or await insert_and_return(self.database.guilds, {
                '_id': guild_id,
                'banned_for': None,
                'banner': None,
                'reminders_id': None,
                'flags': 0,
                'invite': None,
                'language': None,
                'color': None,
                'description': None,
                'last_bumped': None,
                'partnership_channel': None,
                'webhook_url': None,
            } | update.get('$set', {})),
        )
