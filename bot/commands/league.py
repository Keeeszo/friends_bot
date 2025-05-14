from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import fetch_coc_data, send_to_topic, send_progress, update_progress, delete_progress, format_time_left, \
    escape_markdown
from config import CLAN_TAG
import asyncio


async def liga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el ranking de clanes y los MVP de nuestro clan en la liga actual"""
    # Paso 1: Iniciar progreso
    await send_progress(update, context, "Analizando liga")

    # Paso 2: Obtener datos básicos (20%)
    await update_progress(update, context, 20, "Obteniendo datos del clan")

    # Obtener datos básicos del clan
    clan_data = await fetch_coc_data(f"/clans/{CLAN_TAG}")
    if not clan_data:
        await delete_progress(context)
        await send_to_topic("❌ Error obteniendo datos del clan", update)
        return

    await update_progress(update, context, 40, "Verificando participación")
    # Verificar participación en liga
    league_data = clan_data.get('warLeague', {})
    if not league_data or league_data.get('id') == 0:
        await delete_progress(context)
        await send_to_topic("ℹ️ El clan no está participando actualmente en una liga", update)
        return

    await update_progress(update, context, 60, "Buscando grupo de liga")
    # Obtener grupo de liga
    league_group = await fetch_coc_data(f"/clans/{CLAN_TAG}/currentwar/leaguegroup")
    if not league_group or league_group.get('state') == "GROUP_NOT_FOUND":
        await delete_progress(context)
        await send_to_topic("ℹ️ No se encontró grupo de liga activo", update)
        return
    # Procesar todas las guerras
    war_tags = []
    await update_progress(update, context, 60, " Procesar todas las guerras")
    for round_info in league_group.get('rounds', []):
        war_tags.extend(round_info.get('warTags', []))

    # Estructuras de datos
    all_clans_stats = {}  # Para el top 3 global
    our_clan_mvps = {}  # Solo para nuestro clan
    our_clan_tag = CLAN_TAG.replace('%23', '#')

    await update_progress(update, context, 80, "Analizando guerras")
    for war_tag in war_tags:
        if war_tag == "#0": continue

        war_data = await fetch_coc_data(f"/clanwarleagues/wars/{war_tag.replace('#', '%23')}")
        if not war_data or war_data.get('state') not in ['inWar', 'warEnded']:
            continue

        # Procesar ambos clanes (para el ranking global)
        for clan in [war_data.get('clan'), war_data.get('opponent')]:
            if not clan: continue

            tag = clan.get('tag')
            if tag not in all_clans_stats:
                all_clans_stats[tag] = {
                    'name': clan.get('name'),
                    'stars': 0,
                    'destruction': 0,
                    'wins': 0
                }

            all_clans_stats[tag]['stars'] += clan.get('stars', 0)
            all_clans_stats[tag]['destruction'] += clan.get('destructionPercentage', 0)

            # Solo contar victorias si la guerra terminó
            if war_data.get('state') == 'warEnded':
                if clan.get('stars') > war_data.get('opponent', {}).get('stars', 0):
                    all_clans_stats[tag]['wins'] += 1
                elif clan.get('stars') == war_data.get('opponent', {}).get('stars', 0):
                    if clan.get('destructionPercentage', 0) > war_data.get('opponent', {}).get('destructionPercentage',
                                                                                               0):
                        all_clans_stats[tag]['wins'] += 1

            # Procesar solo los miembros de NUESTRO clan para MVP
            if clan.get('tag') == our_clan_tag:
                for member in clan.get('members', []):
                    player_tag = member.get('tag')
                    if player_tag not in our_clan_mvps:
                        our_clan_mvps[player_tag] = {
                            'name': member.get('name'),
                            'stars': 0,
                            'townhall': member.get('townhallLevel', 0)
                        }

                    for attack in member.get('attacks', []):
                        our_clan_mvps[player_tag]['stars'] += attack.get('stars', 0)

    await update_progress(update, context, 90, "Finalizando")
    message_parts = [
        f"🏆 *LIGA DE CLANES - {league_group.get('season', 'Temporada actual')}* 🏆",
        f"▸ *Liga:* {league_data.get('name', 'Desconocida')}",
        f"▸ *Estado:* {'En progreso' if league_group.get('state') == 'inWar' else 'Finalizada'}"
    ]

    # 1. TOP 3 CLANES (global)
    top_clans = sorted(
        all_clans_stats.values(),
        key=lambda x: (-x['stars'], -x['destruction'])
    )[:3]

    if top_clans:
        message_parts.append("\n🏅 *TOP 3 CLANES*:")
        for i, clan in enumerate(top_clans, 1):
            avg_destruction = clan['destruction'] / len(war_tags) if war_tags else 0
            message_parts.append(
                f"{i}. {escape_markdown(clan['name'])}: "
                f"⭐ {clan['stars']} | "
                f"🔥 {avg_destruction:.1f}% | "
                f"🏆 {clan['wins']}V"
            )

    # 2. ESTADÍSTICAS DE NUESTRO CLAN
    our_stats = all_clans_stats.get(our_clan_tag, {})
    message_parts.extend([
        f"\n📊 *NUESTRO CLAN*:",
        f"▸ Posición: {next((i + 1 for i, c in enumerate(top_clans) if c['name'] == our_stats.get('name')), '?')}",
        f"▸ Estrellas: {our_stats.get('stars', 0)}",
    ])

    # 3. MVP DE NUESTRO CLAN
    sorted_mvps = sorted(our_clan_mvps.values(), key=lambda x: -x['stars'])[:10]
    if sorted_mvps:
        message_parts.append("\n👑 *TOP 10 MVP (NUESTRO CLAN)*:")
        for i, mvp in enumerate(sorted_mvps, 1):
            message_parts.append(
                f"{i}. {escape_markdown(mvp['name'])} (TH{mvp['townhall']}) - "
                f"⭐ {mvp['stars']} estrellas"
            )

    await update_progress(update, context, 100, "¡Completado!")
    await asyncio.sleep(0.5)
    await delete_progress(context)
    await send_to_topic('\n'.join(message_parts), update)
