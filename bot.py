import os
from threading import Thread
from flask import Flask

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

Thread(target=run_web, daemon=True).start()
import discord
from discord.ext import commands
import json
import string

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

try:
    with open("torneos.json", "r") as f:
        torneos = json.load(f)
except:
    torneos = {}

# VISTA DEL BOTON UNIRME (la que ya tenias)
class TorneoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Unirme", style=discord.ButtonStyle.green)
    async def unirme(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal = str(interaction.channel.id)
        if canal not in torneos:
            torneos[canal] = []
        if interaction.user.id not in torneos[canal]:
            torneos[canal].append(interaction.user.id)
            with open("torneos.json", "w") as f:
                json.dump(torneos, f)
            await interaction.response.send_message("Te uniste!", ephemeral=True)
        else:
            await interaction.response.send_message("Ya estabas unido", ephemeral=True)

@bot.command()
async def torneo(ctx, nombre: str = "Torneo"):
    canal = str(ctx.channel.id)
    torneos[canal] = []
    with open("torneos.json", "w") as f:
        json.dump(torneos, f)
    embed = discord.Embed(title=f"🏆 {nombre}", description="Dale a Unirme para entrar")
    embed.add_field(name="Participantes (0)", value="Nadie aun")
    embed.set_footer(text="| ttbot")
    await ctx.send(embed=embed, view=TorneoView())

# COMANDO PARA REPARTIR EN GRUPOS A-Z
@bot.command()
@commands.has_permissions(administrator=True)
async def iniciar(ctx):
    canal = str(ctx.channel.id)
    data = torneos.get(canal, [])
    jugadores_ids = data.get("jugadores", []) if isinstance(data, dict) else data
    if not jugadores_ids:
        return await ctx.send("No hay jugadores")

    import math, string
    total = len(jugadores_ids)
    num_grupos = 1 if total <= 50 else math.ceil(total / 50)
    while num_grupos > 1 and (total // num_grupos) < 48:
        num_grupos -= 1

    base = total // num_grupos
    sobra = total % num_grupos
    letras = list(string.ascii_uppercase)

    # Borra grupos viejos antes de crear nuevos
    for r in list(ctx.guild.roles):
        if r.name.startswith("Grupo "):
            try:
                for m in r.members:
                    try: await m.remove_roles(r)
                    except: pass
                await r.delete()
            except: pass
    for ch in list(ctx.guild.text_channels):
        if "grupo-" in ch.name.lower():
            try: await ch.delete()
            except: pass

    roles_n, canales_n = [], []
    idx = 0
    for i in range(num_grupos):
        letra = letras[i]
        cantidad = base + (1 if i < sobra else 0)

        rol = await ctx.guild.create_role(name=f"Grupo {letra}")
        roles_n.append(rol.id)

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            rol: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            ctx.guild.me: discord.PermissionOverwrite(view_channel=True, manage_messages=True)
        }
        canal_g = await ctx.guild.create_text_channel(f"grupo-{letra.lower()}", overwrites=overwrites)
        canales_n.append(canal_g.id)

        grupo = jugadores_ids[idx: idx+cantidad]
        idx += cantidad
        for uid in grupo:
            m = ctx.guild.get_member(uid)
            if m:
                try: await m.add_roles(rol)
                except: pass
        lista = "\n".join([f"{j+1}. <@{uid}>" for j, uid in enumerate(grupo)])
        await canal_g.send(embed=discord.Embed(title=f"GRUPO {letra} - {len(grupo)} jugadores", description=lista, color=0x2b2d31))

    torneos[canal] = {"jugadores": jugadores_ids, "roles": roles_n, "canales": canales_n}
    with open("torneos.json", "w") as f:
        json.dump(torneos, f)

@bot.command()
@commands.has_permissions(administrator=True)
async def cerrar(ctx):
    canal = str(ctx.channel.id)
    if canal not in torneos:
        return await ctx.send("No hay torneo")

    data = torneos[canal]
    for cid in data.get("canales", []):
        ch = ctx.guild.get_channel(cid)
        if ch:
            try: await ch.delete()
            except: pass
    for rid in data.get("roles", []):
        r = ctx.guild.get_role(rid)
        if r:
            try:
                for m in list(r.members):
                    try: await m.remove_roles(r)
                    except: pass
                await r.delete()
            except: pass

    del torneos[canal]
    with open("torneos.json", "w") as f:
        json.dump(torneos, f)
    await ctx.send("✅ Torneo cerrado. Grupos del A a la Z eliminados y roles quitados.")
import os
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
