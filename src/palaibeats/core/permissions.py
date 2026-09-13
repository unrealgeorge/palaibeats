"""DJ-role permission gate.

Anyone can browse the library / view the queue / see radio stations.
Actions that change playback (play, skip, stop, volume, radio management)
require either the configured DJ role or server-admin permissions.
"""

from __future__ import annotations

import discord


def is_dj(member: discord.Member, dj_role_name: str) -> bool:
    if member.guild_permissions.administrator:
        return True
    if member.id == member.guild.owner_id:
        return True
    return any(role.name.lower() == dj_role_name.lower() for role in member.roles)
