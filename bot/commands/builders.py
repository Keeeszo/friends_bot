from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from typing import Optional, Tuple

from bot.utils import (
    load_constructores,
    save_constructores,
    parse_duration,
    format_time_left,
    send_to_topic,
    fetch_coc_data
)
from config import CLAN_TAG

async def constructores_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🔨 *Gestión de Constructores* 🔨\n\n"
            "📌 Comandos disponibles:\n"
            "/constructores add <tag> <cantidad>\n"
            "/constructores build <tag/nombre> <tiempo> [desc]\n"
            "/constructores list [filtro]\n"
            "/constructores cancel <tag/nombre> <id>\n",
            parse_mode="Markdown"
        )
        return

    subcommand = context.args[0].lower()
    if subcommand == "add":
        await constructores_add(update, context)
    elif subcommand == "build":
        await constructores_build(update, context)
    elif subcommand == "list":
        await constructores_list(update, context)
    elif subcommand == "cancel":
        await constructores_cancel(update, context)
    else:
        await update.message.reply_text("Subcomando no reconocido")

async def constructores_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 3:
            await update.message.reply_text(
                "Formato: /constructores add <tag_jugador/nombre> <cantidad>\n"
                "Ejemplo: /constructores add #VGGG0VY 5\n"
            )
            return

        player_tag = context.args[1]
        try:
            cantidad = int(context.args[2])
        except ValueError:
            await update.message.reply_text("La cantidad debe ser un número entero")
            return

        if cantidad < 1 or cantidad > 5:
            await update.message.reply_text("La cantidad debe ser entre 1 y 5")
            return

        clan_members = await fetch_coc_data(f"/clans/{CLAN_TAG}/members")
        if not clan_members:
            await update.message.reply_text("❌ Error obteniendo lista del clan")
            return

        user_id = str(update.effective_user.id)
        data = load_constructores()

        for uid, user_data in data.items():
            if player_tag in user_data.get("accounts", {}):
                if uid != user_id:
                    owner = user_data.get("username", "otro usuario")
                    await update.message.reply_text(
                        f"❌ Este jugador ya está registrado por {owner}\n"
                        f"Tag: {player_tag}"
                    )
                    return

        account_tag, account_data = None, None
        for member in clan_members.get('items', []):
            if (member["tag"] == player_tag or
                    player_tag == member["name"]):
                account_tag = member["tag"]
                account_data = member
                break

        if not account_tag:
            await update.message.reply_text(
                f"❌ El jugador {player_tag} no es miembro del clan actual\n"
            )
            return

        if user_id not in data:
            data[user_id] = {
                "username": update.effective_user.username or update.effective_user.full_name,
                "accounts": {}
            }

        data[user_id]["accounts"][account_tag] = {
            "name": account_data["name"],
            "max_builders": cantidad,
            "active_builds": [],
            "registered_at": datetime.now().isoformat(),
            "th_level": account_data["townHallLevel"]
        }

        save_constructores(data)

        await update.message.reply_text(
            f"✅ Se han asignado {cantidad} constructores al jugador:\n"
            f"Nombre: {account_data['name']} [ {account_tag} ]\n"
            f"Usuario TG: {update.effective_user.username or update.effective_user.full_name}"
        )

    except Exception as e:
        await update.message.reply_text("⚠️ Error al procesar el comando")

