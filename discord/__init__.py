from . import controllers
from . import models
from . import lib
from . import services


def _post_init_hook(env):
    """模組安裝/升級後重啟 Discord Bot"""
    env['discord.bot.manager'].restart_bot()
