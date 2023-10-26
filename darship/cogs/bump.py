import aiohttp
import disnake
from disnake.ext import commands
from yarl import URL
import time

from ..core import PartnershipBot
from ..database import Guild
from ..types import RatingType
from ..utils import list_permission_keys

class BumpCog(commands.Cog):
    bot: PartnershipBot
    def __init__(self, bot: PartnershipBot) -> None:
        self.bot = bot
        super().__init__()


    @commands.Cog.listener('on_button_click')
    async def button_clicked(self, inter: disnake.MessageInteraction) -> None:
        custom_id = inter.component.custom_id
        parts = [custom_id]
        if ':' in custom_id:
            parts = custom_id.split(':', 1)
        match parts[0]:
            case 'darship_like':
                guild_id: int = int(parts[1])
                ratings = self.bot.database.database.ratings
                rating = await ratings.find_one({
                    'guild_id': {'$eq': guild_id},
                    'user_id': {'$eq': inter.author.id},
                })
                _, t = await self.bot.begin_interaction(inter)
                if rating is not None:
                    if rating['type'] == RatingType.LIKE.value:
                        await inter.response.send_message(t("WOULD_YOU_REMOVE_RATING"), components=[
                            disnake.ui.Button(
                                style=disnake.ButtonStyle.blurple,
                                label=t("WOULD_YOU_REMOVE_RATING_BUTTON_LABEL"),
                                custom_id=f"darship_remove_rating:{guild_id}"
                            ),
                        ], ephemeral=True)
                        return
                    else:
                        await ratings.update_one({
                            '_id': {'$eq': rating['_id']},
                        }, {
                            '$set': {'type': RatingType.LIKE.value, 'reason': None},
                        })
                else:
                    await ratings.insert_one({
                        'guild_id': guild_id,
                        'user_id': inter.author.id,
                        'type': RatingType.LIKE.value,
                        'reason': None,
                    })
                await inter.response.send_message(t("SUCCESSFULLY_LIKED"), ephemeral=True)
            case 'darship_dislike':
                guild_id: int = int(parts[1])
                ratings = self.bot.database.database.ratings
                rating = await ratings.find_one({
                    'guild_id': {'$eq': guild_id},
                    'user_id': {'$eq': inter.author.id},
                })
                _, t = await self.bot.begin_interaction(inter)
                await inter.response.send_modal(disnake.ui.Modal(
                    title=t("DISLIKE"),
                    components=[
                        disnake.ui.TextInput(
                            label=t("DISLIKE_REASON"),
                            custom_id="darship_dislike_reason",
                            style=disnake.TextInputStyle.short,
                            value=rating['reason'] if rating and rating['type'] == RatingType.DISLIKE.value else None,
                            required=True,
                            min_length=10,
                            max_length=64,
                        ),
                    ],
                    custom_id=f"darship_dislike:{guild_id}",
                    timeout=0.0,
                ))
            case 'darship_remove_rating':
                guild_id: int = int(parts[1])
                _, t = await self.bot.begin_interaction(inter)
                await self.bot.database.database.ratings.delete_one({
                    'guild_id': guild_id,
                    'user_id': inter.author.id,
                })
                await inter.response.edit_message(content=t("RATING_SUCCESSFULLY_REMOVED"), components=[])
            case 'darship_join':
                guild_id: int = int(parts[1])
                _, t = await self.bot.begin_interaction(inter)
                invite = (await self.bot.database.guild(guild_id)).invite
                if not invite:
                    await inter.response.send_message(t("UNABLE_GET_INVITE"), ephemeral=True)
                    return
                
                await inter.response.send_message(t("JOIN_MESSAGE").format(
                    invite=URL(disnake.Invite.BASE) / invite,
                ), ephemeral=True)


    @commands.Cog.listener('on_modal_submit')
    async def modal_submitted(self, inter: disnake.ModalInteraction):
        custom_id = inter.custom_id
        parts = [custom_id]
        if ':' in custom_id:
            parts = custom_id.split(':', 1)
        match parts[0]:
            case 'darship_dislike':
                ratings = self.bot.database.database.ratings
                reason = inter.text_values['darship_dislike_reason']
                await ratings.delete_one({
                    'guild_id': {'$eq': int(parts[1])},
                    'user_id': inter.author.id,
                })
                await ratings.insert_one({
                    'guild_id': int(parts[1]),
                    'user_id': inter.author.id,
                    'type': RatingType.DISLIKE.value,
                    'reason': reason,
                })
                _, t = await self.bot.begin_interaction(inter)
                await inter.response.send_message(t("SUCCESSFULLY_DISLIKED").format(reason=reason), ephemeral=True)
            case 'darship_set_description':
                _, t = await self.bot.begin_interaction(inter, update={
                    'description': inter.text_values['darship_new_description'],
                })
                await inter.response.send_message(t("SUCCESSFULLY_CHANGED_DESCRIPTION"))


    @commands.slash_command(
        name=disnake.Localized("bump", key="COMMAND_BUMP_NAME"),
        description=disnake.Localized("Bump server", key="COMMAND_BUMP_DESCRIPTION"),
        dm_permission=False,
    )
    async def bump(self, inter: disnake.GuildCommandInteraction) -> None:
        source_guild, t = await self.bot.begin_interaction(inter)
        if source_guild.banned_for:
            await inter.response.send_message(t("BANNED_FOR").format(reason=source_guild.banned_for), ephemeral=True)
            return
        if source_guild.language is None:
            await inter.response.send_message(t("LANGUAGE_SETUP_REQUIRED").format(command="</set-language:1167070852639096844>"), ephemeral=True)
            return
        if source_guild.webhook_url is None:
            await inter.response.send_message(t("CHANNEL_SETUP_REQUIRED").format(command="</set-channel:1167051138995081307>"), ephemeral=True)
            return
        if source_guild.description is None:
            await inter.response.send_message(t("DESCRIPTION_SETUP_REQUIRED").format(command="</set-description:1167048763932672111>"), ephemeral=True)
            return
        COOLDOWN: int = 60 * 60 * 2
        diff: int = int(time.time()) - (source_guild.last_bumped or 0)
        if diff < COOLDOWN:
            await inter.response.send_message(t("BUMP_COOLDOWN").format(at=disnake.utils.format_dt(
                source_guild.last_bumped + COOLDOWN,
                style="R",
            )), ephemeral=True)
            return
        await self.bot.database.guild(inter.guild_id, update={
            '$set': {
                'last_bumped': int(time.time()),
            },
        })
        await inter.response.send_message(t("ADVERTISING_START"))
        rating: int = 0
        async for rate in self.bot.database.database.ratings.find({
            'guild_id': {'$eq': source_guild.id},
        }):
            match rate['type']:
                case RatingType.LIKE.value:
                    rating += 1
                case RatingType.DISLIKE.value:
                    rating -= 1
        rating_as_str = str(rating)
        invalid_webhooks: list[str] = []
        counter: int = 0
        timestamp = disnake.utils.utcnow()
        member_count = str(inter.guild.member_count)
        embed = lambda t: disnake.Embed(
            title=inter.guild.name,
            description=source_guild.description,
            timestamp=timestamp,
            color=source_guild.color,
        ).add_field(
            name=t("OWNER"),
            value=inter.guild.owner.mention,
        ).add_field(
            name=t("BUMPER"),
            value=inter.author.mention,
        ).add_field(
            name=t("MEMBER_COUNT"),
            value=member_count,
        ).add_field(
            name=t("RATING"),
            value=rating_as_str,
        ).set_thumbnail(inter.guild.icon.url if inter.guild.icon else None).set_footer(
            text=f"ID: {source_guild.id} | Owner ID: {inter.guild.owner.id} | Bumper ID: {inter.author.id}"
        )
        components = lambda t: [
            disnake.ui.Button(
                style=disnake.ButtonStyle.success,
                label=t("JOIN"),
                custom_id=f"darship_join:{source_guild.id}",
                emoji="🚪",
                row=0,
            ),
            disnake.ui.Button(
                style=disnake.ButtonStyle.primary,
                custom_id=f"darship_like:{source_guild.id}",
                emoji="👍",
                row=0,
            ),
            disnake.ui.Button(
                style=disnake.ButtonStyle.primary,
                custom_id=f"darship_dislike:{source_guild.id}",
                emoji="👎",
                row=0,
            ),
        ]
        async with aiohttp.ClientSession() as session:
            async for doc in self.bot.database.database.guilds.find({
                'banned_for': {'$eq': None},
                'webhook_url': {'$ne': None},
            } | ({} if source_guild.language == 'international' else {'language': {'$eq': source_guild.language}})):
                target_guild = Guild(self.bot.database, doc)
                target_t = self.bot.make_tr(target_guild.language)
                webhook = disnake.Webhook.from_url(target_guild.webhook_url, session=session)
                try:
                    await webhook.send(embed=embed(target_t), components=components(target_t))
                    counter += 1
                except disnake.NotFound:
                    invalid_webhooks.append(target_guild.id)
                except:
                    pass
        if invalid_webhooks:
            await self.bot.database.database.guilds.update_many({
                '_id': {'$in': invalid_webhooks},
            }, {
                '$set': {'webhook_url': None},
            })
        message = await inter.original_response()
        await message.edit(t("ADVERTISING_DONE").format(x=counter, y=len(invalid_webhooks) + counter))


    @commands.slash_command(
        name=disnake.Localized("set-channel", key="COMMAND_SETCHANNEL_NAME"),
        description=disnake.Localized("Set auto-partnership channel", key="COMMAND_SETCHANNEL_DESCRIPTION"),
        dm_permission=False,
        default_member_permissions=disnake.Permissions(
            manage_channels=True,
            manage_guild=True,
            manage_webhooks=True,
        ),
    )
    async def set_channel(
        self,
        inter: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel = commands.Param(
            name=disnake.Localized("channel", key="PARAM_CHANNEL"),
            description=disnake.Localized("Channel for auto-partnership", key="PARAM_CHANNEL_DESCRIPTION"),
            channel_types=[disnake.ChannelType.text],
        ),
    ) -> None:
        if not inter.app_permissions.manage_webhooks:
            _, t = await self.bot.begin_interaction(inter)
            await inter.response.send_message(t("BOT_REQUIRES_NEXT_PERMISSIONS").format(
                permissions=t("SEPARATOR").join(map(lambda k: t(k), list_permission_keys)),
            ))
            return
        await inter.response.defer()
        webhook = await channel.create_webhook(name="Darship", avatar=self.bot.user.avatar)
        _, t = await self.bot.begin_interaction(inter, update={
            'partnership_channel': channel.id,
            'webhook_url': webhook.url,
        })
        await inter.followup.send(t("SUCCESSFULLY_SET_CHANNEL"))


    @commands.slash_command(
        name=disnake.Localized("set-color", key="COMMAND_SETCOLOR_NAME"),
        description=disnake.Localized("Set embed color", key="COMMAND_SETCOLOR_DESCRIPTION"),
        dm_permission=False,
        default_member_permissions=disnake.Permissions(
            manage_guild=True,
        ),
    )
    async def set_color(
        self,
        inter: disnake.GuildCommandInteraction,
        color: int = commands.Param(
            name=disnake.Localized("color", key="PARAM_COLOR"),
            description=disnake.Localized("Embed color", key="PARAM_COLOR_DESCRIPTION"),
            min_value=0x000000,
            max_value=0xFFFFFF,
        ),
    ) -> None:
        _, t = await self.bot.begin_interaction(inter, update={
            'color': color,
        })
        await inter.response.send_message(embed=disnake.Embed(
            title=t("SUCCESSFULLY_SET_COLOR").format(color=f"#{color:>06X}"),
            timestamp=disnake.utils.utcnow(),
            color=color,
        ))


    @commands.slash_command(
        name=disnake.Localized("set-description", key="COMMAND_SETDESCRIPTION_NAME"),
        description=disnake.Localized("Set description", key="COMMAND_SETDESCRIPTION_DESCRIPTION"),
        dm_permission=False,
        default_member_permissions=disnake.Permissions(
            manage_guild=True,
        ),
    )
    async def set_description(
        self,
        inter: disnake.GuildCommandInteraction,
    ) -> None:
        guild, t = await self.bot.begin_interaction(inter)
        await inter.response.send_modal(disnake.ui.Modal(
            title=t("MODAL_TITLE_SET_DESCRIPTION"),
            components=[
                disnake.ui.TextInput(
                    label=t("MODAL_LABEL_NEW_DESCRIPTION"),
                    custom_id="darship_new_description",
                    style=disnake.TextInputStyle.paragraph,
                    value=guild.description,
                    required=True,
                    min_length=24,
                    max_length=1024,
                )
            ],
            custom_id="darship_set_description",
            timeout=0.0,
        ))


    @commands.slash_command(
        name=disnake.Localized("set-invite-here", key="COMMAND_SETINVITEHERE_NAME"),
        description=disnake.Localized("Set invite here", key="COMMAND_SETINVITEHERE_DESCRIPTION"),
        dm_permission=False,
        default_member_permissions=disnake.Permissions(
            create_instant_invite=True,
            manage_guild=True,
        ),
    )
    async def set_invite_here(
        self,
        inter: disnake.GuildCommandInteraction,
    ) -> None:
        if not inter.app_permissions.create_instant_invite:
            _, t = await self.bot.begin_interaction(inter)
            await inter.response.send_message(t("BOT_REQUIRES_NEXT_PERMISSIONS").format(
                permissions=t("SEPARATOR").join(map(lambda k: t(k), list_permission_keys)),
            ), ephemeral=True)
            return
        invite = await inter.channel.create_invite(
            reason="Partnership link",
            max_age=0,
            max_uses=0,
            unique=False,
        )
        _, t = await self.bot.begin_interaction(inter, update={
            'invite': invite.code,
        })
        await inter.response.send_message(t("SUCCESSFULLY_SET_INVITE").format(
            invite=invite.url,
        ), ephemeral=True)


    @commands.slash_command(
        name=disnake.Localized("set-language", key="COMMAND_SETLANGUAGE_NAME"),
        description=disnake.Localized("Set server language", key="COMMAND_SETLANGUAGE_DESCRIPTION"),
        dm_permission=False,
        default_member_permissions=disnake.Permissions(
            create_instant_invite=True,
            manage_guild=True,
        ),
    )
    async def set_server_language(
        self,
        inter: disnake.GuildCommandInteraction,
        language: str = commands.Param(
            name=disnake.Localized("language", key="PARAM_LANGUAGE"),
            description=disnake.Localized("Language used to advertising", key="PARAM_LANGUAGE_DESCRIPTION"),
            choices=[
                disnake.OptionChoice(
                    name=disnake.Localized("International", key="LANGUAGE_INTERNATIONAL"),
                    value="international",
                ),
                disnake.OptionChoice(
                    name=disnake.Localized("English (US)", key="LANGUAGE_EN_US"),
                    value="en-US",
                ),
                disnake.OptionChoice(
                    name=disnake.Localized("Russian", key="LANGUAGE_RU"),
                    value="ru",
                ),
                disnake.OptionChoice(
                    name=disnake.Localized("Ukrainian", key="LANGUAGE_UK"),
                    value="uk",
                ),
            ]
        ),
    ) -> None:
        _, t = await self.bot.begin_interaction(inter, update={
            'language': language,
        })
        await inter.response.send_message(t("SUCCESSFULLY_SET_LANGUAGE").format(
            language=t("LANGUAGE"),
        ))


def setup(bot: PartnershipBot) -> None:
    bot.add_cog(BumpCog(bot))
