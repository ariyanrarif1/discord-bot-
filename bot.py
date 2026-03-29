import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

# ---------------- Discord Bot Setup ----------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Google Sheets Setup ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Crime BlackList | EN 01").sheet1  # replace with your sheet name

# ---------------- Bot Events ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---------------- Commands ----------------

# 1️⃣ Interactive Blacklist Add
@bot.command()
async def bl(ctx):
    questions = [
        "Nickname",
        "Additional",
        "Discord Tag / ID",
        "Reason",
        "Blacklist Duration",
        "Blacklist Dates",
        "by",
        "Additional Info"
    ]
    answers = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for question in questions:
        await ctx.send(f"➡ Please enter **{question}**:")
        try:
            msg = await bot.wait_for("message", check=check, timeout=120)
            answers.append(msg.content)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Timeout! Command cancelled.")
            return

    try:
        sheet.append_row(answers)
        await ctx.send(f"✅ Blacklist entry added for `{answers[0]}` successfully!")
    except Exception as e:
        await ctx.send(f"❌ Error writing to sheet: {e}")
        print("Error:", e)

# 2️⃣ Interactive Name Check
@bot.command()
async def chek(ctx):
    await ctx.send("➡ Please enter the **Nickname** to check:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        search_name = msg.content.strip()
    except asyncio.TimeoutError:
        await ctx.send("⏰ Timeout! Command cancelled.")
        return

    try:
        data = sheet.get_all_records()
        found = False
        for row in data:
            if str(row.get("Nickname","")).lower() == search_name.lower():
                found = True
                details = "\n".join([f"{k}: {v}" for k,v in row.items()])
                await ctx.send(f"✅ Found `{search_name}`:\n```\n{details}\n```")
                break
        if not found:
            await ctx.send(f"❌ Name `{search_name}` not found in the sheet.")
    except Exception as e:
        await ctx.send(f"❌ Error reading sheet: {e}")
        print("Error:", e)

# 3️⃣ Read last N rows (default 10)
@bot.command()
async def read(ctx, limit: int = 10):
    try:
        data = sheet.get_all_records()
        if not data:
            await ctx.send("Sheet is empty!")
            return
        
        data = data[-limit:]
        msg = " | ".join(data[0].keys()) + "\n"
        for row in data:
            row_text = " | ".join(str(v) for v in row.values())
            if len(msg) + len(row_text) + 1 > 1900:
                await ctx.send(f"```\n{msg}```")
                msg = ""
            msg += row_text + "\n"
        if msg:
            await ctx.send(f"```\n{msg}```")
    except Exception as e:
        await ctx.send(f"❌ Error reading sheet: {e}")
        print("Error:", e)

@bot.command(name="del")
async def del_row(ctx):
    await ctx.send("➡ Please enter the **Nickname** to delete:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        del_name = msg.content.strip()
    except asyncio.TimeoutError:
        await ctx.send("⏰ Timeout! Command cancelled.")
        return

    await ctx.send(f"⚠ Are you sure you want to delete `{del_name}`? Type **YES** to confirm.")

    try:
        confirm = await bot.wait_for("message", check=check, timeout=30)
        if confirm.content.strip().upper() != "YES":
            await ctx.send("❌ Deletion cancelled.")
            return
    except asyncio.TimeoutError:
        await ctx.send("⏰ Timeout! Deletion cancelled.")
        return

    try:
        all_values = sheet.get_all_values()  # raw rows
        found = False
        for idx, row in enumerate(all_values, start=1):  # rows are 1-indexed
            if len(row) > 0 and row[0].strip().lower() == del_name.lower():
                found = True
                sheet.delete_rows(idx)  # ✅ works now
                await ctx.send(f"✅ Row for `{del_name}` has been deleted successfully!")
                break
        if not found:
            await ctx.send(f"❌ Name `{del_name}` not found in the sheet.")
    except Exception as e:
        await ctx.send(f"❌ Error deleting row: {e}")
        print("Error:", e)

# ---------------- Run Bot ----------------
import os
client.run(os.getenv("DISCORD_TOKEN"))