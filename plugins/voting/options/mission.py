import asyncio
import os
from typing import Optional

from core import Coalition, Server
from plugins.voting.base import VotableItem


class Mission(VotableItem):

    def __init__(self, server: Server, config: dict, params: Optional[list[str]] = None):
        super().__init__('mission', server, config, params)

    def print(self) -> str:
        return (f"You can now vote to change the mission of this server.\n"
                f"If you vote for the current mission, the mission will be restarted!\n"
                f"If you do not want any change, vote for \"No Change\".")

    def get_choices(self) -> list[str]:
        return ['No Change'] + self.config.get('choices', [
            os.path.basename(x) for x in self.server.settings['missionList']
        ])

    async def execute(self, winner: str):
        if winner == 'No Change':
            return
        message = f"The mission will change in 60s."
        self.server.sendChatMessage(Coalition.ALL, message)
        self.server.sendPopupMessage(Coalition.ALL, message)
        await asyncio.sleep(60)
        for idx, mission in enumerate(await self.server.getMissionList()):
            if winner in mission:
                await self.server.loadMission(mission=idx + 1, modify_mission=False)
                break
        else:
            mission = os.path.join(await self.server.get_missions_dir(), winner)
            await self.server.loadMission(mission=mission, modify_mission=False)
