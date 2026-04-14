import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    print("❌ TOKEN fehlt! Setze ihn in Railway Variables!")
    exit()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

scheduled = []

@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")

    await bot.change_presence(
        activity=discord.Game(name="🔵⚪ Ruhrstadt 👊")
    )

    check_schedule.start()


@bot.command()
async def announce(ctx, *, message):
    role = ctx.guild.get_role(1490395401365356556)

    if role not in ctx.author.roles:
        await ctx.send("❌ Du hast keine Berechtigung für diesen Command!")
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


@bot.command()
async def schedule(ctx, days: int, *, message):
    time = datetime.now() + timedelta(days=days)

    scheduled.append({
        "time": time,
        "guild": ctx.guild.id,
        "message": message
    })

    await ctx.send(f"⏳ Geplant in {days} Tagen!")


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
