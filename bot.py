import discord
from discord.ext import commands
import os
import asyncio

import discord
from discord.ext import commands
import os
import asyncio

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= IDS =================
ACTIVITY_ADMIN_ROLE = 1493967153261580312

ACTIVITY_CHANNEL_ID = 1493967155430031413
STRIKE_CHANNEL_ID = 1493967156012908673

STRIKE_1 = 1493967152984625308
STRIKE_2 = 1493967152984625307
STRIKE_3 = 1493967152984625305

EXEMPT_ROLES = {
    1493967153261580312,
    1493967153261580311,
    1493967153261580310,
    1493967153261580308,
    1493967152984625304,
}

# ================= STATE =================
activity_running = False
activity_message_id = None
activity_number = 4

activity_reacted = set()
first_reactor = None

# rollback storage für !delete
backup_before_strikes = {}

# ================= READY =================
@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")


# ================= FIRST REACTION =================
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

        channel = bot.get_channel(ACTIVITY_CHANNEL_ID)
        if channel:
            asyncio.create_task(
                channel.send(f"🥇 First {user.mention}")
            )


# ================= ACTIVITY START =================
@bot.command()
async def activity(ctx, days: int):
    global activity_running, activity_message_id, activity_number
    global activity_reacted, first_reactor, backup_before_strikes

    role = ctx.guild.get_role(ACTIVITY_ADMIN_ROLE)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if activity_running:
        return await ctx.send("❌ Läuft bereits!")

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)

    msg = await channel.send(
        f"**ACTIVITY CHECK**\n\n| {activity_number} |\nWer nicht Reactet Strike\n||@everyone||"
    )

    await msg.add_reaction("✅")

    activity_running = True
    activity_message_id = msg.id
    activity_reacted = set()
    first_reactor = None
    backup_before_strikes = {}

    await ctx.send("✅ Activity gestartet!")

    await asyncio.sleep(days * 86400)
    await finish_activity(ctx.guild)


# ================= ABBRUCH =================
@bot.command()
async def abbruch(ctx):
    global activity_running

    role = ctx.guild.get_role(ACTIVITY_ADMIN_ROLE)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if not activity_running:
        return await ctx.send("❌ Kein Activity Check aktiv!")

    activity_running = False

    await ctx.send("🛑 Activity Check abgebrochen (keine Strikes vergeben)")


# ================= DELETE / ROLLBACK =================
@bot.command()
async def delete(ctx):
    global backup_before_strikes, activity_running

    role = ctx.guild.get_role(ACTIVITY_ADMIN_ROLE)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if not backup_before_strikes:
        return await ctx.send("❌ Nichts zum Zurücksetzen!")

    guild = ctx.guild

    for member_id, roles in backup_before_strikes.items():
        member = guild.get_member(member_id)
        if not member:
            continue

        try:
            current_roles = [r for r in member.roles if r.name != "@everyone"]

            # alles Strike entfernen
            for r in [STRIKE_1, STRIKE_2, STRIKE_3]:
                role_obj = guild.get_role(r)
                if role_obj in current_roles:
                    await member.remove_roles(role_obj)

            # alte Rollen wiedergeben
            for r_id in roles:
                role_obj = guild.get_role(r_id)
                if role_obj:
                    await member.add_roles(role_obj)

        except:
            pass

    backup_before_strikes = {}
    activity_running = False

    await ctx.send("♻️ Activity Check komplett zurückgesetzt!")


# ================= FINISH =================
async def finish_activity(guild):
    global activity_running, activity_message_id, activity_number
    global first_reactor, backup_before_strikes

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

        if any(r.id in EXEMPT_ROLES for r in member.roles):
            continue

        # backup speichern
        backup_before_strikes[member.id] = [r.id for r in member.roles]

        if member.id in reacted_ids:
            continue

        try:
            r1 = guild.get_role(STRIKE_1)
            r2 = guild.get_role(STRIKE_2)
            r3 = guild.get_role(STRIKE_3)

            roles = [r.id for r in member.roles]

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
                f"**Warum?:** Reactet nicht im Activity Check.\n"
                f"| {member.mention} |"
            )

        except:
            pass

    # reset
    activity_running = False
    activity_message_id = None
    activity_number += 1
    first_reactor = None

    await channel.send("✅ Activity Check beendet!")


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= IDS =================
ACTIVITY_ADMIN_ROLE = 1493967153261580312

