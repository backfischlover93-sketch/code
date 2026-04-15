import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta
import asyncio

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    print("❌ TOKEN fehlt!")
    exit()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

scheduled = []

# ===== IDs =====
ANNOUNCE_ROLE = 1493967153261580312

ACTIVITY_ROLE_ID = 1493967153261580312
ACTIVITY_CHANNEL_ID = 1493967155430031413
STRIKE_CHANNEL_ID = 1493967156012908673

STRIKE_1 = 1493967152984625308
STRIKE_2 = 1493967152984625307
STRIKE_3 = 1493967152984625305


# ===== ACTIVITY STATE =====
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

    await ctx.send("📨 Sende...")

    for m in ctx.guild.members:
        if not m.bot:
            try:
                await m.send(embed=discord.Embed(
                    title="📢 ANKÜNDIGUNG",
                    description=message,
                    color=discord.Color.blue()
                ))
            except:
                pass

    await ctx.send("✅ Fertig!")


# ===== ACTIVITY START =====
@bot.command()
async def activity(ctx, days: int):
    global activity_running, activity_message_id, activity_number

    role = ctx.guild.get_role(ACTIVITY_ROLE_ID)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if activity_running:
        return await ctx.send("❌ Läuft schon!")

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)

    msg = await channel.send(
        f"**ACTIVITY CHECK**\n| {activity_number} |\nWer nicht reagiert bekommt Strike"
    )

    await msg.add_reaction("✅")

    activity_message_id = msg.id
    activity_running = True

    await ctx.send("✅ gestartet")

    await asyncio.sleep(days * 86400)
    await finish_activity(ctx.guild)


# ===== END COMMAND =====
@bot.command()
async def end(ctx):
    if not activity_running:
        return await ctx.send("❌ Kein Activity Check")

    await finish_activity(ctx.guild)
    await ctx.send("🛑 beendet")


# ===== FINISH LOGIC =====
async def finish_activity(guild):
    global activity_running, activity_message_id, activity_number

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)
    strike_channel = bot.get_channel(STRIKE_CHANNEL_ID)

    msg = await channel.fetch_message(activity_message_id)

    reacted_ids = set()

    for reaction in msg.reactions:
        if str(reaction.emoji) == "✅":
            async for user in reaction.users():
                reacted_ids.add(user.id)

    role = guild.get_role(ACTIVITY_ROLE_ID)

    for member in guild.members:
        if member.bot:
            continue

        if role not in member.roles:
            continue

        if member.id in reacted_ids:
            continue

        # STRIKE SYSTEM
        try:
            if guild.get_role(STRIKE_1) in member.roles:
                await member.remove_roles(guild.get_role(STRIKE_1))
                await member.add_roles(guild.get_role(STRIKE_2))

                await strike_channel.send(
                    f"**· Strike 2**\nWarum: Activity Check\n{member.mention}"
                )

            elif guild.get_role(STRIKE_2) in member.roles:
                await member.remove_roles(guild.get_role(STRIKE_2))
                await member.add_roles(guild.get_role(STRIKE_3))

                await strike_channel.send(
                    f"**· Strike 3**\nWarum: Activity Check\n{member.mention}"
                )

            else:
                await member.add_roles(guild.get_role(STRIKE_1))

                await strike_channel.send(
                    f"**· Strike 1**\nWarum: Activity Check\n{member.mention}"
                )

        except:
            pass

    await channel.send(f"✅ Activity Check #{activity_number} beendet!")

    activity_number += 1
    activity_running = False
    activity_message_id = None


# ===== SCHEDULE =====
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