async def constructores_build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 3:
            await update.message.reply_text(
                "🔨 *Uso correcto:*\n"
                "Por tag: `/constructores build #VGGG0VY 2d8h [descripción]`\n"
                "📝 *Duración:* Usa formato 1d2h30m (días, horas, minutos)",
                parse_mode="Markdown"
            )
            return

        identifier = context.args[1]
        duration_str = context.args[2]
        description = " ".join(context.args[3:]) if len(context.args) > 3 else "Construcción"

        try:
            duration = parse_duration(duration_str)
            if duration.total_seconds() < 1:
                await update.message.reply_text("⚠️ La duración mínima es 1s")
                return
        except ValueError:
            await update.message.reply_text(
                "❌ Formato de tiempo inválido. Ejemplos válidos:\n"
                "• 3h30m\n• 2d5h\n• 45m"
            )
            return

        user_id = str(update.effective_user.id)
        data = load_constructores()
        user_data = data.get(user_id, {})

        account_tag, account_data = None, None
        identifier_lower = identifier.lower().strip()

        for tag, account in user_data.get("accounts", {}).items():
            if (identifier_lower == tag.lower() or
                    identifier_lower == account.get("name", "").lower()):
                account_tag = tag
                account_data = account
                break

        if not account_tag:
            accounts_list = []
            for tag, acc in user_data.get("accounts", {}).items():
                acc_name = acc.get("name", "Sin nombre")
                acc_th = acc.get("th_level", "?")
                active = len(acc.get("active_builds", []))
                max_b = acc.get("max_builders", 0)
                accounts_list.append(
                    f"• {acc_name} (TH{acc_th}) - {tag} - {active}/{max_b} const."
                )

            await update.message.reply_text(
                "🔍 *Cuenta no encontrada*. Tus cuentas registradas:\n" +
                "\n".join(accounts_list) if accounts_list else "No tienes cuentas registradas",
                parse_mode="Markdown"
            )
            return

        active_builds = account_data["active_builds"]
        if len(active_builds) >= account_data["max_builders"]:
            await update.message.reply_text(
                f"⚠️ *Límite alcanzado* para {account_data['name']} ({account_tag})\n"
                f"Tienes {len(active_builds)}/{account_data['max_builders']} construcciones activas\n\n"
                f"Usa `/constructores cancel {account_tag} <id>` para liberar espacio",
                parse_mode="Markdown"
            )
            return

        end_time = datetime.now() + duration
        new_build = {
            "start_time": datetime.now().isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration_str,
            "description": description[:100],
            "status": "active"
        }
        active_builds.append(new_build)
        save_constructores(data)

        time_left = format_time_left(end_time.isoformat())
        builder_count = f"{len(active_builds)}/{account_data['max_builders']}"

        await update.message.reply_text(
            f"🏗️ *Nueva construcción registrada*\n\n"
            f"• 👷 Constructor: {account_data['name']} (TH{account_data.get('th_level', '?')})\n"
            f"• ⏱️ Duración: {duration_str}\n"
            f"• 📝 Descripción: {description}\n"
            f"• 🔨 Constructores: {builder_count}",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text("⚠️ Error al procesar el comando")

async def constructores_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        data = load_constructores()

        if not data.get(user_id, {}).get("accounts"):
            await update.message.reply_text("No tienes constructores registrados")
            return

        filter_name = context.args[1] if len(context.args) > 1 else None
        message = ["🏗️ *Tus constructores registrados* 🏗️"]
        has_active_builds = False

        for tag, account in data[user_id]["accounts"].items():
            if filter_name and filter_name != account["name"]:
                continue

            message.append(
                f"\n🔧 *{account['name']}* (TH{account['th_level']}) - {tag}\n"
                f"Constructores: {len(account['active_builds'])}/{account['max_builders']} activos"
            )

            for i, build in enumerate(account["active_builds"], 1):
                has_active_builds = True
                time_left = format_time_left(build["end_time"])
                message.append(
                    f"{i}. ⏳ {build['description']}\n"
                    f"   🕒 Finaliza en {time_left}"
                )

        if len(message) == 1:
            if filter_name:
                await update.message.reply_text(
                    f"ℹ️ No se encontró la cuenta con nombre exacto: '{filter_name}'",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("No tienes construcciones activas actualmente")
            return

        await update.message.reply_text('\n'.join(message), parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("⚠️ Error al listar constructores")

async def constructores_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 3:
            await update.message.reply_text(
                "🔨 *Uso correcto:* `/constructores cancel <nombre_cuenta> <id_constructor>`\n"
                "Ejemplo: `/constructores cancel Keeeszo 1`\n"
                "ℹ️ Usa el ID que aparece en `/constructores list` (número de lista)",
                parse_mode="Markdown"
            )
            return

        account_name = context.args[1]
        build_id_str = context.args[2]

        user_id = str(update.effective_user.id)
        data = load_constructores()

        target_account = None
        for tag, account in data.get(user_id, {}).get("accounts", {}).items():
            if account["name"].lower() == account_name.lower():
                target_account = account
                break

        if not target_account:
            await update.message.reply_text(
                f"❌ No se encontró la cuenta '{account_name}'\n"
                f"Usa `/constructores list` para ver tus cuentas",
                parse_mode="Markdown"
            )
            return

        try:
            build_id = int(build_id_str) - 1
            if build_id < 0 or build_id >= len(target_account["active_builds"]):
                raise ValueError
        except ValueError:
            await update.message.reply_text(
                f"❌ ID inválido. \n"
                f"Ejemplo: `/constructores cancel {account_name} 1`",
                parse_mode="Markdown"
            )
            return

        removed_build = target_account["active_builds"].pop(build_id)
        save_constructores(data)

        await update.message.reply_text(
            f"🗑️ *Construcción cancelada exitosamente*\n\n"
            f"• 🔧 Cuenta: {target_account['name']}\n"
            f"• 📝 Descripción: {removed_build['description']}\n\n"
            f"🏗️ Constructores libres: {int(target_account['max_builders']) - len(target_account['active_builds'])}",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Error al cancelar la construcción. Verifica:\n"
            "1. Que el nombre de la cuenta sea correcto\n"
            "2. Que el ID de construcción exista\n"
            "3. Usa `/constructores list` para verificar",
            parse_mode="Markdown"
        )