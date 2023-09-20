# Welcome to DCSServerBot 2.0
You've found a comprehensive solution that lets you administrate your DCS instances via Discord, has built in per-server
and per-user statistics, optional cloud-based statistics, [coalitions](./COALITIONS.md) support and much more! With its 
plugin system and reporting framework, DCSServerBot can be enhanced very easily to support whatever might come into your 
mind. 

This documentation will show you the main features, how to install and configure the bot and some more sophisticated 
stuff at the bottom, if you for instance run multiple servers maybe even over multiple locations. 

If you don't need statistics and search a smaller and easier to install solution, you might want to look at my
[DCSServerBotLight](https://github.com/Special-K-s-Flightsim-Bots/DCSServerBotLight), which can do some of the stuff
you see in here already, without the need of any PostgreSQL-database.

Now let's see, what DCSServerBot can do for you (installation instructions below)!

Attention: 

---
## Plugins
DCSServerBot has a modular architecture with plugins that support specific Discord commands or allow events from connected DCS servers to be processed.
It comes with a rich set of default plugins but can be enhanced either by optional plugins provided by me or some that you wrote on your own.

### General Administrative Commands
These commands can be used to administrate the bot itself.

| Command     | Parameter | Channel       | Role    | Description                                                                                                                                                                                                               |
|-------------|-----------|---------------|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| .reload     | [Plugin]  | all           | Admin   | Reloads one or all plugin(s) and their configurations from disk.                                                                                                                                                          |
| .upgrade    |           | all           | Admin   | Upgrades the bot to the latest available version (git needed, see below).                                                                                                                                                 |
| .rename     | newname   | admin-channel | Admin   | Renames a DCS server. DCSServerBot auto-detects server renaming, too.                                                                                                                                                     |
| .unregister |           | admin-channel | Admin   | Unregisters the current server from this agent.<br/>Only needed, if the very same server is going to be started on another machine connected to another agent (see "Moving a Server from one Location to Another" below). |

### List of supported Plugins
| Plugin       | Scope                                                                 | Optional | Depending on          | Documentation                              |
|--------------|-----------------------------------------------------------------------|----------|-----------------------|--------------------------------------------|
| GameMaster   | Interaction with the running mission (inform users, set flags, etc)   | no       |                       | [README](./plugins/gamemaster/README.md)   |
| Mission      | Handling of missions, compared to the WebGUI.                         | no       | GameMaster            | [README](./plugins/mission/README.md)      |
| Scheduler    | Autostart / -stop of servers or missions, change weather, etc.        | yes*     | Mission               | [README](./plugins/scheduler/README.md)    |
| Admin        | Admin commands to manage your DCS server.                             | yes*     |                       | [README](./plugins/admin/README.md)        |
| UserStats    | Users statistics system.                                              | yes*     | Mission               | [README](./plugins/userstats/README.md)    |
| CreditSystem | User credits, based on achievements.                                  | yes*     | Mission               | [README](./plugins/creditsystem/README.md) |
| MissionStats | Detailed users statistics / mission statistics.                       | yes*     | Userstats             | [README](./plugins/missionstats/README.md) |
| Punishment   | Punish users for teamhits or teamkills.                               | yes      | Mission               | [README](./plugins/punishment/README.md)   |
| SlotBlocking | Slotblocking either based on units or a point based system.           | yes      | Mission, Creditsystem | [README](./plugins/slotblocking/README.md) |
| Cloud        | Cloud-based statistics and global ban system.                         | yes      | Userstats             | [README](./plugins/cloud/README.md)        |
| ServerStats  | Server statistics for your DCS servers.                               | yes      | Userstats             | [README](./plugins/serverstats/README.md)  |
| GreenieBoard | Greenieboard and LSO quality mark analysis (SC and Moose.AIRBOSS)     | yes      | Missionstats          | [README](./plugins/greenieboard/README.md) |
| MOTD         | Generates a message of the day.                                       | yes      | Mission, Missionstats | [README](./plugins/motd/README.md)         |
| FunkMan      | Support for [FunkMan](https://github.com/funkyfranky/FunkMan)         | yes      |                       | [README](./plugins/funkman/README.md)      |
| DBExporter   | Export the whole DCSServerBot database as json.                       | yes      |                       | [README](./plugins/dbexporter/README.md)   |
| OvGME        | Install or update mods into your DCS server.                          | yes      |                       | [README](./plugins/ovgme/README.md)        |
| Commands     | Map executables or shell commands to custom discord commands.         | yes      |                       | [README](./plugins/commands/README.md)     |
| Music        | Upload and play music over SRS.                                       | yes      |                       | [README](./plugins/music/README.md)        |
| Backup       | Backup your servers, database and bot configuration to a cloud drive. | yes      |                       | [README](./plugins/backup/README.md)       |

*) These plugins are loaded by the bot by default, but they are not necessarily needed to operate the bot. If you
want to remove them, overwrite PLUGINS in your dcsserverbot.ini.

### How to install 3rd-Party Plugins
Whenever someone else provides a plugin, they most likely do that as a zip file. You can just download any
plugin zipfile into the plugins directory. They will get unpacked automatically on the next start of DCSServerBot. 

### In case you want to write your own Plugin ...
There is a sample in the plugins/samples subdirectory, that will guide you through the steps. 
If you want your plugin to be added to the distribution, just contact me via the contact details below.

## Extensions
Many DCS admins use extensions or add-ons like DCS-SRS, Tacview, Lotatc, etc.</br>
DCSServerBot supports some of them already and can add a bit of quality of life. 
Check out [Extensions](./extensions/README.md) for more info on how to use them.

---
## Installation

### Prerequisites
You need to have [python 3.9](https://www.python.org/downloads/) (or higher) and [PostgreSQL](https://www.postgresql.org/download/) installed.
The python modules needed are listed in requirements.txt and can be installed with ```pip3 install -r requirements.txt```.
If using PostgreSQL remotely over unsecured networks, it is recommended to have SSL enabled.
For autoupdate to work, you have to install [GIT](https://git-scm.com/download/win) and make sure, ```git``` is in your PATH.

### Discord Token
The bot needs a unique Token per installation. This one can be obtained at http://discord.com/developers <br/>
Create a "New Application", add a Bot, select Bot from the left menu, give it a nice name and icon, press "Copy" below "Click to Reveal Token".
Now your Token is in your clipboard. Paste it in dcsserverbot.ini in your config-directory.
Both "Privileged Gateway Intents" have to be enabled on that page.<br/>
To add the bot to your Discord guild, select "OAuth2" from the menu, then "URL Generator", select the "bot" checkbox, and then select the following permissions:
_Manage Channels, Send Messages, Manage Messages, Embed Links, Attach Files, Read Message History, Add Reactions_
Press "Copy" on the generated URL, paste it into the browser of your choice, select the guild the bot has to be added to - and you're done!
For easier access to channel IDs, enable "Developer Mode" in "Advanced Settings" in Discord.

### Download
Best is to use ```git clone https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot.git``` as you then can use the 
autoupdate functionality of the bot.<br/>
Otherwise download the latest release version and extract it somewhere on your PC that is running the DCS server(s) and 
give it write permissions, if needed. 

**Attention:** Make sure that the bots installation directory can only be seen by yourself and is not exposed to anybody outside via www etc.

### Database
DCSServerBot uses PostgreSQL to store all information that needs to be persisted, like players, mission information, 
statistics and whatnot. Therefor, it needs a fast database. Starting with SQLite back in the days, I decided to move
over to PostgreSQL with version 2.0 already and never regret it.<br/>
Just install PostgreSQL from the above-mentioned website (current version at the time of writing is somewhat about 14, 
but will run with any newer version than that, too). 

### DCSServerBot Installation
Just run the provided ```install``` script. It will search for existing DCS installations, create a database user and 
database and asks you to add existing DCS servers to the configuration file (see below).

---
## Configuration
The bot configuration is held in **config/dcsserverbot.ini**. See **dcsserverbot.ini.sample** for an example.<br/>
If you run the ```install``` script for the first time, it will generate a basic file for you that you can amend to your 
needs afterwards.<br/>
For some configurations, default values may apply. They are kept in config/default.ini. **Don't change this file**, 
just overwrite the settings, if you want to have them differently.

The following parameters can be used to configure the bot:

a) __BOT Section__

| Parameter           | Description                                                                                                                                                                                                                                                                                                                                                                                                          |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| OWNER               | The Discord ID of the bots owner (that's you!). If you don't know your ID, go to your Discord profile, make sure "Developer Mode" is enabled under "Advanced", go to "My Account", press the "..." besides your profile picture and select "Copy ID"                                                                                                                                                                 |
| TOKEN               | The token to be used to run the bot. Can be obtained at http://discord.com/developers.                                                                                                                                                                                                                                                                                                                               |
| PUBLIC_IP           | (Optional) Your public IP, if you have a dedicated one, otherwise the bot will determine your current one.                                                                                                                                                                                                                                                                                                           |
| DATABASE_URL        | URL to the PostgreSQL database used to store our data. **If login fails, check password for any special character!**                                                                                                                                                                                                                                                                                                 |
| USE_DASHBOARD       | Whether to use the fancy cmd dashboard or not (for performance reasons over slow RDP connections). Default is true.                                                                                                                                                                                                                                                                                                  |
| COMMAND_PREFIX      | The prefix to be used by Discord commands. Default is '.'                                                                                                                                                                                                                                                                                                                                                            |
| CHAT_COMMAND_PREFIX | The prefix to be used by in-game-chat commands. Default is '-'                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                        
| HOST                | IP the bot listens on for messages from DCS. Default is 127.0.0.1, to only accept internal communication on that machine.                                                                                                                                                                                                                                                                                            |
| PORT                | UDP port, the bot listens on for messages from DCS. Default is 10081. **__Don't expose this port to the outside world!__**                                                                                                                                                                                                                                                                                           |
| MASTER              | If true, start the bot in master-mode (default for one-bot-installations). If only one bot is running, then there is only a master.\nIf you have to use more than one bot installation, for multiple DCS servers that are spanned over several locations, you have to install one agent (MASTER = false) at every other location. All DCS servers of that location will then automatically register with that agent. |
| MASTER_ONLY         | True, if this is a master-only installation, set to false otherwise.                                                                                                                                                                                                                                                                                                                                                 |
| SLOW_SYSTEM         | If true, some timeouts are increased to allow slower systems to catch up. Default is false.                                                                                                                                                                                                                                                                                                                          |
| PLUGINS             | List of plugins to be loaded (**this overwrites the default, you usually don't want to touch it!**).                                                                                                                                                                                                                                                                                                                 |
| OPT_PLUGINS         | List of optional plugins to be loaded. Here you can add your plugins that you want to use and that are not loaded by default.                                                                                                                                                                                                                                                                                        |
| AUTOUPDATE          | If true, the bot auto-updates itself with the latest release on startup.                                                                                                                                                                                                                                                                                                                                             |
| AUTOBAN             | If true, members leaving the discord will be automatically banned (default = false).                                                                                                                                                                                                                                                                                                                                 |
| MESSAGE_BAN         | Ban-message to be displayed on DCS join, when people are auto-banned on DCS due to a Discord ban.                                                                                                                                                                                                                                                                                                                    |
| WIPE_STATS_ON_LEAVE | If true, stats will be wiped whenever someone leaves your discord (default = true).                                                                                                                                                                                                                                                                                                                                  |
| AUTOMATCH           | If false, users have to match themselves using the .linkme command (see [README](./plugins/userstats/README.md)). If true, the bot will do a best-guess-match.                                                                                                                                                                                                                                                       |
| DISCORD_STATUS      | (Optional) status to be displayed below the bots avatar in Discord.                                                                                                                                                                                                                                                                                                                                                  |
| GREETING_DM         | A greeting message, that people will receive as a DM in Discord, if they join your guild.                                                                                                                                                                                                                                                                                                                            |
| MESSAGE_TIMEOUT     | General timeout for popup messages (default 10 seconds).                                                                                                                                                                                                                                                                                                                                                             | 
| MESSAGE_AUTODELETE  | Delete messages after a specific amount of seconds. This is true for all statistics embeds, LSO analysis, greenieboard, but no usual user commands.                                                                                                                                                                                                                                                                  |
| DESANITIZE          | Whether to desanitize MissionScriping.lua or not (default = yes).                                                                                                                                                                                                                                                                                                                                                    |
| AUDIT_CHANNEL       | (Optional) The ID of an audit channel where audit events will be logged into. For security reasons, it is recommended that no users can delete messages in this channel.                                                                                                                                                                                                                                             |

b) __LOGGING Section__

| Parameter           | Description                                                                                     |
|---------------------|-------------------------------------------------------------------------------------------------|
| LOGLEVEL            | The level of logging that is written into the logfile (DEBUG, INFO, WARNING, ERROR, CRITICAL).  |
| LOGROTATE_COUNT     | Number of logfiles to keep (default: 5).                                                        |
| LOGROTATE_SIZE      | Number of bytes until which a logfile is rotated (default: 10 MB).                              |

c) __DB Section__

| Parameter           | Description                                                      |
|---------------------|------------------------------------------------------------------|
| MASTER_POOL_MIN     | Minimum number of database connections in the pool (on MASTER).  |
| MASTER_POOL_MAX     | Maximum number of database connections in the pool (on MASTER).  |
| AGENT_POOL_MIN      | Minimum number of database connections in the pool (on AGENT).   |
| AGENT_POOL_MAX      | Maximum number of database connections in the pool (on AGENT).   |


d) __ROLES Section__

| Parameter      | Description                                                                                                                   |
|----------------|-------------------------------------------------------------------------------------------------------------------------------|
| Admin          | The name of the admin role in you Discord.                                                                                    |
| DCS Admin      | The name of the role you'd like to give admin rights on your DCS servers (_Moderator_ for instance).                          |
| DCS            | The role of users being able to see their statistics and mission information (usually the general user role in your Discord). |
| GameMaster     | Members of this role can run commands that affect the mission behaviour or handle coalition specific details.                 |

e) __FILTER Section__ (Optional)

