import discord
from discord.ext import commands, tasks
import os
from datetime import datetime
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


# ===== ACTIVITY START =====
@bot.command()
async def activity(ctx, days: int):
    global activity_running, activity_message_id, activity_number

    if activity_running:
        return await ctx.send("❌ Läuft schon!")

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)

    msg = await channel.send(
        f"""**ACTIVITY CHECK**

| {activity_number} |
Wer nicht Reactet Strike
||@everyone||"""
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
    await ctx.send("🛑 beendet")


# ===== STRIKE SYSTEM =====
async def finish_activity(guild):
    global activity_running, activity_message_id, activity_number

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)
    strike_channel = bot.get_channel(STRIKE_CHANNEL_ID)

    msg = await channel.fetch_message(activity_message_id)

    reacted_ids = set()

    for reaction in msg.reactions:
        if reaction.emoji == "✅":
            async for user in reaction.users():
                if not user.bot:
                    reacted_ids.add(user.id)

    strike1 = guild.get_role(STRIKE_1)
    strike2 = guild.get_role(STRIKE_2)
    strike3 = guild.get_role(STRIKE_3)

    for member in guild.members:
        if member.bot:
            continue

        if member.id in reacted_ids:
            continue

        try:
            # ===== STRIKE 3 =====
            if strike2 in member.roles:
                await member.remove_roles(strike2)
                await member.add_roles(strike3)

                await strike_channel.send(
                    f"""· Strike 3

Warum?: Reactet nicht im Activity Check.
| {member.mention} |"""
                )

            # ===== STRIKE 2 =====
            elif strike1 in member.roles:
                await member.remove_roles(strike1)
                await member.add_roles(strike2)

                await strike_channel.send(
                    f"""· Strike 2

Warum?: Reactet nicht im Activity Check.
| {member.mention} |"""
                )

            # ===== STRIKE 1 =====
            else:
                await member.add_roles(strike1)

                await strike_channel.send(
                    f"""· Strike 1

Warum?: Reactet nicht im Activity Check.
| {member.mention} |"""
                )

        except Exception as e:
            print("Strike Fehler:", e)

    await channel.send(f"✅ Activity Check #{activity_number} beendet!")

    activity_number += 1
    activity_running = False
    activity_message_id = None


# ===== START =====
bot.run(TOKEN)
