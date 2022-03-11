import asyncio
import discord
import os
import platform
import psycopg2
import psycopg2.extras
import re
import subprocess
from contextlib import closing
from core import utils, DCSServerBot, Plugin, Report, const
from core.const import Status
from discord.ext import commands, tasks
from typing import Union, List
from .listener import AdminEventListener


class Agent(Plugin):

    def __init__(self, bot, listener):
        super().__init__(bot, listener)
        self.update_pending = False
        self.update_bot_status.start()
        if self.bot.config.getboolean('DCS', 'AUTOUPDATE') is True:
            self.check_for_dcs_update.start()

    def cog_unload(self):
        if self.bot.config.getboolean('DCS', 'AUTOUPDATE') is True:
            self.check_for_dcs_update.cancel()
        self.update_bot_status.cancel()
        super().cog_unload()

    @commands.command(description='Lists the registered DCS servers')
    @utils.has_role('DCS')
    @commands.guild_only()
    async def servers(self, ctx):
        if len(self.globals) > 0:
            for server_name, server in self.globals.items():
                if server['status'] in [Status.RUNNING, Status.PAUSED]:
                    players = self.bot.player_data[server['server_name']]
                    num_players = len(players[players['active'] == True]) + 1
                    report = Report(self.bot, 'mission', 'serverStatus.json')
                    env = await report.render(server=server, num_players=num_players)
                    await ctx.send(embed=env.embed)
        else:
            await ctx.send('No server running on host {}'.format(platform.node()))

    @commands.command(description='Starts a DCS/DCS-SRS server')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def startup(self, ctx):
        server = await utils.get_server(self, ctx)
        if server:
            installation = server['installation']
            if server['status'] in [Status.STOPPED, Status.SHUTDOWN]:
                await ctx.send('DCS server "{}" starting up ...'.format(server['server_name']))
                utils.start_dcs(self, server)
                server['status'] = Status.LOADING
                # set maintenance flag to prevent auto-stops of this server
                server['maintenance'] = True
                await self.bot.audit(
                    f"User {ctx.message.author.display_name} started DCS server \"{server['server_name']}\".")
            else:
                await ctx.send('DCS server "{}" is already started.'.format(server['server_name']))
            if 'SRS_CONFIG' in self.config[installation]:
                if not utils.is_open(self.config[installation]['SRS_HOST'], self.config[installation]['SRS_PORT']):
                    if await utils.yn_question(self, ctx, 'Do you want to start the DCS-SRS server "{}"?'.format(server['server_name'])) is True:
                        await ctx.send('DCS-SRS server "{}" starting up ...'.format(server['server_name']))
                        utils.start_srs(self, server)
                        await self.bot.audit(
                            f"User {ctx.message.author.display_name} started DCS-SRS server \"{server['server_name']}\".")
                else:
                    await ctx.send('DCS-SRS server "{}" is already started.'.format(server['server_name']))

    @commands.command(description='Shutdown a DCS/DCS-SRS server')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def shutdown(self, ctx):
        server = await utils.get_server(self, ctx)
        if server:
            installation = server['installation']
            if server['status'] in [Status.UNKNOWN, Status.LOADING]:
                await ctx.send('Server is currently starting up. Please wait and try again.')
            elif server['status'] not in [Status.STOPPED, Status.SHUTDOWN]:
                if await utils.yn_question(self, ctx, 'Do you want to shut down the '
                                                      'DCS server "{}"?'.format(server['server_name'])) is True:
                    await ctx.send('Shutting down DCS server "{}" ...'.format(server['server_name']))
                    utils.stop_dcs(self, server)
                    server['status'] = Status.SHUTDOWN
                    # set maintenance flag to prevent auto-starts of this server
                    server['maintenance'] = True
                    await self.bot.audit(
                        f"User {ctx.message.author.display_name} shut DCS server \"{server['server_name']}\" down.")
            else:
                await ctx.send('DCS server {} is already shut down.'.format(server['server_name']))
            if 'SRS_CONFIG' in self.config[installation]:
                if utils.check_srs(self, server):
                    if await utils.yn_question(self, ctx, 'Do you want to shut down the '
                                                          'DCS-SRS server "{}"?'.format(server['server_name'])) is True:
                        if utils.stop_srs(self, server):
                            await ctx.send('DCS-SRS server "{}" shutdown.'.format(server['server_name']))
                            await self.bot.audit(f"User {ctx.message.author.display_name} shut "
                                                 f"DCS-SRS server \"{server['server_name']}\" down.")
                        else:
                            await ctx.send('Shutdown of DCS-SRS server "{}" failed.'.format(server['server_name']))
                else:
                    await ctx.send('DCS-SRS server {} is already shut down.'.format(server['server_name']))

    async def do_update(self, warntimes: List[int], ctx=None):
        self.update_pending = True
        if ctx:
            await ctx.send('Shutting down DCS servers, warning users before ...')
        else:
            self.log.info('Shutting down DCS servers, warning users before ...')
        servers = []
        for server_name, server in self.globals.items():
            if 'maintenance' in server:
                servers.append(server)
            else:
                server['maintenance'] = True
            if server['status'] in [Status.RUNNING, Status.PAUSED]:
                for warntime in warntimes:
                    self.loop.call_later(warntime, self.bot.sendtoDCS,
                                         server, {
                                             'command': 'sendPopupMessage',
                                             'message': f'Server is going down for a DCS update in {warntime} seconds!',
                                             'to': 'all',
                                             'time': self.config['BOT']['MESSAGE_TIMEOUT']
                                         })
                self.loop.call_later(max(warntimes), utils.stop_dcs, self, server)
        # give the DCS servers some time to shut down.
        await asyncio.sleep(max(warntimes) + 10)
        if ctx:
            await ctx.send('Updating DCS World. Please wait, this might take some time ...')
        else:
            self.log.info('Updating DCS World ...')
        subprocess.run(['dcs_updater.exe', '--quiet', 'update'], executable=os.path.expandvars(
            self.config['DCS']['DCS_INSTALLATION']) + '\\bin\\dcs_updater.exe')
        utils.sanitize(self)
        if ctx:
            await ctx.send('DCS World updated to the latest version.\nStarting up DCS servers again ...')
        else:
            self.log.info('DCS World updated to the latest version.\nStarting up DCS servers again ...')
        self.update_pending = False
        for server_name, server in self.globals.items():
            if server not in servers:
                # let the scheduler do its job
                del server['maintenance']
            else:
                # the server was running before (being in maintenance mode), so start it again
                utils.start_dcs(self, server)

    @commands.command(description='Update a DCS Installation')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def update(self, ctx):
        # check versions
        branch, old_version = utils.getInstalledVersion(self.config['DCS']['DCS_INSTALLATION'])
        new_version = await utils.getLatestVersion(branch)
        if old_version == new_version:
            await ctx.send('Your installed version {} is the latest on branch {}.'.format(old_version, branch))
        elif new_version:
            if await utils.yn_question(self, ctx, 'Would you like to update from version {} to {}?\nAll running '
                                                  'DCS servers will be shut down!'.format(old_version,
                                                                                          new_version)) is True:
                await self.bot.audit(f"User {ctx.message.author.display_name} started an update of all DCS "
                                     f"servers on node {platform.node()}.")
                await self.do_update([120, 60], ctx)

    @commands.command(description='Change the password of a DCS server')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def password(self, ctx):
        server = await utils.get_server(self, ctx)
        if server:
            if server['status'] == Status.SHUTDOWN:
                msg = await ctx.send('Please enter the new password: ')
                response = await self.bot.wait_for('message', timeout=300.0)
                password = response.content
                await msg.delete()
                await response.delete()
                utils.changeServerSettings(server['server_name'], 'password', password)
                await ctx.send('Password has been changed.')
                await self.bot.audit(f"User {ctx.message.author.display_name} changed the password "
                                     f"of server \"{server['server_name']}\".")
            else:
                await ctx.send('Server "{}" has to be shut down to change the password.'.format(server['server_name']))

    @commands.command(description='Kick a user by name', usage='<name>')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def kick(self, ctx, name, *args):
        server = await utils.get_server(self, ctx)
        if server:
            if len(args) > 0:
                reason = ' '.join(args)
            else:
                reason = 'n/a'
            self.bot.sendtoDCS(server, {"command": "kick", "name": name, "reason": reason})
            await ctx.send(f'User "{name}" kicked.')
            await self.bot.audit(f'User {ctx.message.author.display_name} kicked player {name}' +
                                 (f' with reason "{reason}".' if reason != 'n/a' else '.'))

    @commands.command(description='Bans a user by ucid or discord id', usage='<member / ucid> [reason]')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def ban(self, ctx, user: Union[discord.Member, str], *args):
        if len(args) > 0:
            reason = ' '.join(args)
        else:
            reason = 'n/a'
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                if isinstance(user, discord.Member):
                    # a player can have multiple ucids
                    cursor.execute('SELECT ucid FROM players WHERE discord_id = %s', (user.id, ))
                    ucids = [row[0] for row in cursor.fetchall()]
                else:
                    # ban a specific ucid only
                    ucids = [user]
                for ucid in ucids:
                    for server in self.globals.values():
                        self.bot.sendtoDCS(server, {
                            "command": "ban",
                            "ucid": ucid,
                            "reason": reason
                        })
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    @commands.command(description='Unbans a user by ucid or discord id', usage='<member / ucid>')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def unban(self, ctx, user: Union[discord.Member, str]):
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                if isinstance(user, discord.Member):
                    # a player can have multiple ucids
                    cursor.execute('SELECT ucid FROM players WHERE discord_id = %s', (user.id, ))
                    ucids = [row[0] for row in cursor.fetchall()]
                else:
                    # unban a specific ucid only
                    ucids = [user]
                for ucid in ucids:
                    for server in self.globals.values():
                        self.bot.sendtoDCS(server, {"command": "unban", "ucid": ucid})
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    @tasks.loop(minutes=1.0)
    async def update_bot_status(self):
        for server_name, server in self.globals.items():
            if server['status'] in const.STATUS_EMOJI.keys():
                await self.bot.change_presence(activity=discord.Game(const.STATUS_EMOJI[server['status']] + ' ' +
                                                                     re.sub(self.config['FILTER']['SERVER_FILTER'],
                                                                            '', server_name).strip()))
                await asyncio.sleep(10)

    @tasks.loop(minutes=5.0)
    async def check_for_dcs_update(self):
        # don't run, if an update is currently running
        if self.update_pending:
            return
        branch, old_version = utils.getInstalledVersion(self.config['DCS']['DCS_INSTALLATION'])
        new_version = await utils.getLatestVersion(branch)
        if new_version and old_version != new_version:
            self.log.info('A new version of DCS World is available. Auto-updating ...')
            await self.do_update([120, 60])

    @check_for_dcs_update.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