| Parameter      | Description                                                                                                                                                                                                                       |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TAG_FILTER     | Many groups have their own tag, that might make it difficult for the bot to match usernames. The usual tags like [Tag], =Tag= or similar ones, are supported already. If you see matching issues, you might want to try this one. |
| SERVER_FILTER  | Filter to shorten server names (if needed)                                                                                                                                                                                        |
| MISSION_FILTER | Filter to shorten mission names (if needed)                                                                                                                                                                                       |
| EVENT_FILTER   | Filter events from the missionstats plugin (optional). See [here](https://wiki.hoggitworld.com/view/DCS_singleton_world) for a complete list of events.                                                                           |

f) __REPORTS__ Section (Optional)

| Parameter   | Description                                                                                  |
|-------------|----------------------------------------------------------------------------------------------|
| NUM_WORKERS | Number of threads that render a graph.                                                       |
| CKJ_FONT    | One of TC, JP or KR to support Traditional Chinese, Japanese or Korean characters in reports. |

g) __DCS Section__

| Parameter                       | Description                                                                                                                                   |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| DCS_INSTALLATION                | The installation directory of DCS World.                                                                                                      |
| AUTOUPDATE                      | If true, your DCS server will be kept up-to-date automatically by the bot (default=false).                                                    |
| GREETING_MESSAGE_MEMBERS        | A greeting message, that people will receive in DCS chat, if they get recognized by the bot as a member of your discord.                      |
| GREETING_MESSAGE_UNMATCHED      | A greeting message, that people will receive in DCS chat, if they are unmatched.                                                              |
| SERVER_USER                     | The username to display as user no. 1 in the server (aka "Observer")                                                                          |
| MAX_HUNG_MINUTES                | The maximum amount in minutes the server is allowed to not respond to the bot until considered dead (default = 3). Set it to 0 to disable it. |
| MESSAGE_PLAYER_USERNAME         | Message that a user gets when using line-feeds or carriage-returns in their names.                                                            |
| MESSAGE_PLAYER_DEFAULT_USERNAME | Message that a user gets when being rejected because of a default player name (Player, Spieler, etc.).                                        |                                                                                                                                               |
| MESSAGE_BAN                     | Message a banned user gets when being rejected.                                                                                               |
| MESSAGE_AFK                     | Message for players that are kicked because of being AFK.                                                                                     |
| MESSAGE_SLOT_SPAMMING           | Message for players that got kicked because of slot spamming.                                                                                 |
| MESSAGE_SERVER_FULL             | Message for players that can't join because the server is full and available slots are reserverd for VIPs.                                    |

