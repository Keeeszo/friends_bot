from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import fetch_coc_data, send_to_topic, send_progress, update_progress, delete_progress, format_time_left, \
    escape_markdown
from config import CLAN_TAG


async def capital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información detallada del asalto a la capital"""
    try:
        await send_progress(update, context, "Iniciando solicitud")
        await update_progress(update, context, 10, "Obteniendo información básica del clan")
        """Muestra información básica del clan"""
        clan_data = await fetch_coc_data(f"/clans/{CLAN_TAG}")
        if not clan_data:
            await delete_progress(context)
            await update.message.reply_text("❌ Error obteniendo datos del clan")
            return
        # Mostrar progreso

        # Obtener datos
        await update_progress(update, context, 20, "Obteniendo información del ataque a la capital")
        raid_data = await fetch_coc_data(f"/clans/{CLAN_TAG}/capitalraidseasons?limit=1")
        if not raid_data or not raid_data.get('items'):
            await delete_progress(context)
            await send_to_topic("❌ Error obteniendo datos del capital", update)
            return

        current_raid = raid_data['items'][0]
        state = current_raid.get('state', 'unknown')

        if state != 'ongoing':
            await delete_progress(context)
            await send_to_topic("ℹ️ No hay asalto al capital activo actualmente", update)
            return

        await update_progress(update, context, 70, "Procesando miembros")
        # Procesar miembros
        members = current_raid.get('members', [])
        total_members = clan_data.get("members")
        members_with_attacks = sum(1 for m in members if m.get('attacks', 0) > 0)

        # Top 5 looters
        top_looters = sorted(
            members,
            key=lambda x: x.get('capitalResourcesLooted', 0),
            reverse=True
        )[:10]

        # Miembros que no han atacado
        inactive_members = [
            m for m in members
            if m.get('attacks', 0) < m.get('attackLimit', 5)
        ]

        # Estadísticas generales
        total_loot = current_raid.get('capitalTotalLoot', 0)
        total_attacks = current_raid.get('totalAttacks', 0)
        districts_destroyed = current_raid.get('enemyDistrictsDestroyed', 0)

        # Calcular tiempo restante
        end_time = current_raid.get('endTime', '')
        time_left = format_time_left(end_time) if end_time else "tiempo desconocido"

        # Construir mensaje
        message_parts = [
            f"🏰 *ASALTO A LA CAPITAL* 🏰",
            f"▸ Estado: {'En progreso' if state == 'ongoing' else 'Finalizado'}",
            f"▸ Finaliza en: {time_left}",
            f"▸ Distritos destruidos: {districts_destroyed}",
            f"▸ Botín total: {total_loot:,}",
            f"▸ Ataques realizados: {total_attacks}",
            f"▸ Miembros activos: {members_with_attacks}/{total_members}",
        ]

        # Top 5 looters
        if top_looters:
            message_parts.append("\n🏅 *TOP RECOLECTORES*:")
            for i, member in enumerate(top_looters, 1):
                message_parts.append(
                    f"{i}. {member['name']}: "
                    f"💎 {member.get('capitalResourcesLooted', 0):,} | "
                    f"⚔️ {member.get('attacks', 0)}/{member.get('attackLimit', 0)} ataques"
                )

        # Miembros inactivos
        if inactive_members:
            inactive_names = [escape_markdown(m['name']) for m in inactive_members]
            message_parts.append(
                f"\n⚠️ *MIEMBROS ACTIVOS EN EL ASALTO QUE FALTAN POR ATACAR: ({len(inactive_names)}):* "
                f"{', '.join(inactive_names)}"
            )

        # Añadir log de ataques recientes si hay espacio
        attack_log = current_raid.get('attackLog', [])
        if attack_log:
            last_raid = attack_log[0]
            message_parts.append(
                f"\n🔍 *ÚLTIMO CLAN ATACADO:* {last_raid['defender']['name']} "
                f"(Nvl {last_raid['defender']['level']})"
            )

        await delete_progress(context)
        await send_to_topic('\n'.join(message_parts), update)

    except Exception as e:
        await delete_progress(context)
        await send_to_topic("⚠️ Error procesando datos del capital", update)
