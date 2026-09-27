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
async def iniciar(ctx, por_sala: int = 48):
    canal = str(ctx.channel.id)

    if canal not in torneos or len(torneos[canal]) == 0:
        return await ctx.send("No hay jugadores we")

    jugadores_ids = torneos[canal]
    if isinstance(jugadores_ids, dict): # por si se guardo mal antes
        jugadores_ids = jugadores_ids.get("jugadores", [])

    total = len(jugadores_ids)
    letras = list(string.ascii_uppercase)
    num_grupos = -(-total // por_sala)

    if num_grupos > 26:
        return await ctx.send(f"Son mas de 26 grupos ({total} jugadores) we")

    await ctx.send(f"Repartiendo {total} jugadores en {num_grupos} grupos (A-{letras[num_grupos-1]})...")

    # 1. Borra todo lo viejo al instante antes de crear lo nuevo
    for rol in ctx.guild.roles:
        if rol.name.startswith("Grupo "):
            try:
                for m in rol.members[:]:
                    try: await m.remove_roles(rol)
                    except: pass
                await rol.delete()
            except: pass
    for c in ctx.guild.text_channels:
        if "grupo-" in c.name:
            try: await c.delete()
            except: pass

    roles_nuevos = []
    canales_nuevos = []

    for i in range(num_grupos):
        letra = letras[i]
        rol = await ctx.guild.create_role(name=f"Grupo {letra}")
        roles_nuevos.append(rol.id)

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            rol: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            ctx.guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        canal_grupo = await ctx.guild.create_text_channel(f"🔒 grupo-{letra.lower()}", overwrites=overwrites)
        canales_nuevos.append(canal_grupo.id)

        inicio = i * por_sala
        fin = inicio + por_sala
        grupo = jugadores_ids[inicio:fin]

        for uid in grupo:
            member = ctx.guild.get_member(uid)
            if member:
                try: await member.add_roles(rol)
                except: pass

        lista = "\n".join([f"{j+1}. <@{uid}>" for j, uid in enumerate(grupo)])
        embed = discord.Embed(title=f"GRUPO {letra} - {len(grupo)} jugadores", description=lista)
        await canal_grupo.send(embed=embed)

    # Guardamos los IDs para el cerrar
    torneos[canal] = {
        "jugadores": jugadores_ids,
        "roles": roles_nuevos,
        "canales": canales_nuevos
    }
    with open("torneos.json", "w") as f:
        json.dump(torneos, f)

    await ctx.send("✅ Grupos creados")

@bot.command()
@commands.has_permissions(administrator=True)
async def cerrar(ctx):
    canal_id = str(ctx.channel.id)
    if canal_id not in torneos:
        await ctx.send("No hay torneo")
        return

    await ctx.send("Borrando todo al instante...")
    data = torneos[canal_id]

    # Borra canales por ID
    for cid in data.get("canales", []):
        ch = ctx.guild.get_channel(cid)
        if ch:
            try: await ch.delete()
            except: pass

    # Quita rol a jugadores y borra rol
    for rid in data.get("roles", []):
        rol = ctx.guild.get_role(rid)
        if rol:
            for m in rol.members[:]:
                try: await m.remove_roles(rol)
                except: pass
            try: await rol.delete()
            except: pass

    del torneos[canal_id]
    with open("torneos.json", "w") as f:
        json.dump(torneos, f)

    await ctx.send("✅ Torneo cerrado. Roles y grupos eliminados al instante.")

import os
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
