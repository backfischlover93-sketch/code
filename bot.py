import discord
from discord.ext import commands, tasks
import os
import asyncio
import json
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ TOKEN fehlt!")
    exit()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= IDS =================
ACTIVITY_ADMIN_ROLE = 1490395401365356556

ACTIVITY_CHANNEL_ID = 1490395401935655043
STRIKE_CHANNEL_ID = 1490395402304749810

STRIKE_1 = 1490395401336000558
STRIKE_2 = 1490395401336000557
STRIKE_3 = 1490395401336000555

EXEMPT_ROLES = {
    1490395401365356556,
    1490395401365356555,
    1490395401365356554,
    1490395401348710489,
    1491520735477235832,
    1490395401336000559,
}

# ================= STATE =================
activity_running = False
activity_message_id = None
activity_number = 4
first_reactor = None
backup_before_strikes = {}

scheduled = []
STATE_FILE = "activity_state.json"


# ================= SAVE / LOAD =================
def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump({
            "activity_running": activity_running,
            "activity_message_id": activity_message_id,
            "activity_number": activity_number
        }, f)


def load_state():
    global activity_running, activity_message_id, activity_number
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            activity_running = data.get("activity_running", False)
            activity_message_id = data.get("activity_message_id", None)
            activity_number = data.get("activity_number", 4)
    except:
        pass


# ================= LOOP =================
@tasks.loop(minutes=1)
async def check_schedule():
    now = datetime.now()

    for item in scheduled[:]:
        if now >= item["time"]:
            guild = bot.get_guild(item["guild"])

            if guild:
                for member in guild.members:
                    if not member.bot:
                        try:
                            await member.send(
                                f"📢 GEPLANTE ANKÜNDIGUNG:\n{item['message']}"
                            )
                        except:
                            pass

            scheduled.remove(item)


# ================= READY =================
@bot.event
async def on_ready():
    load_state()

    print(f"✅ Bot online als {bot.user}")

    bot.add_view(AppealView())

    if not check_schedule.is_running():
        check_schedule.start()

    await bot.change_presence(
        activity=discord.Game(name="🔵 Ruhrstadt")
    )


# ================= REACTION =================
@bot.event
async def on_reaction_add(reaction, user):
    global first_reactor

    if user.bot:
        return

    if not activity_running:
        return

    if reaction.message.id != activity_message_id:
        return

    if str(reaction.emoji) != "✅":
        return

    if first_reactor is None:
        first_reactor = user
        channel = bot.get_channel(1490395401935655043)

        if channel:
            await channel.send(f"🥇 First {user.mention}")


# ================= ACTIVITY =================
@bot.command()
async def activity(ctx, days: int):
    global activity_running, activity_message_id, activity_number
    global first_reactor, backup_before_strikes

    role = ctx.guild.get_role(1490395401365356556)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if activity_running:
        return await ctx.send("❌ Läuft bereits!")

    channel = bot.get_channel(1490395401935655043)

    msg = await channel.send(
        f"**ACTIVITY CHECK**\n\n| {activity_number} |\nWer nicht Reactet Strike\n||@everyone||"
    )

    await msg.add_reaction("✅")

    activity_running = True
    activity_message_id = msg.id
    first_reactor = None
    backup_before_strikes = {}

    save_state()

    await ctx.send("✅ Activity gestartet!")

    await asyncio.sleep(days * 86400)
    await finish_activity(ctx.guild)


# ================= ABORT =================
@bot.command()
async def abbruch(ctx):
    global activity_running

    role = ctx.guild.get_role(1490395401365356556)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    activity_running = False
    save_state()

    await ctx.send("🛑 Activity abgebrochen")


# ================= END =================

import json

used_activity_ids = {
    1501223693345620089,
    1500425476009889863,
    1499739823592837362,
    1498693215073730583,
    1497666708587151431,
    1496535300883611670,
    1495792869531848947,
    1495061932913201212,
    1494049528381177886,
    1493602959731326996,
    1492971321598935280,
    1492122957894389843,
    1491407539911528488,
    1490776002253684767
}


activity_message_id = None
activity_running = False


def save_state():
    data = {
        "activity_message_id": activity_message_id,
        "activity_running": activity_running,
        "used_activity_ids": list(used_activity_ids)
    }

    with open("state.json", "w") as f:
        json.dump(data, f)


def load_state():
    global activity_message_id, activity_running, used_activity_ids

    try:
        with open("state.json", "r") as f:
            data = json.load(f)

            activity_message_id = data.get("activity_message_id")
            activity_running = data.get("activity_running", False)

            used_activity_ids = set(data.get("used_activity_ids", []))

    except:
        used_activity_ids = set()


