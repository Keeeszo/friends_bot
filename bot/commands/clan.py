from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import fetch_coc_data, send_to_topic
from config import CLAN_TAG


async def claninfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clan_data = await fetch_coc_data(f"/clans/{CLAN_TAG}")
    if not clan_data:
        await update.message.reply_text("❌ Error obteniendo datos del clan")
        return

    winrate = ((clan_data['warWins']) / (clan_data['warLosses'] + clan_data['warWins'])) * 100
    war_league = clan_data.get('warLeague', {}).get('name', 'Sin liga')

    message = (
        f"🏰 *{(clan_data['name'])}* ({clan_data['tag']})\n"
        f"👑 Nivel: {clan_data['clanLevel']} | Miembros: {clan_data['members']}/50\n"
        f"🏆 Puntos: {clan_data['clanPoints']} | Capital: {clan_data.get('clanCapitalPoints', 0)}\n"
        f"⚔️ Liga: {(war_league)}\n"
        f"🔔 Tasa de victorias: {winrate:.2f}%\n"
        f"⭐ Racha de guerras ganadas: {(clan_data['warWinStreak'])}"
    )
    await send_to_topic(message, update)


async def miembros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    members_data = await fetch_coc_data(f"/clans/{CLAN_TAG}/members")
    if not members_data:
        await update.message.reply_text("❌ Error obteniendo miembros")
        return

    top_donadores = sorted(
        members_data.get('items', []),
        key=lambda x: x.get('donations', 0),
        reverse=True
    )[:5]

    members_info = "\n".join(
        f"{i + 1}. TH{m['townHallLevel']} {m['name']} [ {m['tag']} ]"
        for i, m in enumerate(members_data.get('items', []))
    )

    top_members_info = "\n".join(
        f"{i + 1}. {(m['name'])}: 🎁 {m.get('donations', 0)} | 🏆 {m.get('trophies', 0)}"
        for i, m in enumerate(top_donadores)
    )

    message = (
        "Jugadores: \n"
        f"{members_info}\n\n"
        "🌟 *Top 5 Donadores*:\n"
        f"{top_members_info}\n\n"
        f"👥 Total miembros: {len(members_data.get('items', []))}"
    )
    await send_to_topic(message, update)