class Master(Agent):

    @commands.command(description='Prune unused data in the database', hidden=True)
    @utils.has_role('Admin')
    @commands.guild_only()
    async def prune(self, ctx):
        if not await utils.yn_question(self, ctx, 'This will remove old data from your database and compact it.\nAre '
                                                  'you sure?'):
            return
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                # delete non-members that haven't a name with them (very old data)
                cursor.execute('DELETE FROM statistics WHERE player_ucid IN (SELECT ucid FROM players WHERE '
                               'discord_id = -1 AND name IS NULL)')
                cursor.execute('DELETE FROM players WHERE discord_id = -1 AND name IS NULL')
                # delete players that haven't shown up for 6 month
                cursor.execute("DELETE FROM statistics WHERE player_ucid IN (SELECT ucid FROM players WHERE last_seen "
                               "IS NULL OR last_seen < NOW() - interval '6 month')")
                cursor.execute("DELETE FROM players WHERE last_seen IS NULL OR last_seen < NOW() - interval '6 month'")
            conn.commit()
            await self.bot.audit(f'User {ctx.message.author.display_name} pruned the database.')
        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            self.bot.log.exception(error)
        finally:
            self.bot.pool.putconn(conn)

    @commands.command(description='Bans a user by ucid or discord id', usage='<member / ucid> [reason]')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def ban(self, ctx, user: Union[discord.Member, str], *args):
        if len(args) > 0:
            reason = ' '.join(args)
        else:
            reason = 'n/a'
        conn = self.bot.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                if isinstance(user, discord.Member):
                    # a player can have multiple ucids
                    cursor.execute('SELECT ucid FROM players WHERE discord_id = %s', (user.id, ))
                    ucids = [row[0] for row in cursor.fetchall()]
                else:
                    # ban a specific ucid only
                    ucids = [user]
                for ucid in ucids:
                    cursor.execute('INSERT INTO bans (ucid, banned_by, reason) VALUES (%s, %s, %s)',
                                   (ucid, ctx.message.author.display_name, reason))
                conn.commit()
                await super().ban(self, ctx, user, *args)
            await ctx.send('Player {} banned.'.format(user))
            await self.bot.audit(f'User {ctx.message.author.display_name} banned ' +
                                 (f'member {user.display_name}' if isinstance(user, discord.Member) else f' ucid {user}') +
                                 (f' with reason "{reason}"' if reason != 'n/a' else ''))
        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            self.bot.log.exception(error)
        finally:
            self.bot.pool.putconn(conn)

    @commands.command(description='Unbans a user by ucid or discord id', usage='<member / ucid>')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def unban(self, ctx, user: Union[discord.Member, str]):
        conn = self.bot.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                if isinstance(user, discord.Member):
                    # a player can have multiple ucids
                    cursor.execute('SELECT ucid FROM players WHERE discord_id = %s', (user.id, ))
                    ucids = [row[0] for row in cursor.fetchall()]
                else:
                    # unban a specific ucid only
                    ucids = [user]
                for ucid in ucids:
                    cursor.execute('DELETE FROM bans WHERE ucid = %s', (ucid, ))
                conn.commit()
                await super().unban(self, ctx, user)
            await ctx.send('Player {} unbanned.'.format(user))
            await self.bot.audit(f'User {ctx.message.author.display_name} unbanned ' +
                                 (f'member {user.display_name}' if isinstance(user, discord.Member) else f' ucid {user}'))
        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            self.bot.log.exception(error)
        finally:
            self.bot.pool.putconn(conn)

    def format_bans(self, rows):
        embed = discord.Embed(title='List of Bans', color=discord.Color.blue())
        ucids = names = reasons = ''
        for ban in rows:
            if ban['discord_id'] != -1:
                user = self.bot.get_user(ban['discord_id'])
            else:
                user = None
            names += (user.name if user else ban['name'] if ban['name'] else '<unknown>') + '\n'
            ucids += ban['ucid'] + '\n'
            reasons += ban['reason'] + '\n'
        embed.add_field(name='UCID', value=ucids)
        embed.add_field(name='Name', value=names)
        embed.add_field(name='Reason', value=reasons)
        return embed

    @commands.command(description='Shows active bans')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def bans(self, ctx):
        conn = self.bot.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute('SELECT b.ucid, COALESCE(p.discord_id, -1) AS discord_id, p.name, b.banned_by, '
                               'b.reason FROM bans b LEFT OUTER JOIN players p on b.ucid = p.ucid')
                rows = list(cursor.fetchall())
                await utils.pagination(self, ctx, rows, self.format_bans, 20)
        except (Exception, psycopg2.DatabaseError) as error:
            self.bot.log.exception(error)
        finally:
            self.bot.pool.putconn(conn)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        self.bot.log.debug('Member {} has left guild {} - ban them on DCS servers (optional) '
                           'and delete their stats.'.format(member.display_name, member.guild.name))
        conn = self.bot.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                if self.bot.config.getboolean('BOT', 'AUTOBAN') is True:
                    cursor.execute('INSERT INTO bans SELECT ucid, \'DCSServerBot\', \'Player left guild.\' FROM '
                                   'players WHERE discord_id = %s', (member.id, ))
                cursor.execute('DELETE FROM statistics WHERE player_ucid IN (SELECT ucid FROM players WHERE '
                               'discord_id = %s)', (member.id, ))
                conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.bot.log.exception(error)
            conn.rollback()
        finally:
            self.bot.pool.putconn(conn)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        conn = self.bot.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                # try to match new users with existing but unmatched DCS users
                ucid = utils.match_user(self, member)
                if ucid:
                    cursor.execute(
                        'UPDATE players SET discord_id = %s WHERE ucid = %s AND discord_id = -1', (member.id, ucid))
                    await self.bot.audit(f"New member {member.display_name} could be matched to ucid {ucid}.")
                else:
                    await self.bot.audit(f"New member {member.display_name} could not be matched to a DCS user.")
                # auto-unban them if they were auto-banned
                if self.bot.config.getboolean('BOT', 'AUTOBAN') is True:
                    self.bot.log.debug('Member {} has joined guild {} - remove possible '
                                       'bans from DCS servers.'.format(member.display_name, member.guild.name))
                    cursor.execute('DELETE FROM bans WHERE ucid IN (SELECT ucid FROM players WHERE '
                                   'discord_id = %s)', (member.id, ))
                conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.bot.log.exception(error)
            conn.rollback()
        finally:
            self.bot.pool.putconn(conn)
        self.eventlistener.updateBans()


def setup(bot: DCSServerBot):
    if bot.config.getboolean('BOT', 'MASTER') is True:
        bot.add_cog(Master(bot, AdminEventListener))
    else:
        bot.add_cog(Agent(bot, AdminEventListener))