h) __Server Specific Sections__

This section has to be named **exactly** like your Saved Games\<instance> directory. Usual names are DCS.OpenBeta or DCS.openbeta_server.
If your directory is named DCS instead (stable version), just add these fields to the DCS category above.

| Parameter                  | Description                                                                                                                                                                                |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DCS_HOST                   | The internal (!) IP of the machine, DCS is running onto. If the DCS server is running on the same machine as the bot (default), this should be 127.0.0.1.                                  |
| DCS_PORT                   | Must be a unique value > 1024 of an unused port in your system. This is **NOT** the DCS tcp/udp port (10308), that is used by DCS but a unique different one. Keep the default, if unsure. |
| DCS_HOME                   | The main configuration directory of your DCS server installation (for Hook installation). Keep it empty, if you like to place the Hook by yourself.                                        |
| EVENTS_CHANNEL             | The ID of the channel where in-game events should be shown. If not specified, the CHAT_CHANNEL will be used instead. If set to -1, events will be disabled.                                |
| CHAT_CHANNEL               | The ID of the in-game chat channel to be used for the specific DCS server. Must be unique for every DCS server instance configured. If "-1", no chat messages will be generated.           |
| STATUS_CHANNEL             | The ID of the status-display channel to be used for the specific DCS server. Must be unique for every DCS server instance configured.                                                      |
| ADMIN_CHANNEL              | The ID of the admin-commands channel to be used for the specific DCS server. Must be unique for every DCS server instance configured.                                                      |
| AUTOSCAN                   | Scan for missions in Saved Games\..\Missions and auto-add them to the mission list (default = false).                                                                                      |
| AFK_TIME                   | Number of seconds a player is considered AFK when being on spectators for longer than AFK_TIME seconds. Default is -1 (disabled).                                                          |
| CHAT_LOG                   | true (default), log all chat messages from players in Saved Games\<installation>\Logs\chat.log                                                                                             |
| CHAT_LOGROTATE_COUNT       | Number of chat-logs to keep (default = 10).                                                                                                                                                |
| CHAT_LOGROTATE_SIZE        | Max size of a chat.log until it gets rotated (default 1 MB).                                                                                                                               |
| MISSIONS_DIR               | (Optional) If you want to use a central missions directory for multiple servers, you can set it in here.                                                                                   |
| PING_ADMIN_ON_CRASH        | Define if the role DCS Admin should be pinged when a server crash is being detected (default = true).                                                                                      |
| START_MINIMIZED            | DCS will start minimized as default. You can disabled that by setting this value to false.                                                                                                 |
| STATISTICS                 | If false, no statistics will be generated for this server. Default is true (see [Userstats](./plugins/userstats/README.md)).                                                               |
| MISSION_STATISTICS         | If true, mission statistics will be generated for all missions loaded in this server (see [Missionstats](./plugins/missionstats/README.md)).                                               | 
| DISPLAY_MISSION_STATISTICS | If true, the persistent mission stats embed is displayed in the servers stats channel (default = true).                                                                                    |
| PERSIST_MISSION_STATISTICS | If true, player data is exported in the missionstats table (default = true).                                                                                                               |
| PERSIST_AI_STATISTICS      | If true, AI data is exported, too (only player data otherwise), default = false.                                                                                                           |
| COALITIONS                 | Enable coalition handling (see [Coalitions](./COALITIONS.md)), default = false.                                                                                                            |                                                                                                                                                                                                                                                                                                                                                 
| ALLOW_PLAYERS_POOL         | Only for [Coalitions](./COALITIONS.md)                                                                                                                                                     |
| COALITION_LOCK_TIME        | The time you are not allowed to change [coalitions](./COALITIONS.md) in the format "nn days" or "nn hours". Default is 1 day.                                                              |
| Coalition Red              | Members of this role are part of the red coalition (see [Coalitions](./COALITIONS.md)).                                                                                                    |
| Coalition Blue             | Members of this role are part of the blue coalition (see [Coalitions](./COALITIONS.md)).                                                                                                   |
| COALITION_BLUE_EVENTS      | Coalition events channel for blue coalition (optional, see [Coalitions](./COALITIONS.md)).                                                                                                 |
| COALITION_BLUE_CHANNEL     | Coalition chat channel for blue coalition (optional, see [Coalitions](./COALITIONS.md)).                                                                                                   |
| COALITION_RED_EVENTS       | Coalition events channel for red coalition (optional, see [Coalitions](./COALITIONS.md)).                                                                                                  |
| COALITION_RED_CHANNEL      | Coalition chat channel for red coalition (optional, see [Coalitions](./COALITIONS.md)).                                                                                                    |

