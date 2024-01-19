import disnake
from disnake.ext import commands
import time
from ..core import PartnershipBot
from typing import Optional
from ..utils import python_version


class BaseCog(commands.Cog):
    bot: PartnershipBot

    def __init__(self, bot: PartnershipBot) -> None:
        self.bot = bot
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.logger.info(
            "Logged as %s#%s!", self.bot.user.name, self.bot.user.discriminator
        )
        await self.bot.update_presence()

    @commands.slash_command(
        name=disnake.Localized("ping", key="COMMAND_PING_NAME"),
        description=disnake.Localized("Pong!", key="COMMAND_PING_DESCRIPTION"),
    )
    async def ping(self, inter: disnake.ApplicationCommandInteraction) -> None:
        _, t = await self.bot.begin_interaction(inter)
        send_time: float = time.time()
        await inter.response.send_message(
            "🏓",
            ephemeral=True,
        )
        spent: float = time.time() - send_time
        ws_latency: Optional[float] = None
        if self.bot.ws is not None:
            ws_latency = self.bot.ws.latency
        message: disnake.InteractionMessage = await inter.original_response()
        await message.edit(
            f"🏓 {t('PING_WEBSOCKET')}: {t('UNKNOWN') if ws_latency is None else f'{ws_latency:.4}ms'}\n"
            f"🏓 {t('PING_HTTP')}: {spent:.4}ms",
        )

    @commands.slash_command(
        name=disnake.Localized("bot", key="COMMAND_BOT_NAME"),
        description=disnake.Localized("About bot", key="COMMAND_BOT_DESCRIPTION"),
    )
    async def botinfo(self, inter: disnake.ApplicationCommandInteraction) -> None:
        _, t = await self.bot.begin_interaction(inter)
        await inter.response.send_message(
            embed=disnake.Embed(
                title=t("BOT_TITLE"),
                description=t("BOT_DESCRIPTION"),
                color=0x6F9AD2,
            )
            .add_field(
                name=t("BOT_OWNER"),
                value="<@1073325901825187841> (nerdarp)",
                inline=False,
            )
            .add_field(
                name=t("BOT_LANGUAGE_VERSION"),
                value=f"<:dh_pl_logo_python:1165581055915466752> {python_version(False)} (||{python_version(True)}||)",
            ),
            components=[
                disnake.ui.Button(
                    style=disnake.ButtonStyle.link,
                    url="https://discord.gg/EVtSwKttEH",
                    emoji="<:dh_discord_clyde_blurple:1145500476150927420>",
                ),
                disnake.ui.Button(
                    style=disnake.ButtonStyle.link,
                    url=f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=536872961",
                    label=t("BOT_ADD"),
                ),
            ],
            ephemeral=True,
        )


def setup(bot: PartnershipBot) -> None:
    bot.add_cog(BaseCog(bot))