@bot.command()
async def end(ctx, message_id: int = None):
    global activity_message_id, activity_running, used_activity_ids

    role = ctx.guild.get_role(1490395401365356556)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if message_id:
        activity_message_id = message_id

    if not activity_message_id:
        return await ctx.send("❌ Keine Message ID!")

    if activity_message_id in used_activity_ids:
        return await ctx.send("❌ Diese Activity wurde bereits beendet! Verwende die aktuelle Nachrichten ID!")

    channel = bot.get_channel(1490395401935655043)

    try:
        await channel.fetch_message(activity_message_id)
    except:
        return await ctx.send("❌ Message nicht gefunden!")

    await ctx.send("⏳ Beende Activity...")

    await finish_activity(ctx.guild)

    used_activity_ids.add(activity_message_id)

    activity_running = False
    activity_message_id = None

    save_state()

    await ctx.send("✅ Fertig!")

# ================= FINISH =================
async def finish_activity(guild):
    global activity_running, activity_message_id, activity_number
    global first_reactor, backup_before_strikes

    channel = bot.get_channel(1490395401935655043)
    strike_channel = bot.get_channel(1490395402304749810)

    try:
        msg = await channel.fetch_message(activity_message_id)
    except:
        return

    reacted_ids = set()

    for reaction in msg.reactions:
        if str(reaction.emoji) == "✅":
            async for user in reaction.users():
                if not user.bot:
                    reacted_ids.add(user.id)

    for member in guild.members:
        if member.bot:
            continue

        if any(r.id in EXEMPT_ROLES for r in member.roles):
            continue

        backup_before_strikes[member.id] = [r.id for r in member.roles]

        if member.id in reacted_ids:
            continue

        try:
            r1 = guild.get_role(STRIKE_1)
            r2 = guild.get_role(STRIKE_2)
            r3 = guild.get_role(STRIKE_3)

            if r1 in member.roles:
                await member.remove_roles(r1)
                await member.add_roles(r2)
                level = 2

            elif r2 in member.roles:
                await member.remove_roles(r2)
                await member.add_roles(r3)
                level = 3

            else:
                await member.add_roles(r1)
                level = 1

            await strike_channel.send(
                f"**· Strike {level}**\n"
                f"Warum?: Reactet nicht im Activity Check\n"
                f"| {member.mention} |"
            )

        except:
            pass

    activity_running = False
    activity_message_id = None
    activity_number += 1
    first_reactor = None

    save_state()

    await channel.send("✅ Activity Check beendet!")


# ================= ANNOUNCE =================
@bot.command()
async def announce(ctx, *, message):
    role = ctx.guild.get_role(1490395401365356556)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    await ctx.send("📢 Sende...")

    for member in ctx.guild.members:
        if not member.bot:
            try:
                embed = discord.Embed(
                    title="📢ANKÜNDIGUNG📢",
                    description=message,
                    color=discord.Color.blue()
                )
                await member.send(embed=embed)
            except:
                pass

    await ctx.send("✅ Fertig!")

# ================= WELCOME =================
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1490395401935655038)

    if channel is None:
        return

    embed = discord.Embed(
        title="👋 Herzlich Willkommen",
        description=f"Herzlich Willkommen {member.mention} beim Fanatico Bochum",
        color=discord.Color.blue()
    )

    embed.set_image(url="https://cdn.discordapp.com/attachments/1106263110219735225/1500490057889349742/Screenshot_2026-04-19_165813.png?ex=69f89fc3&is=69f74e43&hm=8e630423e0eb295ac93770873b109b633b35c0e419d2fccb6dda337dfb885740&")

    await channel.send(embed=embed)

# ================= BAN =================

import discord
from discord.ext import commands

BAN_OWNER_ID = 725358263901880402

blacklist_words = [
    "hurensohn",
    "fotze",
    "hure",
    "wichser",
    "fick"
]