### DCS/Hook Configuration
The DCS World integration is done via Hooks. They are being installed automatically into your configured DCS servers by the bot.

### Desanitization
DCSServerBot desanitizes your MissionScripting environment. That means, it changes entries in {DCS_INSTALLATION}\Scripts\MissionScripting.lua.
If you use any other method of desanitization, DCSServerBot checks, if additional desanitizations are needed and conducts them.
**To be able to do so, you must change the permissions on the DCS-installation directory. Give the User group write permissions for instance.**
Your MissionScripting.lua will look like this afterwards:
```lua
do
	sanitizeModule('os')
	--sanitizeModule('io')
	--sanitizeModule('lfs')
	--_G['require'] = nil
	_G['loadlib'] = nil
	--_G['package'] = nil
end
```

### Custom MissionScripting.lua
If you want to use a **custom MissionScripting.lua** that has more sanitization (for instance for LotAtc, Moose, 
OverlordBot or the like) or additional lines to be loaded (for instance for LotAtc, or DCS-gRPC), just place the 
MissionScripting.lua of your choice in the config directory of the bot. It will be replaced on every bot startup then.

### Discord Configuration
The bot uses the following **internal** roles to apply specific permissions to commands.
You can change the role names to the ones being used in your discord. That has to be done in the dcsserverbot.ini 
configuration file. If you want to add multiple groups, separate them by comma (does **not** apply to coalition roles!).

