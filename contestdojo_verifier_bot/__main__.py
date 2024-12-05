import aiohttp
import discord
import os
import traceback
from contestdojo_api_client import Client as ContestDojoClient
from contestdojo_api_client.structs import EventStudent

EVENT_ID = "JHVrMPgX08z7kdmZP8Cs"
CONTESTDOJO_API_KEY = os.environ["CONTESTDOJO_API_KEY"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

VERIFY_TEXT = """
Welcome to the BMT 2024 Online Discord server!

To gain access to the channels, please first verify yourself with ContestDojo
using the button below. You will be prompted to enter the email address you used
to register for the event. This is the same email address you will use to login
to the website to take your tests.

Once you are verified, you will be able to see the rest of the server. If you
have trouble verifying, please reach out to server staff or open a ticket.
""".strip()


class Client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.cd = ContestDojoClient(CONTESTDOJO_API_KEY)

    async def _async_setup_hook(self):
        # https://github.com/Rapptz/discord.py/pull/9870
        await super()._async_setup_hook()
        self.http.connector = aiohttp.TCPConnector(limit=0)

    async def setup_hook(self):
        self.view = VerifyView(self)
        self.add_view(self.view)

    async def on_message(self, message: discord.Message):
        if (
            message.content == "<<verifyview>>"
            and isinstance(message.author, discord.Member)
            and message.author.guild_permissions.administrator
            and self.view is not None
        ):
            await message.delete()
            await message.channel.send(VERIFY_TEXT, view=self.view)

    async def find_student_by_email(self, email: str):
        matches = await self.cd.list_event_students(EVENT_ID, email=email)
        if len(matches) == 0:
            return None
        if len(matches) == 1:
            return matches[0]
        raise ValueError(
            "Found two students with this email. This should not happen..."
        )

    async def verify_student(self, student: EventStudent, member: discord.Member):
        verified_role = discord.utils.get(member.guild.roles, name="Verified")
        if verified_role is None:
            raise ValueError("Couldn't find the Verified role.")

        await member.edit(
            nick=f"[{student.number}] {student.fname} {student.lname}",
        )
        await member.add_roles(verified_role)
        await self.cd.update_event_student(
            EVENT_ID,
            student.id,
            custom_fields={
                "discord-id": str(member.id),
                "discord-username": member.name,
            },
        )


class VerifyModal(discord.ui.Modal, title="ContestDojo Verification"):
    email = discord.ui.TextInput(
        label="Email Address",
        placeholder="Enter the email address on your student account.",
    )

    def __init__(self, bot: Client):
        self.bot = bot
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        if isinstance(interaction.user, discord.User):
            return await interaction.response.send_message(
                "You can't use this in DMs! How did we even get here...",
                ephemeral=True,
            )

        student = await self.bot.find_student_by_email(self.email.value)
        if student is None:
            return await interaction.response.send_message(
                "Couldn't find your student account. Make sure you're using the right email!",
                ephemeral=True,
            )

        if student.number is None or student.number == "":
            return await interaction.response.send_message(
                "Unfortunately, you don't seem to be registered for the event.",
                ephemeral=True,
            )

        if (
            student.customFields is not None
            and (id := student.customFields.get("discord-id", "")) != ""
            and id != str(interaction.user.id)
        ):
            user = await self.bot.fetch_user(int(id))
            return await interaction.response.send_message(
                f"Looks like you've already verified with a different Discord account ({user.name})!",
                ephemeral=True,
            )

        await self.bot.verify_student(student, interaction.user)
        return await interaction.response.send_message(
            f"Welcome to the server, {student.fname}! Your student ID is {student.number}.",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )
        traceback.print_exception(type(error), error, error.__traceback__)


class VerifyView(discord.ui.View):
    def __init__(self, bot: Client):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Verify with ContestDojo",
        style=discord.ButtonStyle.green,
        custom_id="persistent:verify_contestdojo",
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal(self.bot))


Client().run(BOT_TOKEN)
