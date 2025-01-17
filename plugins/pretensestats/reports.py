from core import report, Server, Side
from datetime import datetime

from .const import PRETENSE_RANKS


class Header(report.EmbedElement):
    async def render(self, data: dict, server: Server):
        desc = f"__{server.current_mission.name}__\n\n" if server.current_mission else ""
        desc += f"Rankings as of <t:{int(datetime.now().timestamp())}:f>:"
        self.embed.description = desc


class ZoneDistribution(report.PieChart):
    @staticmethod
    def calculate_zone_distribution(zones):
        blue_count = len(zones["blue"])
        neutral_count = len(zones["neutral"])
        red_count = len(zones["red"])
        total_count = blue_count + neutral_count + red_count

        blue_percentage = round(blue_count / total_count * 100, 1)
        neutral_percentage = round(neutral_count / total_count * 100, 1)
        red_percentage = round(red_count / total_count * 100, 1)

        return {
            "Blue": blue_percentage,
            "Neutral": neutral_percentage,
            "Red": red_percentage
        }

    @staticmethod
    def normalize_zones(zones: dict) -> dict:
        red = {}
        blue = {}
        neutral = {}
        for name, zone in zones.items():
            if Side(zone['side']) == Side.RED:
                red[name] = zone
            elif Side(zone['side']) == Side.BLUE:
                blue[name] = zone
            else:
                neutral[name] = zone
        return {"blue": blue, "neutral": neutral, "red": red}

    async def render(self, data: dict):
        zones = data["zones"]
        if not zones.get('blue') and not zones.get('red') and not zones.get('neutral'):
            zones = self.normalize_zones(zones)
        zone_distribution = self.calculate_zone_distribution(zones)
        self.colors = []
        if zone_distribution['Blue'] > 0.0:
            self.colors.append('blue')
        if zone_distribution['Neutral'] > 0.0:
            self.colors.append('lightgrey')
        if zone_distribution['Red'] > 0.0:
            self.colors.append('red')
        await super().render(zone_distribution)


class Top10Pilots(report.EmbedElement):
    @staticmethod
    def get_rank(xp):
        for rank in reversed(list(PRETENSE_RANKS.keys())):
            if xp >= PRETENSE_RANKS[rank]["requiredXP"]:
                return PRETENSE_RANKS[rank]["name"]
        return None

    async def render(self, data: dict):
        # Extract player scores from the JSON data
        player_scores = {}
        stats = data.get("stats", {})
        for player, stats in stats.items():
            if isinstance(stats, dict):  # Check if stats is a dictionary
                xp = stats.get("XP", 0)
                player_scores[player] = xp

        # Sort players by their score in descending order
        sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)

        # Add player scores to the leaderboard
        names = ''
        xp = ''
        ranks = ''
        for rank, (player, score) in enumerate(sorted_players[:10], start=1):
            names += f'{player}\n'
            xp += f'{score:>5}\n'
            ranks += f'{self.get_rank(score)}\n'
        if names:
            self.embed.add_field(name='Name', value=names)
            self.embed.add_field(name='XP', value=xp)
            self.embed.add_field(name='Rank', value=ranks)