| Role           | Description                                                                                                                                         |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| DCS            | People with this role are allowed to chat, check their statistics and gather information about running missions and players.                        |
| DCS Admin      | People with this role are allowed to restart missions, managing the mission list, ban and unban people.                                             |
| Admin          | People with this role are allowed to manage the server, start it up, shut it down, update it, change the password and gather the server statistics. |
| GameMaster     | People with this role can see both [coalitions](./COALITIONS.md) and run specific commands that are helpful in missions.                            |
| Coalition Blue | People with this role are members of the blue coalition (see [Coalitions](./COALITIONS.md)).                                                        |
| Coalition Red  | People with this role are members of the red coalition (see [Coalitions](./COALITIONS.md)).                                                         |

### Sample Configuration
To view some sample configurations for the bot or for each configurable plugin, look [here](config/samples/README.md).

### Auto-Banning
The bot supports automatically bans / unbans of players from the configured DCS servers, as soon as they leave / join your Discord guild.
If you like that feature, set _AUTOBAN = true_ in dcsserverbot.ini (default = false).

However, players that are being banned from your Discord or that are being detected as hackers are auto-banned from all your configured DCS servers without prior notice.

### Additional Security Features
Players that have no pilot ID (empty) or that share an account with others, will not be able to join your DCS server. 
This is not configurable, it's a general rule (and a good one in my eyes).

