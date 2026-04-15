import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta
import asyncio

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    print("❌ TOKEN fehlt!")
    exit()

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

scheduled = []

# ===== IDS =====
ANNOUNCE_ROLE = 1493967153261580312

ACTIVITY_CHANNEL_ID = 1493967155430031413
STRIKE_CHANNEL_ID = 1493967156012908673

STRIKE_1 = 1493967152984625308
STRIKE_2 = 1493967152984625307
STRIKE_3 = 1493967152984625305


# ===== STATE =====
activity_running = False
activity_message_id = None
activity_number = 4


# ===== READY =====
@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")
    await bot.change_presence(activity=discord.Game(name="🔵⚪ Ruhrstadt 👊"))


# ===== ANNOUNCE =====
@bot.command()
async def announce(ctx, *, message):
    role = ctx.guild.get_role(ANNOUNCE_ROLE)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    await ctx.send("📨 sende...")

    for m in ctx.guild.members:
        if not m.bot:
            try:
                await m.send(f"📢 {message}")
            except:
                pass

    await ctx.send("✅ fertig")


# ===== ACTIVITY START =====
@bot.command()
async def activity(ctx, days: int):
    global activity_running, activity_message_id, activity_number

    if activity_running:
        return await ctx.send("❌ Activity läuft schon!")

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)

    msg = await channel.send(
        f"**ACTIVITY CHECK**\n| {activity_number} |\nReagiere mit ✅ sonst Strike!"
    )

    await msg.add_reaction("✅")

    activity_message_id = msg.id
    activity_running = True

    await ctx.send("✅ Activity Check gestartet!")

    await asyncio.sleep(days * 86400)
    await finish_activity(ctx.guild)


# ===== MANUAL END =====
@bot.command()
async def end(ctx):
    if not activity_running:
        return await ctx.send("❌ Kein Activity Check aktiv!")

    await finish_activity(ctx.guild)
    await ctx.send("🛑 Activity Check beendet!")


# ===== STRIKE LOGIC (100% FIXED) =====
async def finish_activity(guild):
    global activity_running, activity_message_id, activity_number

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)
    strike_channel = bot.get_channel(STRIKE_CHANNEL_ID)

    if not channel or not activity_message_id:
        return

    try:
        msg = await channel.fetch_message(activity_message_id)
    except:
        return

    # ===== USERS DIE REAGIERT HABEN =====
    reacted_ids = set()

    for reaction in msg.reactions:
        if reaction.emoji == "✅":
            async for user in reaction.users():
                if not user.bot:
                    reacted_ids.add(user.id)

    # ===== STRIKE ROLES =====
    strike1 = guild.get_role(STRIKE_1)
    strike2 = guild.get_role(STRIKE_2)
    strike3 = guild.get_role(STRIKE_3)

    # ===== ALLE MEMBERS CHECKEN =====
    for member in guild.members:
        if member.bot:
            continue

        # ❌ NICHT reagiert
        if member.id not in reacted_ids:

            try:
                # STRIKE 2 → 3
                if strike2 in member.roles:
                    await member.remove_roles(strike2)
                    await member.add_roles(strike3)

                    await strike_channel.send(
                        f"**Strike 3** ❌ Activity Check\n{member.mention}"
                    )

                # STRIKE 1 → 2
                elif strike1 in member.roles:
                    await member.remove_roles(strike1)
                    await member.add_roles(strike2)

                    await strike_channel.send(
                        f"**Strike 2** ❌ Activity Check\n{member.mention}"
                    )

                # KEIN STRIKE → 1
                else:
                    await member.add_roles(strike1)

                    await strike_channel.send(
                        f"**Strike 1** ❌ Activity Check\n{member.mention}"
                    )

            except Exception as e:
                print("Strike Fehler:", e)

    await channel.send(f"✅ Activity Check #{activity_number} beendet!")

    activity_number += 1
    activity_running = False
    activity_message_id = None


# ===== SCHEDULE SYSTEM =====
@tasks.loop(minutes=1)
async def check_schedule():
    now = datetime.now()

    for item in scheduled[:]:
        if now >= item["time"]:
            guild = bot.get_guild(item["guild"])

            if guild:
                for m in guild.members:
                    if not m.bot:
                        try:
                            await m.send(item["message"])
                        except:
                            pass

            scheduled.remove(item)


bot.run(TOKEN)
