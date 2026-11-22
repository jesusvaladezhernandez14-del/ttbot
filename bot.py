# ============================================================
# TTBOT - FREE FIRE TOURNAMENT PRO - SALAS 48-50
# +500 LINEAS / ANTI-ROMPER / RENDER 24/7
# ============================================================
import os
import json
import random
import datetime
import string
import discord
from discord.ext import commands
from flask import Flask
import threading

# ---------------- KEEP ALIVE RENDER ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "ttbot Free Fire online"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# ---------------- CONFIG FREE FIRE ----------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
DATA_FILE = "torneos.json"
SALA_MIN = 12
SALA_MAX = 50
SALA_IDEAL = 48
MAX_SALAS = 10
PUNTOS_BOOYAH = 12
PUNTOS_POR_KILL = 1
PUNTOS_TOP2 = 9
PUNTOS_TOP3 = 7
PUNTOS_TOP4 = 5
PUNTOS_TOP5 = 4

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ---------------- BASE DE DATOS ----------------
def cargar():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"torneos": {}, "bans": {}, "stats": {}, "salas": {}, "historial": []}

def guardar():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"Error guardando: {e}")

db = cargar()
for k in ["torneos", "bans", "stats", "salas", "historial"]:
    if k not in db:
        db[k] = {} if k != "historial" else []

def get_torneo(gid):
    gid = str(gid)
    if gid not in db["torneos"]:
        db["torneos"][gid] = {
            "activo": False, "nombre": "Free Fire", "jugadores": [],
            "max": 48, "ronda": 0, "pausado": False, "creador": None,
            "inicio": None, "salas": [], "modo": "FF-BattleRoyale",
            "reportes": [], "resultados": [], "sala_pass": {},
            "inscripcion_abierta": True, "top": []
        }
    return db["torneos"][gid]

