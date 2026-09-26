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
    total = len(jugadores_ids)

    letras = list(string.ascii_uppercase)
    num_grupos = -(-total // por_sala)

    if num_grupos > 26:
        return await ctx.send("Son mas de 26 grupos (1248 jugadores)")

    await ctx.send(f"Repartiendo {total} jugadores en {num_grupos} grupos (A-{letras[num_grupos-1]})...")

    for i in range(num_grupos):
        letra = letras[i]
        rol = await ctx.guild.create_role(name=f"Grupo {letra}")
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            rol: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        canal_grupo = await ctx.guild.create_text_channel(f"🔒grupo-{letra.lower()}", overwrites=overwrites)

        inicio = i * por_sala
        fin = inicio + por_sala
        grupo = jugadores_ids[inicio:fin]

        for uid in grupo:
            member = ctx.guild.get_member(uid)
            if member:
                try:
                    await member.add_roles(rol)
                except:
                    pass

        lista = "\n".join([f"{j+1}. <@{uid}>" for j, uid in enumerate(grupo)])
        embed = discord.Embed(title=f"GRUPO {letra} - {len(grupo)} jugadores", description=lista)
        await canal_grupo.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def cerrar(ctx):
    canal = str(ctx.channel.id)
    if canal in torneos:
        del torneos[canal]
        with open("torneos.json", "w") as f:
            json.dump(torneos, f)
        await ctx.send("Torneo cerrado")
    else:
        await ctx.send("No hay torneo")

import os
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
