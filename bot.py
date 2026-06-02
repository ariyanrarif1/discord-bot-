import discord
from discord.ext import commands
import gspread
from google.oauth2.service_account import Credentials
import json
import os
import asyncio

# ================== GOOGLE SHEETS ==================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

gc = gspread.authorize(creds)
sheet = gc.open("Crime BlackList | EN 01").sheet1

# ================== DISCORD BOT ==================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ================== ADD BLACKLIST ==================

@bot.command()
async def bl(ctx):
    questions = [
        "Nickname",
        "Additional",
        "Discord ID",
        "Reason",
        "Duration",
        "Dates",
        "By",
        "Extra Info"
    ]

    answers = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for q in questions:
        await ctx.send(f"➡ {q} লিখো:")
        try:
            msg = await bot.wait_for("message", check=check, timeout=120)
            answers.append(msg.content)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Timeout!")
            return

    sheet.append_row(answers)
    await ctx.send(f"✅ Added `{answers[0]}`")

# ================== CHECK ==================

@bot.command()
async def chek(ctx):
    await ctx.send("Nickname লিখো:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        name = msg.content.lower()
    except asyncio.TimeoutError:
        await ctx.send("⏰ Timeout!")
        return

    data = sheet.get_all_records()

    for row in data:
        if str(row.get("Nickname", "")).lower() == name:
            await ctx.send("```\n" + str(row) + "\n```")
            return

    await ctx.send("❌ Not found")

# ================== READ ==================

@bot.command()
async def read(ctx, limit: int = 10):
    data = sheet.get_all_records()[-limit:]

    if not data:
        await ctx.send("Empty sheet")
        return

    msg = ""

    for row in data:
        msg += str(row) + "\n"

        if len(msg) > 1800:
            await ctx.send(f"```\n{msg}\n```")
            msg = ""

    if msg:
        await ctx.send(f"```\n{msg}\n```")

# ================== DELETE ==================

@bot.command(name="del")
async def delete(ctx):
    await ctx.send("Nickname লিখো:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        name = msg.content.lower()
    except asyncio.TimeoutError:
        await ctx.send("⏰ Timeout!")
        return

    values = sheet.get_all_values()

    for i, row in enumerate(values, start=1):
        if row and row[0].lower() == name:
            sheet.delete_rows(i)
            await ctx.send("✅ Deleted")
            return

    await ctx.send("❌ Not found")

# ================== RUN BOT ==================

bot.run(os.getenv("DISCORD_TOKEN"))
