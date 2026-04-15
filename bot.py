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

bot = commands.Bot(command_prefix="!", intents=intents)

scheduled = []

# ===== IDs =====
ANNOUNCE_ROLE = 1490395401365356556

ACTIVITY_ROLE_ID = 1493967153261580312
ACTIVITY_CHANNEL_ID = 1493967155430031413
STRIKE_CHANNEL_ID = 1493967156012908673

STRIKE_1 = 1493967152984625308
STRIKE_2 = 1493967152984625307
STRIKE_3 = 1493967152984625305


# ===== READY =====
@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")

    await bot.change_presence(
        activity=discord.Game(name="🔵⚪ Ruhrstadt 👊")
    )

    check_schedule.start()


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


# ===== ACTIVITY CHECK =====
@bot.command()
async def activity(ctx, days: int):
    role = ctx.guild.get_role(ACTIVITY_ROLE_ID)

    if role not in ctx.author.roles:
        await ctx.send("❌ Keine Berechtigung!")
        return

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)

    msg = await channel.send(
        f"**ACTIVITY CHECK**\n| {days} Tage |\nWer nicht reactet bekommt Strike"
    )

    await msg.add_reaction("✅")

    await ctx.send("✅ Activity Check gestartet!")

    await asyncio.sleep(days * 86400)

    msg = await channel.fetch_message(msg.id)

    reacted_users = set()

    for reaction in msg.reactions:
        if str(reaction.emoji) == "✅":
            users = [user async for user in reaction.users()]
            reacted_users.update(users)

    strike_channel = bot.get_channel(STRIKE_CHANNEL_ID)

    for member in ctx.guild.members:
        if member.bot:
            continue

        if role not in member.roles:
            continue

        if member not in reacted_users:
            try:
                if ctx.guild.get_role(STRIKE_1) in member.roles:
                    await member.remove_roles(ctx.guild.get_role(STRIKE_1))
                    await member.add_roles(ctx.guild.get_role(STRIKE_2))

                    await strike_channel.send(
                        f"**· Strike 2**\n**Warum?**: Reactet nicht im Activity Check\n| {member.mention} |"
                    )

                elif ctx.guild.get_role(STRIKE_2) in member.roles:
                    await member.remove_roles(ctx.guild.get_role(STRIKE_2))
                    await member.add_roles(ctx.guild.get_role(STRIKE_3))

                    await strike_channel.send(
                        f"**· Strike 3**\n**Warum?**: Reactet nicht im Activity Check\n| {member.mention} |"
                    )

                else:
                    await member.add_roles(ctx.guild.get_role(STRIKE_1))

                    await strike_channel.send(
                        f"**· Strike 1**\n**Warum?**: Reactet nicht im Activity Check\n| {member.mention} |"
                    )

            except:
                pass

    await channel.send("✅ Activity Check beendet!")


# ===== FIX: CHECKER STARTET ERST WENN BOT READY IST =====
@check_schedule.before_loop
async def before_check_schedule():
    await bot.wait_until_ready()


# ===== CHECK SCHEDULE =====
# ===== CHECK SCHEDULE =====
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


# WICHTIG: MUSS NACH DER FUNKTION STEHEN
@check_schedule.before_loop
async def before_check_schedule():
    await bot.wait_until_ready()


# ===== START =====
bot.run(TOKEN)