---
## Running of the Bot
To start the bot, you can either use the packaged ```run``` command or ```python run.py```.<br/>
If using _AUTOUPDATE=true_ it is recommended to start the bot via ```run```, as this runs it in a loop as it 
will close itself after an update has taken place.</br>
If you want to run the bot from autostart, create a small batch script, that will change to the bots installation 
directory and run the bot from there like so:
```cmd
@echo off
cd "<whereveryouinstalledthebot>\DCSServerBot"
:loop
venv\Scripts\python run.py
goto loop
```
DCSServerBot runs in a Python virtual environment, with its own independent set of Python libraries and packages.

---
## User Matching
The bot works best, if DCS users and Discord users are matched. See [README](./plugins/userstats/README.md) for details.

---
## How to do the more complex stuff?
DCSServerBot can be used to run a whole worldwide distributed set of DCS servers and therefore supports the largest communities.
The installation and maintenance of such a use-case is just a bit more complex than a single server installation.

### Setup Multiple Servers on a Single Host
DCSServerBot is able to contact DCS servers at the same machine or over the local network.

To run multiple DCS servers under control of DCSServerBot you just have to make sure that you configure different communication ports. This can be done with the parameter DCS_PORT in DCSServerBotConfig.lua. The default is 6666, you can just increase that for every server (6667, 6668, ...).
Don't forget to configure different Discord channels (CHAT_CHANNEL, STATUS_CHANNEL and ADMIN_CHANNEL) for every server, too.
To add subsequent servers, just follow the steps above, and you're good, unless they are on a different Windows server (see below).

