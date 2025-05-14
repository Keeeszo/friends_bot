from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import fetch_coc_data, send_to_topic, format_time_left
from config import CLAN_TAG

def calculate_attack_score(attack, attacker_th, defender_th, attacker_pos, defender_pos):
    star_points = attack['stars'] * 100
    th_diff = defender_th - attacker_th
    th_modifier = 1 + (th_diff * 0.2)
    position_diff = defender_pos - attacker_pos
    position_modifier = 1 + (position_diff * -0.1)
    duration_penalty = (attack['duration'] / 180) * 20
    score = (star_points * th_modifier * position_modifier) - duration_penalty
    return max(10, score)

def get_missing_attackers(clan_members):
    missing = []
    for member in clan_members:
        attacks = member.get('attacks', [])
        if len(attacks) < 2:
            remaining = 2 - len(attacks)
            missing.append({
                'name': member['name'],
                'map_position': member['mapPosition'],
                'th_level': member['townhallLevel'],
                'remaining_attacks': remaining
            })
    return sorted(missing, key=lambda x: x['map_position'])

async def guerra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    war_data = await fetch_coc_data(f"/clans/{CLAN_TAG}/currentwar")
    if not war_data or war_data.get('state') == 'notInWar':
        await send_to_topic("⚔️ No hay guerra activa", update)
        return

    clan = war_data['clan']
    opponent = war_data['opponent']
    team_size = war_data.get('teamSize', 15)

    clan_members = {m['tag']: m for m in clan.get('members', [])}
    opponent_members = {m['tag']: m for m in opponent.get('members', [])}

    attack_scores = []
    defense_scores = []

    for member in clan.get('members', []):
        for attack in member.get('attacks', []):
            defender = opponent_members.get(attack['defenderTag'], {})
            score = calculate_attack_score(
                attack=attack,
                attacker_th=member['townhallLevel'],
                defender_th=defender.get('townhallLevel', member['townhallLevel']),
                attacker_pos=member['mapPosition'],
                defender_pos=defender.get('mapPosition', member['mapPosition'])
            )
            attack_scores.append({
                'attacker': member['name'],
                'attacker_th': member['townhallLevel'],
                'defender': defender.get('name', 'Unknown'),
                'defender_th': defender.get('townhallLevel', '?'),
                'stars': attack['stars'],
                'destruction': attack['destructionPercentage'],
                'duration': attack['duration'],
                'score': score
            })

        defender_tag = member['tag']
        for opp_member in opponent.get('members', []):
            for defense in opp_member.get('attacks', []):
                if defense['defenderTag'] == defender_tag:
                    defense_scores.append({
                        'defender': member['name'],
                        'defender_th': member['townhallLevel'],
                        'attacker': opp_member['name'],
                        'attacker_th': opp_member['townhallLevel'],
                        'stars_lost': defense['stars'],
                        'destruction': defense['destructionPercentage'],
                        'duration': defense['duration'],
                        'score': 100 - defense['stars'] * 25
                    })

    top_attacks = sorted(attack_scores, key=lambda x: -x['score'])[:3]
    top_defenses = sorted(defense_scores, key=lambda x: -x['score'])[:3]
    missing_attackers = get_missing_attackers(clan.get('members', []))

    message = [
        f"⚔️ *GUERRA ACTUAL* ⚔️",
        f"▸ {clan['name']} (Nvl.{clan['clanLevel']}) vs {opponent['name']} (Nvl.{opponent['clanLevel']})",
        f"▸ Ataques: {clan['attacks']}/{team_size * 2} | {clan['stars']}★ vs {opponent['stars']}★",
        f"▸ Destrucción: {clan['destructionPercentage']:.1f}% vs {opponent['destructionPercentage']:.1f}%",
        f"⏳ Estado: {'Preparación' if war_data['state'] == 'preparation' else f'En curso (Finaliza en {format_time_left(war_data.get('endTime'))})'}",
    ]

    if top_attacks:
        message.append("\n🏅 *TOP 3 ATAQUES*:")
        for i, attack in enumerate(top_attacks, 1):
            stars = '★' * attack['stars'] + '☆' * (3 - attack['stars'])
            message.append(
                f"{i}. {attack['attacker']} (TH{attack['attacker_th']}) → {attack['defender']} (TH{attack['defender_th']})")
            message.append(
                f"   {stars} | {attack['destruction']}% | {attack['duration']}s | Puntos: {attack['score']:.1f}")

    if top_defenses:
        message.append("\n🛡️ *TOP 3 DEFENSAS*:")
        for i, defense in enumerate(top_defenses, 1):
            stars = '★' * defense['stars_lost'] + '☆' * (3 - defense['stars_lost'])
            message.append(
                f"{i}. {defense['defender']} (TH{defense['defender_th']}) ← {defense['attacker']} (TH{defense['attacker_th']})")
            message.append(
                f"   {stars} | {defense['destruction']}% | {defense['duration']}s | Puntos: {defense['score']:.1f}")

    if missing_attackers:
        message.append("\n⚠️ *FALTAN POR ATACAR*:")
        for member in missing_attackers:
            message.append(
                f"▸ {member['name']} (TH{member['th_level']}, Pos.{member['map_position']}) - "
                f"{member['remaining_attacks']} ataque(s) restante(s)"
            )

    await send_to_topic('\n'.join(message), update)