ACTIVITY_CHANNEL_ID = 1493967155430031413
STRIKE_CHANNEL_ID = 1493967156012908673

STRIKE_1 = 1493967152984625308
STRIKE_2 = 1493967152984625307
STRIKE_3 = 1493967152984625305

EXEMPT_ROLES = {
    1493967153261580312,
    1493967153261580311,
    1493967153261580310,
    1493967153261580308,
    1493967152984625304,
}

# ================= STATE =================
activity_running = False
activity_message_id = None
activity_number = 4

activity_reacted = set()
first_reactor = None

# rollback storage für !delete
backup_before_strikes = {}

# ================= READY =================
@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")


# ================= FIRST REACTION =================
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

        channel = bot.get_channel(ACTIVITY_CHANNEL_ID)
        if channel:
            asyncio.create_task(
                channel.send(f"🥇 First {user.mention}")
            )


# ================= ACTIVITY START =================
@bot.command()
async def activity(ctx, days: int):
    global activity_running, activity_message_id, activity_number
    global activity_reacted, first_reactor, backup_before_strikes

    role = ctx.guild.get_role(ACTIVITY_ADMIN_ROLE)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if activity_running:
        return await ctx.send("❌ Läuft bereits!")

    channel = bot.get_channel(ACTIVITY_CHANNEL_ID)

    msg = await channel.send(
        f"**ACTIVITY CHECK**\n\n| {activity_number} |\nWer nicht Reactet Strike\n||@everyone||"
    )

    await msg.add_reaction("✅")

    activity_running = True
    activity_message_id = msg.id
    activity_reacted = set()
    first_reactor = None
    backup_before_strikes = {}

    await ctx.send("✅ Activity gestartet!")

    await asyncio.sleep(days * 86400)
    await finish_activity(ctx.guild)


# ================= ABBRUCH =================
@bot.command()
async def abbruch(ctx):
    global activity_running

    role = ctx.guild.get_role(ACTIVITY_ADMIN_ROLE)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if not activity_running:
        return await ctx.send("❌ Kein Activity Check aktiv!")

    activity_running = False

    await ctx.send("🛑 Activity Check abgebrochen (keine Strikes vergeben)")


# ================= DELETE / ROLLBACK =================
@bot.command()
async def delete(ctx):
    global backup_before_strikes, activity_running

    role = ctx.guild.get_role(ACTIVITY_ADMIN_ROLE)

    if role not in ctx.author.roles:
        return await ctx.send("❌ Keine Berechtigung!")

    if not backup_before_strikes:
        return await ctx.send("❌ Nichts zum Zurücksetzen!")

    guild = ctx.guild

    for member_id, roles in backup_before_strikes.items():
        member = guild.get_member(member_id)
        if not member:
            continue

        try:
            current_roles = [r for r in member.roles if r.name != "@everyone"]

            # alles Strike entfernen
            for r in [STRIKE_1, STRIKE_2, STRIKE_3]:
                role_obj = guild.get_role(r)
                if role_obj in current_roles:
                    await member.remove_roles(role_obj)

            # alte Rollen wiedergeben
            for r_id in roles:
                role_obj = guild.get_role(r_id)
                if role_obj:
                    await member.add_roles(role_obj)

        except:
            pass

    backup_before_strikes = {}
    activity_running = False

    await ctx.send("♻️ Activity Check komplett zurückgesetzt!")


# ================= FINISH =================
async def finish_activity(guild):
    global activity_running, activity_message_id, activity_number
    global first_reactor, backup_before_strikes

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

        if any(r.id in EXEMPT_ROLES for r in member.roles):
            continue

        # backup speichern
        backup_before_strikes[member.id] = [r.id for r in member.roles]

        if member.id in reacted_ids:
            continue

        try:
            r1 = guild.get_role(STRIKE_1)
            r2 = guild.get_role(STRIKE_2)
            r3 = guild.get_role(STRIKE_3)

            roles = [r.id for r in member.roles]

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
                f"**Warum?:** Reactet nicht im Activity Check.\n"
                f"| {member.mention} |"
            )

        except:
            pass

    # reset
    activity_running = False
    activity_message_id = None
    activity_number += 1
    first_reactor = None

    await channel.send("✅ Activity Check beendet!")