DCSServerBot will autodetect all configured DCS servers on the first startup and generate a sample ini file for you already.

### Setup Multiple Servers on Multiple Host at the Same Location
To communicate with DCSServerBot over the network, you need to change two configurations.
By default, DCSServerBot is configured to be bound to the loopback interface (127.0.0.1) not allowing any external connection to the system. This can be changed in dcsserverbot.ini by using the LAN IP address of the Windows server running DCSServerBot instead.<br/>

**Attention:** The scheduler, .startup and .shutdown commands will only work without issues, if the DCS servers are on the same machine as the bot. 
So you might consider installing a bot instance on every server that you use in your network. Just configure them as agents (_MASTER = false_) and you are good.

### Setup Multiple Servers on Multiple Host at Different Locations
DCSServerBot is able to run in multiple locations, worldwide. In every location, one instance of DCSServerBot is needed to be installed in the local network containing the DCS server(s).
Only one single instance of the bot (worldwide) is to be configured as a master. This instance has to be up 24/7 to use the statistics or ban commands. Currently, DCSServerBot does not support handing over the master to other bot instances, if the one and only master goes down.
To configure a server as a master, you have to set _MASTER = true_ (default) in the dcsserverbot.ini configuration file. Every other instance of the bot has to be set as an agent (_MASTER = false_).
The master and all agents are collecting statistics of the DCS servers they control, but only the master runs the statistics module to display them in Discord. To be able to write the statistics to the **central** database, all servers need access to the database. You can either host that database at the location where the master runs and enable all other agents to access that instance (keep security like SSL encryption in mind) or you use a cloud database, available on services like Amazon, Heroku, etc.

