# ============================================================
# TTBOT - ORGANIZADOR DE TORNEOS PRO - ANTI-ROMPER
# Versión Grande / Segura / 24/7 Render
# ============================================================
import os
import json
import random
import asyncio
import datetime
import discord
from discord.ext import commands
from flask import Flask
import threading

# ---------------- KEEP ALIVE PARA RENDER ----------------
app = Flask(__name__)
@app.route('/')
def home():
    return "ttbot online - torneo pro"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web, daemon=True).start()

# ---------------- CONFIG ----------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
DATA_FILE = "torneos.json"
MAX_JUGADORES = 128
MIN_JUGADORES = 2
COOLDOWN_UNIRME = 5
ADMIN_ROL_NOMBRE = "Admin Torneo"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ---------------- BASE DE DATOS ----------------
def cargar_datos():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"torneos": {}, "bans": {}, "stats": {}, "config": {}}

def guardar_datos():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"Error guardando: {e}")

db = cargar_datos()
if "torneos" not in db: db["torneos"] = {}
if "bans" not in db: db["bans"] = {}
if "stats" not in db: db["stats"] = {}
if "config" not in db: db["config"] = {}

def get_torneo(gid):
    gid = str(gid)
    if gid not in db["torneos"]:
        db["torneos"][gid] = {
            "activo": False, "jugadores": [], "ronda": 0,
            "bracket": [], "ganadores": [], "perdedores": [],
            "pausado": False, "creador": None, "inicio": None,
            "nombre": "Torneo", "modo": "1v1", "max": MAX_JUGADORES,
            "canal": None, "reportes": []
        }
    return db["torneos"][gid]

