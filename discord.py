import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

import os
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# gespeicherte geplante Nachrichten
scheduled = []

@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")

    await bot.change_presence(
        activity=discord.Game(name="🔵⚪ Ruhrstadt 👊")
    )

    check_schedule.start()


# 📢 SOFORT AN ALLE DM
@bot.command()
async def announce(ctx, *, message):
    await ctx.send("📨 Sende Nachricht an alle...")

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


# ⏳ GEPLANT NACH X TAGEN
@bot.command()
async def schedule(ctx, days: int, *, message):
    time = datetime.now() + timedelta(days=days)

    scheduled.append({
        "time": time,
        "guild": ctx.guild.id,
        "message": message
    })

    await ctx.send(f"⏳ Geplant in {days} Tagen!")


# 🔁 CHECKER
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
                            await member.send(f"📢 GEPLANTE ANKÜNDIGUNG:\n{item['message']}")
                        except:
                            pass

            scheduled.remove(item)


bot.run(TOKEN)
