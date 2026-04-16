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

    # FIX: TASK START HIER
    if not check_schedule.is_running():
        check_schedule.start()


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
@bot.command()
async def end(ctx, message_id: int = None):
    global activity_message_id, activity_running

    role = ctx.guild.get_role(1490395401365356556)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if message_id:
        activity_message_id = message_id

    if not activity_message_id:
        return await ctx.send("❌ Keine Message ID!")

    channel = bot.get_channel(1490395401935655043)

    try:
        await channel.fetch_message(activity_message_id)
    except:
        return await ctx.send("❌ Message nicht gefunden!")

    await ctx.send("⏳ Beende Activity...")

    await finish_activity(ctx.guild)

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


# ================= START BOT =================
bot.run(TOKEN)
