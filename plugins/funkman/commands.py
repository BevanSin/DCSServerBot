import os

from configparser import ConfigParser
from typing import Optional

import psycopg

from core import Plugin, PluginInstallationError, PluginConfigurationError, DEFAULT_TAG, Server
from services import DCSServerBot
from .listener import FunkManEventListener

# ruamel YAML support
from ruamel.yaml import YAML
yaml = YAML()


class FunkMan(Plugin):

    def read_locals(self) -> dict:
        config = super().read_locals()
        if not config:
            raise PluginInstallationError('funkman', "Can't find config/plugins/funkman.yaml, please create one!")
        return config

    async def install(self) -> bool:
        if await super().install():
            config = self.get_config()
            if 'install' not in config:
                raise PluginConfigurationError(self.plugin_name, 'install')
            funkpath = os.path.expandvars(config['install'])
            if not os.path.exists(funkpath) or not os.path.exists(funkpath + os.path.sep + 'FunkMan.ini'):
                self.log.error(f"No FunkMan installation found at {funkpath}!")
                raise PluginConfigurationError(self.plugin_name, 'install')
            if 'CHANNELID_MAIN' not in config:
                self.log.info('  => Migrating FunkMan.ini ...')
                ini = ConfigParser()
                ini.read(config['install'] + os.path.sep + 'FunkMan.ini')
                if 'CHANNELID_MAIN' in ini['FUNKBOT']:
                    config['CHANNELID_MAIN'] = ini['FUNKBOT']['CHANNELID_MAIN']
                if 'CHANNELID_RANGE' in ini['FUNKBOT']:
                    config['CHANNELID_RANGE'] = ini['FUNKBOT']['CHANNELID_RANGE']
                if 'CHANNELID_AIRBOSS' in ini['FUNKBOT']:
                    config['CHANNELID_AIRBOSS'] = ini['FUNKBOT']['CHANNELID_AIRBOSS']
                if 'IMAGEPATH' in ini['FUNKPLOT']:
                    if ini['FUNKPLOT']['IMAGEPATH'].startswith('.'):
                        config['IMAGEPATH'] = config['install'] + ini['FUNKPLOT']['IMAGEPATH'][1:]
                    else:
                        config['IMAGEPATH'] = ini['FUNKPLOT']['IMAGEPATH']
                with open('config/plugins/funkman.yaml', 'w') as outfile:
                    yaml.dump({DEFAULT_TAG: config}, outfile)
            return True
        return False

    def get_config(self, server: Optional[Server] = None, *, plugin_name: Optional[str] = None,
                   use_cache: Optional[bool] = True) -> dict:
        # retrieve the config from another plugin
        if plugin_name:
            return super().get_config(server, plugin_name=plugin_name, use_cache=use_cache)
        if not server:
            return self.locals.get(DEFAULT_TAG, {})
        if server.node.name not in self._config:
            self._config[server.node.name] = {}
        if server.instance.name not in self._config[server.node.name] or not use_cache:
            default, specific = self.get_base_config(server)
            for x in ['strafe_board', 'strafe_channel', 'bomb_board', 'bomb_channel']:
                if x in default:
                    del default[x]
            self._config[server.node.name][server.instance.name] = default | specific
        return self._config[server.node.name][server.instance.name]

    async def prune(self, conn: psycopg.Connection, *, days: int = -1, ucids: list[str] = None):
        self.log.debug('Pruning FunkMan ...')
        if ucids:
            for ucid in ucids:
                conn.execute('DELETE FROM bomb_runs WHERE player_ucid = %s', (ucid,))
                conn.execute('DELETE FROM strafe_runs WHERE player_ucid = %s', (ucid,))
        elif days > -1:
            conn.execute(f"DELETE FROM bomb_runs WHERE time < (DATE(NOW()) - interval '{days} days')")
            conn.execute(f"DELETE FROM strafe_runs WHERE time < (DATE(NOW()) - interval '{days} days')")
        self.log.debug('FunkMan pruned.')


async def setup(bot: DCSServerBot):
    await bot.add_cog(FunkMan(bot, FunkManEventListener))