def es_admin(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    for rol in ctx.author.roles:
        if rol.name.lower() in ["admin torneo", "admin", "moderador", "organizador", "staff", "owner"]:
            return True
    return False

def esta_baneado(gid, uid):
    return str(uid) in db["bans"].get(str(gid), [])

def get_stats(uid):
    uid = str(uid)
    if uid not in db["stats"]:
        db["stats"][uid] = {"partidas": 0, "booyah": 0, "kills": 0, "puntos": 0, "top10": 0, "ganados": 0}
    return db["stats"][uid]

def sumar_stats(uid, kills=0, puntos=0, booyah=False, top10=False):
    s = get_stats(uid)
    s["partidas"] += 1
    s["kills"] += kills
    s["puntos"] += puntos
    if booyah:
        s["booyah"] += 1
        s["ganados"] += 1
    if top10:
        s["top10"] += 1
    guardar()

def embed(titulo, desc, color=0x00ff00):
    e = discord.Embed(title=titulo, description=desc, color=color, timestamp=datetime.datetime.now())
    e.set_footer(text="TTBOT • Free Fire")
    return e

def calcular_salas(total, por_sala=48):
    if total <= 0:
        return 0
    return -(-total // por_sala)

def repartir_en_salas(jugadores, por_sala=48):
    random.shuffle(jugadores)
    salas = []
    for i in range(0, len(jugadores), por_sala):
        salas.append(jugadores[i:i+por_sala])
    return salas

# ---------------- EVENTOS ----------------
@bot.event
async def on_ready():
    print(f"TTBOT FF ONLINE como {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!ayuda | Free Fire 48"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Te faltó un dato. Pon `!ayuda`")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Espera {int(error.retry_after)}s, no hagas spam.")
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send("🚫 Solo admins pueden hacer eso.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Ese usuario no existe. Usa @usuario")
        return
    print(f"Error: {error}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# ---------------- AYUDA Y REGLAS ----------------
@bot.command(name="ayuda")
async def ayuda(ctx):
    texto = """
**🏆 TTBOT FREE FIRE**

**Para jugadores:**
`!torneo` - Ver torneo actual
`!unirme` - Unirte a la sala
`!salirme` - Salirte
`!lista` - Ver quiénes van
`!salas` - Ver cuántas salas hay
`!misstats` - Tus puntos / kills / booyah
`!top` - Top de puntos
`!reglas` - Reglas Free Fire
`!reportar @user motivo` - Reportar hacker

**Para admins:**
`!crear Nombre 48` - Crear torneo FF
`!crear Nombre 96` - Crear para 2 salas
`!iniciar` - Cerrar inscripción y armar salas
`!grupos` - Crear canales privados por sala
`!sala 1 pass 1234` - Poner sala y pass
`!resultado @ganador kills` - Registrar Booyah
`!puntos @user kills lugar` - Dar puntos manual
`!final` - Terminar torneo
`!cancelar` - Cancelar
`!pausa` / `!reanudar`
`!ban @user` / `!unban @user`
`!limpiar` - Limpiar lista
`!anunciar texto`
`!sortear` - Sorteo entre jugadores
`!resetstats`
"""
    await ctx.send(embed=embed("📖 AYUDA FREE FIRE", texto, 0x3498db))

@bot.command(name="reglas")
async def reglas(ctx):
    texto = """
**📜 REGLAS FREE FIRE**

1. No hacks, no emulador con hacks, no teaming fuera de escuadra
2. No insultos ni toxicidad
3. Si te sales de la sala, pierdes tu lugar
4. Respetar sala y contraseña, no compartirla
5. Grabar partida si puedes, por si hay reclamo
6. El admin tiene la última palabra
7. 48-50 jugadores por sala, si hay más se hace Sala 2
8. Prohibido hacer alianza entre salas
"""
    await ctx.send(embed=embed("📜 REGLAS", texto, 0xffaa00))

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms - Free Fire Online")

@bot.command(name="info")
async def info_cmd(ctx):
    await ctx.send(embed=embed("ℹ️ TTBOT FF", "Bot de torneos Free Fire\nSalas de 48-50\nPuntos: Booyah 12, Kill 1, Top2 9, Top3 7\nUsa `!ayuda`", 0x3498db))

# ---------------- CREAR / TORNEO ----------------
@bot.command(name="crear")
async def crear(ctx, *args):
    if not es_admin(ctx):
        await ctx.send("🚫 Solo admins pueden crear torneos.")
        return
    t = get_torneo(ctx.guild.id)
    if t["activo"]:
        await ctx.send("❌ Ya hay un torneo activo. Usa `!cancelar` primero.")
        return
    max_j = 48
    nombre = "Free Fire"
    if args:
        if args[-1].isdigit():
            max_j = int(args[-1])
            nombre = " ".join(args[:-1]) or "Free Fire"
        else:
            nombre = " ".join(args)
    if max_j < SALA_MIN or max_j > 500:
        await ctx.send(f"❌ El torneo debe ser entre {SALA_MIN} y 500 jugadores.")
        return
    t.update({"activo": True, "jugadores": [], "max": max_j, "nombre": nombre, "ronda": 0, "pausado": False, "creador": ctx.author.id, "inicio": str(datetime.datetime.now()), "salas": [], "resultados": [], "inscripcion_abierta": True, "sala_pass": {}})
    guardar()
    num_salas = calcular_salas(max_j, SALA_IDEAL)
    await ctx.send(embed=embed("🏆 TORNEO FREE FIRE CREADO", f"**{nombre}**\nCupo: {max_j} jugadores\nSalas estimadas: {num_salas} sala(s) de 48\nPon `!unirme` para entrar\nAdmin: {ctx.author.mention}\n\nCuando se llene, admin pone `!iniciar`", 0x00ff00))

@bot.command(name="torneo")
async def torneo_info(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["activo"]:
        await ctx.send("No hay torneo activo. Un admin debe poner `!crear Free 48`")
        return
    num_salas = calcular_salas(len(t["jugadores"]), SALA_IDEAL) if t["jugadores"] else 0
    estado = "⏸️ Pausado" if t["pausado"] else "🟢 Inscripción abierta" if t["inscripcion_abierta"] else "🔒 Inscripción cerrada"
    await ctx.send(embed=embed(f"🏆 {t['nombre']}", f"Estado: {estado}\nJugadores: {len(t['jugadores'])}/{t['max']}\nSalas actuales: {num_salas}\nModo: Battle Royale - 48 por sala\nRonda: {t['ronda']}", 0x3498db))

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
    t["salas"] = []
    guardar()
    await ctx.send("🛑 Torneo Free Fire cancelado por admin.")

@bot.command(name="pausa")
async def pausa(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    t["pausado"] = True
    guardar()
    await ctx.send("⏸️ Torneo pausado. Nadie puede unirse.")

@bot.command(name="reanudar")
async def reanudar(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    t["pausado"] = False
    guardar()
    await ctx.send("▶️ Torneo reanudado.")

@bot.command(name="cerrar")
async def cerrar_inscripcion(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    t["inscripcion_abierta"] = False
    guardar()
    await ctx.send("🔒 Inscripción cerrada. Ya no se puede entrar con `!unirme`")

@bot.command(name="abrir")
async def abrir_inscripcion(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    t["inscripcion_abierta"] = True
    guardar()
    await ctx.send("🟢 Inscripción abierta de nuevo.")

# ---------------- JUGADORES FREE FIRE ----------------
@bot.command(name="unirme")
@commands.cooldown(1, 5, commands.BucketType.user)
async def unirme(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["activo"]:
        await ctx.send("❌ No hay torneo activo. Pide a un admin que ponga `!crear Free 48`")
        return
    if t["pausado"]:
        await ctx.send("⏸️ Torneo pausado, espera.")
        return
    if not t["inscripcion_abierta"]:
        await ctx.send("🔒 Inscripción cerrada.")
        return
    if esta_baneado(ctx.guild.id, ctx.author.id):
        await ctx.send("🚫 Estás baneado de torneos.")
        return
    if ctx.author.id in t["jugadores"]:
        await ctx.send("Ya estás dentro, no hagas spam.")
        return
    if len(t["jugadores"]) >= t["max"]:
        await ctx.send("❌ Torneo lleno. Espera a la próxima sala.")
        return
    if t["ronda"] > 0:
        await ctx.send("❌ Ya empezó, no puedes entrar a media partida.")
        return
    t["jugadores"].append(ctx.author.id)
    guardar()
    restantes = t["max"] - len(t["jugadores"])
    msg = f"✅ {ctx.author.mention} dentro! ({len(t['jugadores'])}/{t['max']}) - Faltan {restantes}"
    if len(t["jugadores"]) == t["max"]:
        msg += "\n\n🔥 **¡SALA LLENA!** Admin pon `!iniciar` para armar salas."
    elif len(t["jugadores"]) % 48 == 0:
        msg += f"\n🔥 Sala {len(t['jugadores'])//48} llena!"
    await ctx.send(msg)

@bot.command(name="salirme")
async def salirme(ctx):
    t = get_torneo(ctx.guild.id)
    if ctx.author.id not in t["jugadores"]:
        await ctx.send("No estás en el torneo.")
        return
    if t["ronda"] > 0 and not es_admin(ctx):
        await ctx.send("❌ Ya empezó, no te puedes salir. Habla con admin.")
        return
    t["jugadores"].remove(ctx.author.id)
    guardar()
    await ctx.send(f"👋 {ctx.author.mention} se salió. Quedan {len(t['jugadores'])}/{t['max']}")

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
        sala_num = (i // SALA_IDEAL) + 1
        texto += f"{i+1}. {nombre} - Sala {sala_num}\n"
        if len(texto) > 1800:
            texto += "... y más"
            break
    await ctx.send(embed=embed(f"👥 Jugadores Free Fire ({len(t['jugadores'])}/{t['max']})", texto, 0x9b59b6))

@bot.command(name="limpiar")
async def limpiar(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    t["jugadores"] = []
    guardar()
    await ctx.send("🧹 Lista limpiada.")

@bot.command(name="agregar")
async def agregar_cmd(ctx, miembro: discord.Member):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if miembro.id in t["jugadores"]:
        await ctx.send("Ya está dentro.")
        return
    if len(t["jugadores"]) >= t["max"]:
        await ctx.send("Torneo lleno.")
        return
    t["jugadores"].append(miembro.id)
    guardar()
    await ctx.send(f"✅ {miembro.mention} agregado por admin. ({len(t['jugadores'])}/{t['max']})")

@bot.command(name="sacar")
async def sacar_cmd(ctx, miembro: discord.Member):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if miembro.id in t["jugadores"]:
        t["jugadores"].remove(miembro.id)
        guardar()
        await ctx.send(f"👢 {miembro.mention} sacado del torneo.")
    else:
        await ctx.send("No está en el torneo.")

@bot.command(name="simular")
async def simular(ctx, cantidad: int = 48):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["activo"]:
        await ctx.send("Primero crea con `!crear`")
        return
    for i in range(cantidad):
        fake_id = 900000000000000000 + i
        if fake_id not in t["jugadores"] and len(t["jugadores"]) < t["max"]:
            t["jugadores"].append(fake_id)
    guardar()
    await ctx.send(f"🤖 Simulados {cantidad} jugadores para prueba. Total: {len(t['jugadores'])}/{t['max']}")

# ---------------- SALAS 48-50 ----------------
@bot.command(name="salas")
async def salas_cmd(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["jugadores"]:
        await ctx.send("No hay jugadores aún.")
        return
    salas = repartir_en_salas(t["jugadores"][:], SALA_IDEAL)
    texto = f"Total: {len(t['jugadores'])} jugadores\nSalas necesarias: {len(salas)}\n\n"
    for i, sala in enumerate(salas):
        texto += f"**SALA {i+1}:** {len(sala)} jugadores - {'🟢 Lista' if len(sala) >= SALA_MIN else '🟡 Faltan jugadores'}\n"
    await ctx.send(embed=embed("🎮 SALAS FREE FIRE", texto, 0xe74c3c))

@bot.command(name="iniciar")
async def iniciar(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["activo"]:
        return await ctx.send("No hay torneo. Pon `!crear Free 48`")
    if len(t["jugadores"]) < SALA_MIN:
        return await ctx.send(f"❌ Faltan jugadores. Mínimo {SALA_MIN} para una sala de Free. Llevas {len(t['jugadores'])}")
    if t["ronda"] > 0:
        return await ctx.send("Ya inició.")
    t["ronda"] = 1
    t["inscripcion_abierta"] = False
    salas = repartir_en_salas(t["jugadores"][:], SALA_IDEAL)
    t["salas"] = salas
    guardar()
    texto = f"🔥 **TORNEO INICIADO - {len(t['jugadores'])} JUGADORES**\n\n"
    for i, sala in enumerate(salas):
        texto += f"**SALA {i+1}:** {len(sala)} jugadores\n"
        if len(sala) < SALA_MAX:
            texto += f"  Quedan {SALA_MAX - len(sala)} lugares libres\n"
    texto += "\nAdmin pon `!grupos` para crear canales privados por sala\nAdmin pon `!sala 1 ID PASS` para pasar sala y contraseña"
    await ctx.send(embed=embed("🔥 ¡A JUGAR!", texto, 0xe74c3c))

@bot.command(name="grupos")
async def grupos(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["jugadores"]:
        return await ctx.send("No hay jugadores.")
    if not t["salas"]:
        t["salas"] = repartir_en_salas(t["jugadores"][:], SALA_IDEAL)
    letras = list(string.ascii_uppercase)
    await ctx.send(f"Creando {len(t['salas'])} sala(s) de Free Fire...")
    for i, sala in enumerate(t["salas"]):
        letra = letras[i] if i < 26 else f"S{i+1}"
        try:
            rol = await ctx.guild.create_role(name=f"Sala {i+1} - {letra}")
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                rol: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(view_channel=True)
            }
            canal = await ctx.guild.create_text_channel(f"🔒sala-{i+1}-{letra.lower()}", overwrites=overwrites)
            for uid in sala:
                m = ctx.guild.get_member(uid)
                if m:
                    try:
                        await m.add_roles(rol)
                    except:
                        pass
            await canal.send(f"**🎮 SALA {i+1} - GRUPO {letra}**\n{len(sala)} jugadores\nSala y contraseña se enviarán aquí.\nNo compartas la sala fuera de este canal.")
        except Exception as e:
            await ctx.send(f"Error creando sala {i+1}: {e}")
    guardar()
    await ctx.send("✅ Salas creadas. Usa `!sala 1 123456 pass123` para poner ID y pass.")

@bot.command(name="sala")
async def sala_cmd(ctx, numero: int, sala_id: str = None, password: str = None):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not sala_id:
        await ctx.send("Uso: `!sala 1 12345678 mipass`")
        return
    t["sala_pass"][str(numero)] = {"id": sala_id, "pass": password or "Sin pass"}
    guardar()
    await ctx.send(f"🎮 **SALA {numero}**\nID: `{sala_id}`\nPass: `{password}`\n¡Compártelo solo en el canal de esa sala!")

@bot.command(name="versala")
async def versala(ctx, numero: int = 1):
    t = get_torneo(ctx.guild.id)
    info = t["sala_pass"].get(str(numero))
    if not info:
        await ctx.send(f"No hay info de Sala {numero}. Admin pon `!sala {numero} ID PASS`")
        return
    if not es_admin(ctx):
        await ctx.send("🚫 Solo admins pueden ver sala y pass aquí. Revisa tu canal de sala.")
        return
    await ctx.send(f"🎮 Sala {numero} - ID: `{info['id']}` Pass: `{info['pass']}`")

# ---------------- RESULTADOS / PUNTOS ----------------
@bot.command(name="resultado")
async def resultado_cmd(ctx, ganador: discord.Member, kills: int = 0):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    puntos = PUNTOS_BOOYAH + (kills * PUNTOS_POR_KILL)
    sumar_stats(ganador.id, kills=kills, puntos=puntos, booyah=True, top10=True)
    t["resultados"].append({"ganador": ganador.id, "kills": kills, "puntos": puntos, "fecha": str(datetime.datetime.now())})
    guardar()
    await ctx.send(embed=embed("🏆 ¡BOOYAH!", f"**Ganador:** {ganador.mention}\nKills: {kills}\nPuntos: {puntos} (12 Booyah + {kills} kills)\n🎉 Felicidades!", 0xf1c40f))

@bot.command(name="puntos")
async def puntos_cmd(ctx, miembro: discord.Member, kills: int = 0, lugar: int = 10):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    puntos_lugar = 0
    if lugar == 1:
        puntos_lugar = PUNTOS_BOOYAH
    elif lugar == 2:
        puntos_lugar = PUNTOS_TOP2
    elif lugar == 3:
        puntos_lugar = PUNTOS_TOP3
    elif lugar == 4:
        puntos_lugar = PUNTOS_TOP4
    elif lugar == 5:
        puntos_lugar = PUNTOS_TOP5
    elif lugar <= 10:
        puntos_lugar = 2
    elif lugar <= 20:
        puntos_lugar = 1
    total = puntos_lugar + (kills * PUNTOS_POR_KILL)
    sumar_stats(miembro.id, kills=kills, puntos=total, booyah=(lugar == 1), top10=(lugar <= 10))
    guardar()
    await ctx.send(f"✅ {miembro.mention} - Lugar {lugar} + {kills} kills = **{total} puntos**\n({puntos_lugar} pts por lugar + {kills} pts por kills)")

@bot.command(name="tabla")
async def tabla_cmd(ctx):
    if not db["stats"]:
        await ctx.send("Aún no hay puntos.")
        return
    orden = sorted(db["stats"].items(), key=lambda x: x[1]["puntos"], reverse=True)[:15]
    texto = ""
    for i, (uid, s) in enumerate(orden):
        m = ctx.guild.get_member(int(uid)) if uid.isdigit() and int(uid) < 900000000000000000 else None
        nombre = m.mention if m else f"Jugador {i+1}"
        texto += f"{i+1}. {nombre} - {s['puntos']} pts | {s['booyah']} Booyah | {s['kills']} kills | Top10: {s['top10']}\n"
    await ctx.send(embed=embed("📊 TABLA DE PUNTOS FREE FIRE", texto, 0xf1c40f))

@bot.command(name="top")
async def top_cmd(ctx):
    if not db["stats"]:
        await ctx.send("Aún no hay stats.")
        return
    orden = sorted(db["stats"].items(), key=lambda x: x[1]["puntos"], reverse=True)[:10]
    texto = ""
    for i, (uid, s) in enumerate(orden):
        m = ctx.guild.get_member(int(uid)) if uid.isdigit() and int(uid) < 900000000000000000 else None
        nombre = m.mention if m else "Jugador"
        texto += f"{i+1}. {nombre} - {s['puntos']} pts - {s['booyah']} Booyah - {s['kills']} kills\n"
    await ctx.send(embed=embed("🏆 TOP 10 FREE FIRE", texto, 0xf1c40f))

@bot.command(name="misstats")
async def misstats(ctx):
    s = get_stats(ctx.author.id)
    await ctx.send(embed=embed(f"📊 Stats de {ctx.author.name}", f"Partidas: {s['partidas']}\nBooyah: {s['booyah']}\nKills: {s['kills']}\nPuntos: {s['puntos']}\nTop 10: {s['top10']}", 0x2ecc71))

@bot.command(name="final")
async def final_cmd(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["activo"]:
        return await ctx.send("No hay torneo activo.")
    t["activo"] = False
    t["inscripcion_abierta"] = False
    db["historial"].append({"nombre": t["nombre"], "jugadores": len(t["jugadores"]), "fecha": str(datetime.datetime.now())})
    guardar()
    await ctx.send(embed=embed("🏆 TORNEO TERMINADO", f"Torneo **{t['nombre']}** terminado.\nPon `!tabla` para ver quién ganó por puntos.\nGracias por jugar!", 0xf1c40f))
    t["jugadores"] = []
    t["salas"] = []
    guardar()

@bot.command(name="historial")
async def historial_cmd(ctx):
    if not db["historial"]:
        await ctx.send("No hay torneos pasados.")
        return
    texto = "\n".join([f"{h['nombre']} - {h['jugadores']} jugadores - {h['fecha'][:10]}" for h in db["historial"][-10:]])
    await ctx.send(embed=embed("📜 Historial", texto, 0x95a5a6))

# ---------------- MODERACION ----------------
@bot.command(name="ban")
async def ban_cmd(ctx, miembro: discord.Member, *, razon: str = "Sin razón"):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    gid = str(ctx.guild.id)
    if gid not in db["bans"]:
        db["bans"][gid] = []
    if str(miembro.id) not in db["bans"][gid]:
        db["bans"][gid].append(str(miembro.id))
    t = get_torneo(ctx.guild.id)
    if miembro.id in t["jugadores"]:
        t["jugadores"].remove(miembro.id)
    guardar()
    await ctx.send(f"🔨 {miembro.mention} baneado. Razón: {razon}")

@bot.command(name="unban")
async def unban_cmd(ctx, miembro: discord.Member):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    gid = str(ctx.guild.id)
    if str(miembro.id) in db["bans"].get(gid, []):
        db["bans"][gid].remove(str(miembro.id))
        guardar()
        await ctx.send(f"✅ {miembro.mention} desbaneado.")
    else:
        await ctx.send("No estaba baneado.")

@bot.command(name="reportar")
async def reportar(ctx, miembro: discord.Member, *, motivo: str = "Sin motivo"):
    t = get_torneo(ctx.guild.id)
    t["reportes"].append({"quien": ctx.author.id, "a_quien": miembro.id, "motivo": motivo, "fecha": str(datetime.datetime.now())})
    guardar()
    await ctx.send(f"📝 Reporte guardado contra {miembro.mention}. Un admin lo revisará.")

@bot.command(name="reportes")
async def ver_reportes(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if not t["reportes"]:
        return await ctx.send("No hay reportes.")
    texto = "\n".join([f"<@{r['quien']}> reportó a <@{r['a_quien']}>: {r['motivo']}" for r in t["reportes"][-10:]])
    await ctx.send(embed=embed("📝 Reportes", texto, 0xe67e22))

@bot.command(name="kicktorneo")
async def kicktorneo(ctx, miembro: discord.Member):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    t = get_torneo(ctx.guild.id)
    if miembro.id in t["jugadores"]:
        t["jugadores"].remove(miembro.id)
        guardar()
        await ctx.send(f"👢 {miembro.mention} sacado.")
    else:
        await ctx.send("No está en el torneo.")

# ---------------- EXTRAS ----------------
@bot.command(name="anunciar")
async def anunciar(ctx, *, texto: str):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    await ctx.send(f"📢 **ANUNCIO FREE FIRE:** {texto}")

@bot.command(name="sortear")
async def sortear(ctx):
    t = get_torneo(ctx.guild.id)
    if not t["jugadores"]:
        return await ctx.send("No hay jugadores.")
    ganador = random.choice(t["jugadores"])
    await ctx.send(f"🎲 Sorteo: ¡Ganó <@{ganador}>!")

@bot.command(name="resetstats")
async def resetstats(ctx):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    db["stats"] = {}
    guardar()
    await ctx.send("Stats reseteadas.")

@bot.command(name="config")
async def config_cmd(ctx, clave: str = None, valor: str = None):
    if not es_admin(ctx):
        return await ctx.send("🚫 Solo admins.")
    if not clave:
        await ctx.send("Uso: `!config max 48`")
        return
    t = get_torneo(ctx.guild.id)
    if clave.lower() == "max":
        try:
            t["max"] = int(valor)
            guardar()
            await ctx.send(f"Máximo cambiado a {valor}")
        except:
            await ctx.send("Pon un número.")
    else:
        await ctx.send("Solo puedes cambiar max.")

@bot.command(name="estado")
async def estado_cmd(ctx):
    t = get_torneo(ctx.guild.id)
    await ctx.send(f"Bot: Online\nTorneo: {'Activo' if t['activo'] else 'Inactivo'}\nJugadores: {len(t['jugadores'])}/{t['max']}\nSalas: {len(t['salas'])}")

# ---------------- ARRANQUE ----------------
if __name__ == "__main__":
    if not TOKEN:
        print("❌ FALTA DISCORD_TOKEN en Render > Environment")
    else:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"Error arrancando: {e}")  