# ================= APPEAL MODAL =================
class AppealModal(discord.ui.Modal, title="Ban Einspruch"):

    explanation = discord.ui.TextInput(
        label="Einspruch Erklärung",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):

        try:
            text = self.explanation.value.lower()

            # FILTER
            for word in blacklist_words:
                if word in text:
                    return await interaction.response.send_message(
                        "❌ Einspruch ungültig (Beleidigung erkannt)",
                        ephemeral=True
                    )

            if len(text.split()) < 15:
                return await interaction.response.send_message(
                    "❌ Mindestens 15 Wörter nötig!",
                    ephemeral=True
                )

            # WICHTIG: sofort ACK (verhindert „Interaktion fehlgeschlagen“)
            await interaction.response.defer(ephemeral=True)

            owner = interaction.client.get_user(BAN_OWNER_ID)
            if owner is None:
                owner = await interaction.client.fetch_user(BAN_OWNER_ID)

            embed = discord.Embed(
                title="📩 Neuer Ban Einspruch",
                description=self.explanation.value,
                color=discord.Color.blue()
            )

            embed.add_field(
                name="User",
                value=f"{interaction.user} ({interaction.user.id})",
                inline=False
            )

            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            view = AppealAdminView()
            view.set_user(interaction.user.id)

            try:
                await owner.send(embed=embed, view=view)
            except Exception as e:
                print("DM ERROR OWNER:", e)

            await interaction.followup.send("✅ Einspruch gesendet!")

        except Exception as e:
            print("APPEAL ERROR:", e)
            try:
                await interaction.followup.send("❌ Fehler beim Einspruch!")
            except:
                pass


# ================= USER BUTTON =================
class AppealView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Einspruch",
        style=discord.ButtonStyle.blurple,
        emoji="📩",
        custom_id="appeal_button"
    )
    async def appeal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AppealModal())


# ================= ADMIN VIEW =================
class AppealAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.user_id = None

    def set_user(self, user_id):
        self.user_id = user_id

    @discord.ui.button(label="Annehmen", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = await interaction.client.fetch_user(self.user_id)

        await guild.unban(user)

        try:
            await user.send("✅ Dein Einspruch wurde angenommen. Du bist entbannt.")
        except:
            pass

        await interaction.response.send_message("✅ User entbannt.")

    @discord.ui.button(label="Ablehnen", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = await interaction.client.fetch_user(self.user_id)

        try:
            await user.send("❌ Dein Einspruch wurde abgelehnt.")
        except:
            pass

        await interaction.response.send_message("❌ Abgelehnt.")

    @discord.ui.button(label="Verlängern", style=discord.ButtonStyle.gray)
    async def extend(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "Schreibe z.B: 30d oder perm",
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        msg = await interaction.client.wait_for("message", check=check)

        user = await interaction.client.fetch_user(self.user_id)

        try:
            await user.send(f"⏳ Bann geändert auf: {msg.content}")
        except:
            pass

        await interaction.followup.send(f"✅ Geändert auf {msg.content}")


# ================= BAN COMMAND =================
@bot.command()
async def bann(ctx, member: discord.Member, duration: str, *, reason="Kein Grund angegeben"):

    allowed_role = ctx.guild.get_role(1490395401365356556)

    if allowed_role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    try:

        embed = discord.Embed(
            title="🔨 Du wurdest gebannt",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        view = AppealView()

        # ================= PERM =================
        if duration.lower() == "perm":

            embed.description = (
                f"Du wurdest permanent gebannt.\n\n"
                f"Grund: {reason}\n\n"
                f"Bei Fragen wende dich an Luca oder Backfisch."
            )

            try:
                await member.send(embed=embed, view=view)
            except:
                pass

            await member.ban(reason=reason)

            await ctx.send(f"✅ {member} permanent gebannt.")

        # ================= TEMP =================
        else:

            amount = int(duration[:-1])
            tage_text = "Tag" if amount == 1 else "Tage"

            embed.description = (
                f"Du wurdest gebannt.\n\n"
                f"Dauer: {amount} {tage_text}\n"
                f"Grund: {reason}\n\n"
                f"Du kannst in {amount} {tage_text} wieder joinen.\n\n"
                f"Bei Fragen wende dich an Luca oder Backfisch."
            )

            try:
                await member.send(embed=embed, view=view)
            except:
                pass

            await member.ban(reason=reason)

            await ctx.send(f"✅ {member} für {amount} {tage_text} gebannt.")

            await asyncio.sleep(amount * 86400)

            user = await bot.fetch_user(member.id)
            await ctx.guild.unban(user)

    except Exception as e:
        await ctx.send(f"❌ Fehler: {e}")


# ================= IMPORTANT =================
@bot.event
async def on_ready():
    load_state()

    print(f"✅ Bot online als {bot.user}")

    bot.add_view(AppealView())

    if not check_schedule.is_running():
        check_schedule.start()

    await bot.change_presence(
        activity=discord.Game(name="🔵 Ruhrstadt")
    )

# ================= START BOT =================
bot.run(TOKEN)
