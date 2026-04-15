import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta
import asyncio

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
ANNOUNCE_ROLE = 1490395401365356556

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
scheduled = []

activity_running = False
activity_message_id = None
activity_number = 4


# ================= READY =================
@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")
    await bot.change_presence(activity=discord.Game(name="🔵⚪ Ruhrstadt 👊"))


# ================= ANNOUNCE =================
@bot.command()
async def announce(ctx, *, message):
    role = ctx.guild.get_role(ANNOUNCE_ROLE)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    await ctx.send("📨 Sende Nachricht...")

    for member in ctx.guild.members:
        if not member.bot:
            try:
                await member.send(
                    embed=discord.Embed(
                        title="📢 ANKÜNDIGUNG 📢",
                        description=message,
                        color=discord.Color.blue()
                    )
                )
            except:
                pass

    await ctx.send("✅ Fertig!")


# ================= ACTIVITY START =================
@bot.command()
async def activity(ctx, days: int):
    global activity_running, activity_message_id, activity_number

    role = ctx.guild.get_role(1490395401365356556)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung für Activity Command!")

    if activity_running:
        return await ctx.send("❌ Activity läuft bereits!")

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)

    msg = await channel.send(
        f"**ACTIVITY CHECK**\n\n| {activity_number} |\nWer nicht Reactet Strike\n||@everyone||"
    )

    await msg.add_reaction("✅")

    activity_running = True
    activity_message_id = msg.id

    await ctx.send("✅ Activity gestartet!")

    await asyncio.sleep(days * 86400)

    await finish_activity(ctx.guild)

# ================= MANUAL END =================
@bot.command()
async def end(ctx):
    global activity_running

    role = ctx.guild.get_role(1490395401365356556)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung für diesen Command!")

    if not activity_running:
        return await ctx.send("❌ Kein Activity Check aktiv!")

    await finish_activity(ctx.guild)
    await ctx.send("🛑 Activity beendet!")


# ================= FINISH LOGIC =================
async def finish_activity(guild):
    global activity_running, activity_message_id, activity_number

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)
    strike_channel = bot.get_channel(STRIKE_CHANNEL_ID)

    try:
        msg = await channel.fetch_message(activity_message_id)
    except:
        return

    reacted_ids = set()

    for reaction in msg.reactions:
        if reaction.emoji == "✅":
            async for user in reaction.users():
                if not user.bot:
                    reacted_ids.add(user.id)

    for member in guild.members:
        if member.bot:
            continue

        # EXEMPT ROLES → NIE STRIKE
        if any(r.id in EXEMPT_ROLES for r in member.roles):
            continue

        # hat reagiert
        if member.id in reacted_ids:
            continue

        try:
            roles = [r.id for r in member.roles]

            r1 = guild.get_role(STRIKE_1)
            r2 = guild.get_role(STRIKE_2)
            r3 = guild.get_role(STRIKE_3)

            if STRIKE_1 in roles:
                await member.remove_roles(r1)
                await member.add_roles(r2)
                level = 2

            elif STRIKE_2 in roles:
                await member.remove_roles(r2)
                await member.add_roles(r3)
                level = 3

            else:
                await member.add_roles(r1)
                level = 1

            await strike_channel.send(
                f"**· Strike {level}**\n"
                f"**Warum?**: Reactet nicht im Activity Check.\n"
                f"| {member.mention} |"
            )

        except:
            pass

    await channel.send("✅ Activity Check beendet!")

    activity_running = False
    activity_message_id = None
    activity_number += 1


# ================= RUN =================
bot.run(TOKEN)
