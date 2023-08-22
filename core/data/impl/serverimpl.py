from __future__ import annotations

import aiohttp
import asyncio
import json
import os
import platform
import shutil
import socket
import traceback

from contextlib import suppress
from core import utils, Server, UploadStatus
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path, PurePath
from psutil import Process
from typing import Optional, TYPE_CHECKING, Union
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from core.data.dataobject import DataObjectFactory
from core.data.const import Status, Channel
from core.mizfile import MizFile
from core.services import ServiceRegistry

if TYPE_CHECKING:
    from core import Plugin, Extension, InstanceImpl
    from services import DCSServerBot


class MissionFileSystemEventHandler(FileSystemEventHandler):
    def __init__(self, server: Server):
        self.server = server
        self.log = server.log

    def on_created(self, event: FileSystemEvent):
        path: str = os.path.normpath(event.src_path)
        if path.endswith('.miz'):
            self.server.addMission(path)
            self.log.info(f"=> New mission {os.path.basename(path)[:-4]} added to server {self.server.name}.")

    def on_moved(self, event: FileSystemMovedEvent):
        self.on_deleted(event)
        self.on_created(FileSystemEvent(event.dest_path))

    def on_deleted(self, event: FileSystemEvent):
        path: str = os.path.normpath(event.src_path)
        if not path.endswith('.miz'):
            return
        for idx, mission in enumerate(self.server.settings['missionList']):
            if mission != path:
                continue
            if (idx + 1) == self.server.mission_id:
                self.log.fatal(f'The running mission on server {self.server.name} got deleted!')
            else:
                self.server.deleteMission(idx + 1)
                self.log.info(f"=> Mission {os.path.basename(mission)[:-4]} deleted from server {self.server.name}.")
            break


