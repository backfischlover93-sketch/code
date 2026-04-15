import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta
import asyncio

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    print("❌ TOKEN fehlt! Setze ihn in Railway Variables!")
    exit()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True  # 🔥 WICHTIG FIX

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
activity_users = set()
activity_number = 4


# ===== READY =====
@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")

    await bot.change_presence(
        activity=discord.Game(name="🔵⚪ Ruhrstadt 👊")
    )


# ===== ANNOUNCE =====
@bot.command()
async def announce(ctx, *, message):
    role = ctx.guild.get_role(ANNOUNCE_ROLE)

    if role not in ctx.author.roles:
        await ctx.send("❌ Du hast keine Berechtigung!")
        return

    await ctx.send("📨 Sende Nachricht an alle...")

    for member in ctx.guild.members:
        if not member.bot:
            try:
                embed = discord.Embed(
                    title="📢 ANKÜNDIGUNG 📢",
                    description=message,
                    color=discord.Color.blue()
                )
                await member.send(embed=embed)
            except:
                pass

    await ctx.send("✅ Fertig!")


# ===== SCHEDULE =====
@bot.command()
async def schedule(ctx, days: int, *, message):
    time = datetime.now() + timedelta(days=days)

    scheduled.append({
        "time": time,
        "guild": ctx.guild.id,
        "message": message
    })

    await ctx.send(f"⏳ Geplant in {days} Tagen!")


# ===== ACTIVITY START =====
@bot.command()
async def activity(ctx, days: int):
    global activity_running, activity_message_id, activity_users, activity_number

    role = ctx.guild.get_role(ACTIVITY_ROLE_ID)

    if role not in ctx.author.roles:
        await ctx.send("❌ Keine Berechtigung!")
        return

    if activity_running:
        await ctx.send("❌ Es läuft bereits ein Activity Check!")
        return

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)

    msg = await channel.send(
        f"**ACTIVITY CHECK**\n| {activity_number} |\nWer nicht reagiert bekommt Strike"
    )

    await msg.add_reaction("✅")

    activity_running = True
    activity_message_id = msg.id
    activity_users = set()

    await ctx.send("✅ Activity gestartet!")

    await asyncio.sleep(days * 86400)

    await finish_activity(ctx.guild)


# ===== LIVE REACTION TRACKING (FIX) =====
@bot.event
async def on_reaction_add(reaction, user):
    global activity_users, activity_message_id

    if user.bot:
        return

    if activity_message_id is None:
        return

    if reaction.message.id != activity_message_id:
        return

    if str(reaction.emoji) == "✅":
        activity_users.add(user.id)


# ===== END COMMAND =====
@bot.command()
async def end(ctx):
    if not activity_running:
        await ctx.send("❌ Kein Activity Check aktiv!")
        return

    await finish_activity(ctx.guild)
    await ctx.send("🛑 Activity Check beendet!")


# ===== FINISH LOGIC =====
async def finish_activity(guild):
    global activity_running, activity_message_id, activity_users, activity_number

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)
    strike_channel = bot.get_channel(STRIKE_CHANNEL_ID)

    if not channel:
        return

    try:
        msg = await channel.fetch_message(activity_message_id)
    except:
        return

    role = guild.get_role(ACTIVITY_ROLE_ID)

    for member in guild.members:
        if member.bot:
            continue

        if role not in member.roles:
            continue

        # ❌ NICHT reagiert
        if member.id not in activity_users:

            try:
                if guild.get_role(STRIKE_1) in member.roles:
                    await member.remove_roles(guild.get_role(STRIKE_1))
                    await member.add_roles(guild.get_role(STRIKE_2))

                    await strike_channel.send(
                        f"**· Strike 2**\n**Warum?**: Reactet nicht im Activity Check\n| {member.mention} |"
                    )

                elif guild.get_role(STRIKE_2) in member.roles:
                    await member.remove_roles(guild.get_role(STRIKE_2))
                    await member.add_roles(guild.get_role(STRIKE_3))

                    await strike_channel.send(
                        f"**· Strike 3**\n**Warum?**: Reactet nicht im Activity Check\n| {member.mention} |"
                    )

                else:
                    await member.add_roles(guild.get_role(STRIKE_1))

                    await strike_channel.send(
                        f"**· Strike 1**\n**Warum?**: Reactet nicht im Activity Check\n| {member.mention} |"
                    )

            except Exception as e:
                print("Error:", e)

    await channel.send("✅ Activity Check beendet!")

    # reset
    activity_running = False
    activity_message_id = None
    activity_users = set()
    activity_number += 1


# ===== SCHEDULE LOOP =====
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


# ===== START =====
bot.run(TOKEN)