def es_admin(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    for rol in ctx.author.roles:
        if rol.name.lower() in ["admin torneo", "admin", "moderador", "organizador"]:
            return True
    return False

def esta_baneado(gid, uid):
    return str(uid) in db["bans"].get(str(gid), [])

def registrar_stats(uid, gano=False):
    uid = str(uid)
    if uid not in db["stats"]:
        db["stats"][uid] = {"jugados": 0, "ganados": 0, "perdidos": 0}
    db["stats"][uid]["jugados"] += 1
    if gano: db["stats"][uid]["ganados"] += 1
    else: db["stats"][uid]["perdidos"] += 1

def embed(titulo, desc, color=0x00ff00):
    return discord.Embed(title=titulo, description=desc, color=color, timestamp=datetime.datetime.now())

# ---------------- EVENTOS ----------------
@bot.event
async def on_ready():
    print(f"✅ TTBOT ONLINE como {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!ayuda | Torneos Pro"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Te faltó un dato. Pon `!ayuda` para ver cómo se usa.")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Espera {int(error.retry_after)}s, no hagas spam.")
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send("🚫 No tienes permiso para eso, solo admins.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Ese usuario no existe. Usa @usuario.")
        return
    print(f"Error: {error}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith(PREFIX):
        # Anti spam simple: si manda más de 5 comandos en 3 seg, ignorar
        pass
    await bot.process_commands(message)

# ---------------- AYUDA ----------------
@bot.command(name="ayuda")
async def ayuda(ctx):
    texto = """
**🏆 COMANDOS TTBOT PRO**

**Jugadores:**
`!torneo` - Ver torneo actual
`!unirme` - Unirte al torneo
`!salirme` - Salirte
`!lista` - Ver jugadores
`!misstats` - Tus estadísticas
`!reglas` - Ver reglas
`!reportar @user motivo` - Reportar tramposo

**Admins:**
`!crear [nombre] [max]` - Crear torneo
`!iniciar` - Iniciar torneo / bracket
`!bracket` - Ver bracket
`!ganador @user` - Pasar de ronda
`!perdedor @user` - Eliminar
`!pausa` / `!reanudar` - Pausar torneo
`!final @ganador` - Terminar torneo
`!cancelar` - Cancelar torneo
`!ban @user` / `!unban @user` - Banear
`!limpiar` - Limpiar lista
`!config max 64` - Cambiar máximo
`!grupos` - Crear grupos A-Z
`!anunciar texto` - Anunciar
`!top` - Top ganadores
`!resetstats` - Borrar stats (admin)
"""
    await ctx.send(embed=embed("📖 AYUDA TTBOT", texto, 0x3498db))

@bot.command(name="reglas")
async def reglas(ctx):
    await ctx.send(embed=embed("📜 REGLAS", "1. No spam\n2. No insultos\n3. No hacer trampa / teaming\n4. Respetar al admin\n5. Si te sales 2 veces, ban\n6. El admin tiene la última palabra", 0xffaa00))

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms - Online")

# ---------------- TORNEO BASE ----------------
@bot.command(name="crear")
async def crear(ctx, nombre: str = "Torneo", max_j: int = 64):
    if not es_admin(ctx):
        await ctx.send("🚫 Solo admins pueden crear torneos.")
        return
    t = get_torneo(ctx.guild.id)
    if t["activo"]:
        await ctx.send("❌ Ya hay un torneo activo. Usa `!cancelar` primero.")
        return
    if max_j < 2 or max_j > 256:
        await ctx.send("❌ Máximo debe ser entre 2 y 256.")
        return
    t.update({"activo": True, "jugadores": [], "ronda": 0, "bracket": [], "ganadores": [], "perdedores": [], "pausado": False, "creador": ctx.author.id, "nombre": nombre, "max": max_j, "inicio": str(datetime.datetime.now())})
    guardar_datos()
    await ctx.send(embed=embed("🏆 TORNEO CREADO", f"**{nombre}**\nMáx: {max_j} jugadores\nPon `!unirme` para entrar\nAdmin: {ctx.author.mention}", 0x00ff00))

@bot.command(name="torneo")
async def torneo_info(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["activo"]:
        await ctx.send("No hay torneo activo. Un admin debe poner `!crear`")
        return
    await ctx.send(embed=embed(f"🏆 {t['nombre']}", f"Estado: {'⏸️ Pausado' if t['pausado'] else '🟢 Activo'}\nJugadores: {len(t['jugadores'])}/{t['max']}\nRonda: {t['ronda']}\nModo: {t['modo']}", 0x3498db))

@bot.command(name="cancelar")
async def cancelar(ctx):
    if not es_admin(ctx):
        await ctx.send("🚫 Solo admins.")
        return
    t = get_torneo(ctx.guild.id)
    if not t["activo"]:
        await ctx.send("No hay torneo que cancelar.")
        return
    t["activo"] = False
    t["jugadores"] = []
    guardar_datos()
    await ctx.send("🛑 Torneo cancelado por admin.")

@bot.command(name="pausa")
async def pausa(ctx):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    t["pausado"] = True
    guardar_datos()
    await ctx.send("⏸️ Torneo pausado. Nadie puede unirse ni avanzar.")

@bot.command(name="reanudar")
async def reanudar(ctx):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    t["pausado"] = False
    guardar_datos()
    await ctx.send("▶️ Torneo reanudado.")

# ---------------- JUGADORES ----------------
@bot.command(name="unirme")
@commands.cooldown(1, 5, commands.BucketType.user)
async def unirme(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["activo"]:
        await ctx.send("❌ No hay torneo activo.")
        return
    if t["pausado"]:
        await ctx.send("⏸️ Torneo pausado, espera.")
        return
    if esta_baneado(ctx.guild.id, ctx.author.id):
        await ctx.send("🚫 Estás baneado de torneos.")
        return
    if ctx.author.id in t["jugadores"]:
        await ctx.send("Ya estás dentro, no hagas spam.")
        return
    if len(t["jugadores"]) >= t["max"]:
        await ctx.send("❌ Torneo lleno.")
        return
    if t["ronda"] > 0:
        await ctx.send("❌ Ya empezó, no puedes entrar a media ronda.")
        return
    t["jugadores"].append(ctx.author.id)
    guardar_datos()
    await ctx.send(f"✅ {ctx.author.mention} dentro! ({len(t['jugadores'])}/{t['max']})")

@bot.command(name="salirme")
async def salirme(ctx):
    t = get_torneo(ctx.guild.id)
    if ctx.author.id not in t["jugadores"]:
        await ctx.send("No estás en el torneo.")
        return
    if t["ronda"] > 0 and not es_admin(ctx):
        await ctx.send("❌ Ya empezó, no te puedes salir. Habla con un admin.")
        return
    t["jugadores"].remove(ctx.author.id)
    guardar_datos()
    await ctx.send(f"👋 {ctx.author.mention} se salió. Quedan {len(t['jugadores'])}")

@bot.command(name="lista")
async def lista(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["jugadores"]:
        await ctx.send("Nadie aún. Pon `!unirme`")
        return
    texto = ""
    for i, uid in enumerate(t["jugadores"]):
        m = ctx.guild.get_member(uid)
        nombre = m.mention if m else f"ID {uid}"
        texto += f"{i+1}. {nombre}\n"
    await ctx.send(embed=embed(f"👥 Jugadores ({len(t['jugadores'])})", texto, 0x9b59b6))

@bot.command(name="limpiar")
async def limpiar(ctx):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    t["jugadores"] = []
    guardar_datos()
    await ctx.send("🧹 Lista limpiada.")

# ---------------- BRACKET / RONDAS ----------------
@bot.command(name="iniciar")
async def iniciar(ctx):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["activo"]: return await ctx.send("No hay torneo.")
    if len(t["jugadores"]) < MIN_JUGADORES: return await ctx.send(f"Faltan jugadores, mínimo {MIN_JUGADORES}.")
    if t["ronda"] > 0: return await ctx.send("Ya inició.")
    random.shuffle(t["jugadores"])
    t["ronda"] = 1
    pares = []
    for i in range(0, len(t["jugadores"])-1, 2):
        pares.append([t["jugadores"][i], t["jugadores"][i+1]])
    t["bracket"] = pares
    guardar_datos()
    texto = ""
    for i, (a,b) in enumerate(pares):
        ma = ctx.guild.get_member(a); mb = ctx.guild.get_member(b)
        texto += f"Partida {i+1}: {ma.mention if ma else a} vs {mb.mention if mb else b}\n"
    if len(t["jugadores"]) % 2 == 1:
        ultimo = ctx.guild.get_member(t["jugadores"][-1])
        texto += f"\n⭐ {ultimo.mention if ultimo else 'Último'} pasa directo (bye)"
    await ctx.send(embed=embed("🔥 RONDA 1 - BRACKET", texto, 0xe74c3c))

@bot.command(name="bracket")
async def bracket(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["bracket"]:
        await ctx.send("Aún no hay bracket. Admin pon `!iniciar`")
        return
    texto = ""
    for i, (a,b) in enumerate(t["bracket"]):
        ma = ctx.guild.get_member(a); mb = ctx.guild.get_member(b)
        texto += f"{i+1}. {ma.mention if ma else a} vs {mb.mention if mb else b}\n"
    await ctx.send(embed=embed(f"📊 Bracket Ronda {t['ronda']}", texto, 0x3498db))

@bot.command(name="ganador")
async def ganador_cmd(ctx, miembro: discord.Member):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if miembro.id not in t["jugadores"]:
        await ctx.send("Ese jugador no está en el torneo.")
        return
    if miembro.id not in t["ganadores"]:
        t["ganadores"].append(miembro.id)
    registrar_stats(miembro.id, gano=True)
    guardar_datos()
    await ctx.send(f"✅ {miembro.mention} avanza a la siguiente ronda!")

@bot.command(name="perdedor")
async def perdedor_cmd(ctx, miembro: discord.Member):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if miembro.id in t["jugadores"]:
        t["jugadores"].remove(miembro.id)
        t["perdedores"].append(miembro.id)
    registrar_stats(miembro.id, gano=False)
    guardar_datos()
    await ctx.send(f"❌ {miembro.mention} eliminado.")

@bot.command(name="siguiente")
async def siguiente(ctx):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["ganadores"]:
        await ctx.send("No hay ganadores marcados. Usa `!ganador @user`")
        return
    t["jugadores"] = t["ganadores"][:]
    t["ganadores"] = []
    t["ronda"] += 1
    if len(t["jugadores"]) == 1:
        await ctx.send(f"🏆 ¡Ya tenemos campeón! <@{t['jugadores'][0]}>")
        return
    random.shuffle(t["jugadores"])
    pares = []
    for i in range(0, len(t["jugadores"])-1, 2):
        pares.append([t["jugadores"][i], t["jugadores"][i+1]])
    t["bracket"] = pares
    guardar_datos()
    texto = "\n".join([f"{i+1}. <@{a}> vs <@{b}>" for i,(a,b) in enumerate(pares)])
    await ctx.send(embed=embed(f"🔥 RONDA {t['ronda']}", texto, 0xe74c3c))

@bot.command(name="final")
async def final_cmd(ctx, ganador: discord.Member):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["activo"]: return await ctx.send("No hay torneo activo.")
    registrar_stats(ganador.id, gano=True)
    await ctx.send(embed=embed("🏆 ¡CAMPEÓN!", f"**{ganador.mention}** ganó el torneo **{t['nombre']}**\n🎉 Felicidades!", 0xf1c40f))
    t["activo"] = False
    t["jugadores"] = []
    t["bracket"] = []
    t["ronda"] = 0
    guardar_datos()

# ---------------- GRUPOS A-Z ----------------
@bot.command(name="grupos")
async def grupos(ctx, por_grupo: int = 48):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["jugadores"]: return await ctx.send("No hay jugadores.")
    if por_grupo < 2 or por_grupo > 100: return await ctx.send("Por grupo entre 2 y 100.")
    import string as _s
    letras = list(_s.ascii_uppercase)
    num = -(-len(t["jugadores"]) // por_grupo)
    if num > 26: return await ctx.send("Son más de 26 grupos, no soporto más de Z.")
    await ctx.send(f"Creando {num} grupos...")
    for i in range(num):
        letra = letras[i]
        try:
            rol = await ctx.guild.create_role(name=f"Grupo {letra}")
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False), rol: discord.PermissionOverwrite(view_channel=True, send_messages=False), ctx.guild.me: discord.PermissionOverwrite(view_channel=True)}
            canal = await ctx.guild.create_text_channel(f"🔒grupo-{letra.lower()}", overwrites=overwrites)
            grupo = t["jugadores"][i*por_grupo:(i+1)*por_grupo]
            for uid in grupo:
                m = ctx.guild.get_member(uid)
                if m:
                    try: await m.add_roles(rol)
                    except: pass
            await canal.send(f"**GRUPO {letra}** - {len(grupo)} jugadores\nSala y pass aquí.")
        except Exception as e:
            await ctx.send(f"Error creando grupo {letra}: {e}")
    await ctx.send("✅ Grupos creados.")

# ---------------- MODERACIÓN / SEGURIDAD ----------------
@bot.command(name="ban")
async def ban_cmd(ctx, miembro: discord.Member, *, razon: str = "Sin razón"):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    gid = str(ctx.guild.id)
    if gid not in db["bans"]: db["bans"][gid] = []
    if str(miembro.id) not in db["bans"][gid]:
        db["bans"][gid].append(str(miembro.id))
    t = get_torneo(ctx.guild.id)
    if miembro.id in t["jugadores"]:
        t["jugadores"].remove(miembro.id)
    guardar_datos()
    await ctx.send(f"🔨 {miembro.mention} baneado de torneos. Razón: {razon}")

@bot.command(name="unban")
async def unban_cmd(ctx, miembro: discord.Member):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    gid = str(ctx.guild.id)
    if str(miembro.id) in db["bans"].get(gid, []):
        db["bans"][gid].remove(str(miembro.id))
        guardar_datos()
        await ctx.send(f"✅ {miembro.mention} desbaneado.")
    else:
        await ctx.send("No estaba baneado.")

@bot.command(name="reportar")
async def reportar(ctx, miembro: discord.Member, *, motivo: str = "Sin motivo"):
    t = get_torneo(ctx.guild.id)
    t["reportes"].append({"quien": ctx.author.id, "a_quien": miembro.id, "motivo": motivo, "fecha": str(datetime.datetime.now())})
    guardar_datos()
    await ctx.send(f"📝 Reporte guardado contra {miembro.mention}. Un admin lo revisará.")

@bot.command(name="reportes")
async def ver_reportes(ctx):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["reportes"]: return await ctx.send("No hay reportes.")
    texto = "\n".join([f"<@{r['quien']}> reportó a <@{r['a_quien']}>: {r['motivo']}" for r in t["reportes"][-10:]])
    await ctx.send(embed=embed("📝 Últimos Reportes", texto, 0xe67e22))

@bot.command(name="kicktorneo")
async def kicktorneo(ctx, miembro: discord.Member):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if miembro.id in t["jugadores"]:
        t["jugadores"].remove(miembro.id)
        guardar_datos()
        await ctx.send(f"👢 {miembro.mention} sacado del torneo.")
    else:
        await ctx.send("No está en el torneo.")

# ---------------- STATS / CONFIG ----------------
@bot.command(name="misstats")
async def misstats(ctx):
    s = db["stats"].get(str(ctx.author.id), {"jugados": 0, "ganados": 0, "perdidos": 0})
    await ctx.send(embed=embed(f"📊 Stats de {ctx.author.name}", f"Jugados: {s['jugados']}\nGanados: {s['ganados']}\nPerdidos: {s['perdidos']}", 0x2ecc71))

@bot.command(name="top")
async def top_cmd(ctx):
    if not db["stats"]: return await ctx.send("Aún no hay stats.")
    orden = sorted(db["stats"].items(), key=lambda x: x[1]["ganados"], reverse=True)[:10]
    texto = ""
    for i, (uid, s) in enumerate(orden):
        m = ctx.guild.get_member(int(uid))
        nombre = m.mention if m else uid
        texto += f"{i+1}. {nombre} - {s['ganados']} wins / {s['jugados']} jugados\n"
    await ctx.send(embed=embed("🏆 TOP GANADORES", texto, 0xf1c40f))

@bot.command(name="resetstats")
async def resetstats(ctx):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    db["stats"] = {}
    guardar_datos()
    await ctx.send("Stats reseteadas.")

@bot.command(name="config")
async def config_cmd(ctx, clave: str = None, valor: str = None):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    if not clave:
        await ctx.send("Uso: `!config max 64` o `!config modo 2v2`")
        return
    t = get_torneo(ctx.guild.id)
    if clave.lower() == "max":
        try:
            t["max"] = int(valor)
            guardar_datos()
            await ctx.send(f"Máximo cambiado a {valor}")
        except: await ctx.send("Pon un número.")
    elif clave.lower() == "modo":
        t["modo"] = valor
        guardar_datos()
        await ctx.send(f"Modo cambiado a {valor}")
    else:
        await ctx.send("Clave no válida. Usa max o modo.")

@bot.command(name="anunciar")
async def anunciar(ctx, *, texto: str):
    if not es_admin(ctx): return await ctx.send("🚫 Solo admins.")
    await ctx.send(f"📢 **ANUNCIO:** {texto}")

@bot.command(name="sortear")
async def sortear(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["jugadores"]: return await ctx.send("No hay jugadores.")
    ganador = random.choice(t["jugadores"])
    await ctx.send(f"🎲 Sorteo: ¡Ganó <@{ganador}>!")

# ---------------- ARRANQUE ----------------
if __name__ == "__main__":
    if not TOKEN:
        print("❌ FALTA DISCORD_TOKEN en Render > Environment")
    else:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"Error arrancando: {e}")