@dataclass
@DataObjectFactory.register("Server")
class ServerImpl(Server):
    _instance: InstanceImpl = field(default=None)
    bot: Optional[DCSServerBot] = field(compare=False, init=False)

    def __post_init__(self):
        super().__post_init__()
        with self.pool.connection() as conn:
            with conn.transaction():
                conn.execute("""
                    INSERT INTO servers (server_name, node, port, status_channel, chat_channel) 
                    VALUES(%s, %s, %s, %s, %s) 
                    ON CONFLICT (server_name) DO UPDATE 
                    SET node=excluded.node, 
                        port=excluded.port,
                        status_channel=excluded.status_channel,
                        chat_channel=excluded.chat_channel, 
                        last_seen=NOW()
                """, (self.name, self.node.name, self.port,
                      self.channels[Channel.STATUS],
                      self.channels[Channel.CHAT]))
        # enable autoscan for missions changes
        if self.locals.get('autoscan', False):
            self.event_handler = MissionFileSystemEventHandler(self)
            self.observer = Observer()
            self.observer.start()

    @property
    def is_remote(self) -> bool:
        return False

    async def get_missions_dir(self) -> str:
        return self.instance.missions_dir

    @property
    def settings(self) -> dict:
        if not self._settings:
            path = os.path.join(self.instance.home, r'Config\serverSettings.lua')
            self._settings = utils.SettingsDict(self, path, 'cfg')
        return self._settings

    @property
    def options(self) -> dict:
        if not self._options:
            path = os.path.join(self.instance.home, r'Config\options.lua')
            self._options = utils.SettingsDict(self, path, 'options')
        return self._options

    @property
    def instance(self) -> InstanceImpl:
        return self._instance

    @instance.setter
    def instance(self, instance: InstanceImpl):
        self._instance = instance
        self.locals |= self.instance.locals
        self.prepare()

    def _install_luas(self):
        dcs_path = os.path.join(self.instance.home, 'Scripts')
        if not os.path.exists(dcs_path):
            os.mkdir(dcs_path)
        ignore = None
        bot_home = os.path.join(dcs_path, r'net\DCSServerBot')
        if os.path.exists(bot_home):
            self.log.debug('  - Updating Hooks ...')
            shutil.rmtree(bot_home)
            ignore = shutil.ignore_patterns('DCSServerBotConfig.lua.tmpl')
        else:
            self.log.debug('  - Installing Hooks ...')
        shutil.copytree('./Scripts', dcs_path, dirs_exist_ok=True, ignore=ignore)
        try:
            with open(r'Scripts/net/DCSServerBot/DCSServerBotConfig.lua.tmpl', 'r') as template:
                with open(os.path.join(bot_home, 'DCSServerBotConfig.lua'), 'w') as outfile:
                    for line in template.readlines():
                        line = utils.format_string(line, node=self.node, instance=self.instance, server=self)
                        outfile.write(line)
        except KeyError as k:
            self.log.error(
                f'! You must set a value for {k}. See README for help.')
            raise k
        except Exception as ex:
            self.log.exception(ex)
        self.log.debug(f"  - Installing Plugin luas into {self.instance.name} ...")
        for plugin_name in self.node.plugins:
            source_path = f'./plugins/{plugin_name}/lua'
            if os.path.exists(source_path):
                target_path = os.path.join(bot_home, f'{plugin_name}')
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                self.log.debug(f'    => Plugin {plugin_name.capitalize()} installed.')
        self.log.debug(f'  - Luas installed into {self.instance.name}.')

    def prepare(self):
        if self.settings['name'] != self.name:
            self.settings['name'] = self.name
        if 'serverSettings' in self.locals:
            for key, value in self.locals['serverSettings'].items():
                if key == 'advanced':
                    self.settings['advanced'] = self.settings['advanced'] | value
                else:
                    self.settings[key] = value
        self._install_luas()

    async def get_current_mission_file(self) -> Optional[str]:
        if not self.current_mission or not self.current_mission.filename:
            settings = self.settings
            start_index = int(settings.get('listStartIndex', 1))
            if start_index <= len(settings['missionList']):
                filename = settings['missionList'][start_index - 1]
            else:
                filename = None
            if not filename or not os.path.exists(filename):
                for idx, filename in enumerate(settings['missionList']):
                    if os.path.exists(filename):
                        settings['listStartIndex'] = idx + 1
                        break
                else:
                    filename = None
        else:
            filename = self.current_mission.filename
        return filename

    def serialize(self, message: dict):
        for key, value in message.items():
            if isinstance(value, int):
                message[key] = str(value)
            elif isinstance(value, Enum):
                message[key] = value.value
            elif isinstance(value, dict):
                message[key] = self.serialize(value)
        return message

    def send_to_dcs(self, message: dict):
        # As Lua does not support large numbers, convert them to strings
        message = self.serialize(message)
        msg = json.dumps(message)
        self.log.debug(f"HOST->{self.name}: {msg}")
        dcs_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dcs_socket.sendto(msg.encode('utf-8'), ('127.0.0.1', int(self.port)))
        dcs_socket.close()

    def rename(self, new_name: str, update_settings: bool = False) -> None:
        # rename the entries in the main database tables
        with self.pool.connection() as conn:
            with conn.transaction():
                if self.node.master:
                    bot: DCSServerBot = ServiceRegistry.get("Bot").bot
                    # call rename() in all Plugins
                    for plugin in bot.cogs.values():  # type: Plugin
                        plugin.rename(conn, self.name, new_name)
                else:
                    for n in self.node.get_active_nodes():
                        self.bus.send_to_node({
                            "command": "rpc",
                            "service": "ServiceBus",
                            "method": "rename",
                            "params": {
                                "old_name": self.name,
                                "new_name": new_name
                            }
                        }, node=n)
                conn.execute('UPDATE servers SET server_name = %s WHERE server_name = %s',
                             (new_name, self.name))
                conn.execute('UPDATE message_persistence SET server_name = %s WHERE server_name = %s',
                             (new_name, self.name))
        if update_settings:
            self.settings['name'] = new_name
        self.name = new_name

    async def do_startup(self):
        basepath = self.node.installation
        for exe in ['DCS_server.exe', 'DCS.exe']:
            path = os.path.join(basepath, 'bin', exe)
            if os.path.exists(path):
                break
        else:
            self.log.error(f"No executable found to start a DCS server in {basepath}!")
            return
        # check if all missions are existing
        missions = [x for x in self.settings['missionList'] if os.path.exists(x)]
        if len(missions) != len(self.settings['missionList']):
            self.settings['missionList'] = missions
            self.log.warning('Removed non-existent missions from serverSettings.lua')
        self.log.debug(r'Launching DCS server with: "{}" --server --norender -w {}'.format(path, self.instance.name))
        p = await asyncio.create_subprocess_exec(path, '--server', '--norender', '-w', self.instance.name)
        with suppress(Exception):
            self.process = Process(p.pid)

    async def init_extensions(self):
        for extension in self.locals.get('extensions', {}):
            ext: Extension = self.extensions.get(extension)
            if not ext:
                if '.' not in extension:
                    ext = utils.str_to_class('extensions.' + extension)(
                        self,
                        self.locals['extensions'][extension] | self.node.locals.get('extensions', {}).get(extension, {})
                    )
                else:
                    ext = utils.str_to_class(extension)(
                        self,
                        self.locals['extensions'][extension] | self.node.locals.get('extensions', {}).get(extension, {})
                    )
                if ext.is_installed():
                    self.extensions[extension] = ext

    async def startup(self) -> None:
        await self.init_extensions()
        for ext in self.extensions.values():
            await ext.prepare()
            await ext.beforeMissionLoad()
        await self.do_startup()
        timeout = 300 if self.node.locals.get('slow_system', False) else 180
        self.status = Status.LOADING
        await self.wait_for_status_change([Status.STOPPED, Status.PAUSED, Status.RUNNING], timeout)

    async def startup_extensions(self) -> None:
        for ext in [x for x in self.extensions.values() if not x.is_running()]:
            try:
                await ext.startup()
            except Exception as ex:
                self.log.exception(ex)

    async def shutdown(self, force: bool = False) -> None:
        if not force:
            await super().shutdown(False)
        self.terminate()
        for ext in [x for x in self.extensions.values() if x.is_running()]:
            try:
                await ext.shutdown()
            except Exception as ex:
                self.log.exception(ex)
        self.status = Status.SHUTDOWN

    def terminate(self) -> None:
        if self.process and self.process.is_running():
            self.process.kill()
        self.process = None

    async def modifyMission(self, preset: Union[list, dict]) -> None:
        def apply_preset(value: dict):
            if 'start_time' in value:
                miz.start_time = value['start_time']
            if 'date' in value:
                miz.date = datetime.strptime(value['date'], '%Y-%m-%d')
            if 'temperature' in value:
                miz.temperature = int(value['temperature'])
            if 'clouds' in value:
                if isinstance(value['clouds'], str):
                    miz.clouds = {"preset": value['clouds']}
                else:
                    miz.clouds = value['clouds']
            if 'wind' in value:
                miz.wind = value['wind']
            if 'groundTurbulence' in value:
                miz.groundTurbulence = int(value['groundTurbulence'])
            if 'enable_dust' in value:
                miz.enable_dust = value['enable_dust']
            if 'dust_density' in value:
                miz.dust_density = int(value['dust_density'])
            if 'qnh' in value:
                miz.qnh = int(value['qnh'])
            if 'enable_fog' in value:
                miz.enable_fog = value['enable_fog']
            if 'fog' in value:
                miz.fog = value['fog']
            if 'halo' in value:
                miz.halo = value['halo']
            if 'requiredModules' in value:
                miz.requiredModules = value['requiredModules']
            if 'accidental_failures' in value:
                miz.accidental_failures = value['accidental_failures']
            if 'forcedOptions' in value:
                miz.forcedOptions = value['forcedOptions']
            if 'miscellaneous' in value:
                miz.miscellaneous = value['miscellaneous']
            if 'difficulty' in value:
                miz.difficulty = value['difficulty']
            if 'files' in value:
                miz.files = value['files']

        if self.status in [Status.STOPPED, Status.SHUTDOWN]:
            filename = await self.get_current_mission_file()
            if not filename:
                return
            try:
                miz = MizFile(self, filename)
                if isinstance(preset, list):
                    for p in preset:
                        apply_preset(p)
                else:
                    apply_preset(preset)
                miz.save()
            except Exception as ex:
                self.log.exception("Exception while parsing mission: ", exc_info=ex)

    async def keep_alive(self):
        # we set a longer timeout in here because, we don't want to risk false restarts
        timeout = 20 if self.node.locals.get('slow_system', False) else 10
        data = await self.send_to_dcs_sync({"command": "getMissionUpdate"}, timeout)
        with self.pool.connection() as conn:
            with conn.transaction():
                conn.execute('UPDATE servers SET last_seen = NOW() WHERE node = %s AND server_name = %s',
                             (platform.node(), self.name))
        if data['pause'] and self.status == Status.RUNNING:
            self.status = Status.PAUSED
        elif not data['pause'] and self.status != Status.RUNNING:
            self.status = Status.RUNNING
        self.current_mission.mission_time = data['mission_time']
        self.current_mission.real_time = data['real_time']

    async def uploadMission(self, filename: str, url: str, force: bool = False) -> UploadStatus:
        stopped = False
        filename = os.path.join(await self.get_missions_dir(), filename)
        try:
            if self.current_mission and os.path.normpath(self.current_mission.filename) == os.path.normpath(filename):
                if not force:
                    return UploadStatus.FILE_IN_USE
                await self.stop()
                stopped = True
            elif os.path.exists(filename) and not force:
                return UploadStatus.FILE_EXISTS

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(filename, 'wb') as outfile:
                            outfile.write(await response.read())
                    else:
                        return UploadStatus.READ_ERROR
            if not self.locals.get('autoscan', False):
                self.addMission(filename)
            if stopped:
                await self.start()
            return UploadStatus.OK
        except Exception:
            traceback.print_exc()

    async def listAvailableMissions(self) -> list[str]:
        return [str(x) for x in sorted(Path(PurePath(self.instance.home, "Missions")).glob("*.miz"))]