### Moving a Server from one Location to Another
When running multiple servers over different locations it might be necessary to move a server from one location to another. As all servers are registered with their local bots, some steps are needed to move a server over.
1) Stop the server in the **old** location from where it should be moved (```.shutdown```)
2) Goto the ADMIN_CHANNEL of that server and type ```.unregister```
3) Remove the entries of that server from the dcsserverbot.ini at the **old** location.
4) Configure a server at the **new** location with the very same name and make sure the correct channels are configured in dcsserverbot.ini of that server.
5) Reload the configuration of that server using the ```.reload``` command.
6) Start the server at the **new** location.

### How to talk to the Bot from inside Missions
If you plan to create Bot-events from inside a DCS mission, that is possible! Just make sure, you include this line in a trigger:
```lua
  dofile(lfs.writedir() .. 'Scripts/net/DCSServerBot/DCSServerBot.lua')
```
_Don't use a Mission Start trigger, as this might clash with other plugins loading stuff into the mission._<br/> 
After that, you can for instance send chat messages to the bot using
```lua
  dcsbot.sendBotMessage('Hello World', '12345678') -- 12345678 is the ID of the channel, the message should appear, default is the configured chat channel
```
inside a trigger or anywhere else where scripting is allowed.

**Attention:** Channel always has to be a string, encapsulated with '', **not** a number.

Embeds can be sent using code similar to this snippet:
```lua
  title = 'Special K successfully landed at Kutaisi!'
  description = 'The unbelievable and unimaginable event happend. Special K succeeded at his 110th try to successfully land at Kutaisi, belly down.'
  img = 'https://i.chzbgr.com/full/8459987200/hB315ED4E/damn-instruction-manual'
  fields = {
    ['Pilot'] = 'sexy as hell',
    ['Speed'] = '130 kn',
    ['Wind'] = 'calm'
  }
  footer = 'Just kidding, they forgot to put their gear down!'
  dcsbot.sendEmbed(title, description, img, fields, footer)
```
They will be posted in the chat channel by default, if not specified otherwise (adding the channel id as a last parameter of the sendEmbed() call, see sendBotMessage() above).

If you like to use a single embed, maybe in the status channel, and update it instead, you can do that, too:
```lua
  title = 'RED Coalition captured Kutaisi!'
  description = 'After a successful last bombing run, RED succeeded in capturing the strategic base of Kutaisi.\nBLUE has to fight back **NOW** there is just one base left!'
  dcsbot.updateEmbed('myEmbed', title, description)
  --[....]
  title = 'Mission Over!'
  description = 'RED has won after capturing the last BLUE base Batumi, congratulations!'
  img = 'http://3.bp.blogspot.com/-2u16gMPPgMQ/T1wfXR-bn9I/AAAAAAAAFrQ/yBKrNa9Q88U/s1600/chuck-norris-in-war-middle-east-funny-pinoy-jokes-2012.jpg'
  dcsbot.updateEmbed('myEmbed', title, description, img)
```
If no embed named "myEmbed" is there already, the updateEmbed() call will generate it for you, otherwise it will be replaced with this one.

---
## Contact / Support
If you need support, if you want to chat with me or other users or if you like to contribute, jump into my [Support Discord](https://discord.gg/zjRateN).

If you like what I do, and you want to support me, you can do that via my [Patreon Page](https://www.patreon.com/DCS_SpecialK).

---
## Credits
Thanks to the developers of the awesome solutions [HypeMan](https://github.com/robscallsign/HypeMan) and [perun](https://github.com/szporwolik/perun), that gave me the main ideas to this solution.
I gave my best to mark parts in the code to show where I copied some ideas or even code from you guys, which honestly is just a very small piece. Hope that is ok.
