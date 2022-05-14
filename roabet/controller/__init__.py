from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from vgamepad import XUSB_BUTTON as BUTTONS
from .player import Player

if TYPE_CHECKING:
    from roabet.db import Character, Stage
    from collections.abc import Callable, Awaitable

class Controllers:
    """
    Class that manages controllers with asyncio.
    """
    def __init__(self, n: int, *, hazards=False):
        self.players = [Player(i + 1, woken=i==0) for i in range(n)]

        self.condensed_workshop: bool = False
        
        # match settings
        self.stock: int = 3
        self.time: int = 8
        self.hazards = hazards
    
    def reset_cursor_pos(self):
        for player in self.players:
            player.reset_cursor_pos()
    
    def set_workshop_length(self, n):
        for player in self.players:
            player.set_workshop_length(n)
    
    async def each_player(self, f: Callable[[Player], Awaitable]):
        """
        Runs a coroutine for each player.
        """
        # asyncio.gather is prone to controller desync
        # some slight deviation is fine though
        await asyncio.gather(*(f(player) for player in self.players))
        
        # for player in self.players:
        #     await f(player)
    
    async def init_local_play(self):
        """
        To be called while on the start screen.
        """
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
        await asyncio.sleep(2)
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
        await asyncio.sleep(2)
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
        await asyncio.sleep(2)
    
    async def init_com_players(self):
        """
        Has each player set themselves to a COM player.
        """
        await self.each_player(lambda p: p.init_com_player())
    
    async def _open_settings(self):
        await self.players[0].move_cursor_to(295, 35)
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
    
    async def _navigate_settings(self, delta):
        for _ in range(abs(delta)):
            await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_DPAD_DOWN if delta > 0
                else BUTTONS.XUSB_GAMEPAD_DPAD_UP)
    
    async def _change_setting(self, delta):
        for _ in range(abs(delta)):
            await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_DPAD_RIGHT if delta > 0
                else BUTTONS.XUSB_GAMEPAD_DPAD_LEFT)
    
    async def change_settings(self, **kwargs):
        opened_settings = False
        cursor_pos = 0
        if 'stock' in kwargs and kwargs['stock'] != self.stock:
            if not opened_settings: 
                await self._open_settings()
                opened_settings = True
            await self._navigate_settings(1 - cursor_pos)
            cursor_pos = 1
            await self._change_setting(kwargs['stock'] - self.stock)
            self.stock = kwargs['stock']
        
        if 'time' in kwargs and kwargs['time'] != self.time:
            if not opened_settings: 
                await self._open_settings()
                opened_settings = True
            await self._navigate_settings(2 - cursor_pos)
            cursor_pos = 2
            await self._change_setting(kwargs['time'] - self.time)
            self.time = kwargs['time']
        
        if opened_settings:
            await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
    
    async def select_fighters(self, *fighters: Character):
        await self.each_player(lambda p: p.cancel_character())
        for i, player in enumerate(self.players):
            set_condensed = False
            if not self.condensed_workshop:
                set_condensed = True
                self.condensed_workshop = True
            await player.select_character(fighters[i], set_condensed=set_condensed)
    
    async def confirm_fighters(self):
        """
        Advances from the fighter select screen to the stage select screen.
        In Tetherball mode, starts the battle.
        """
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_START)
        await asyncio.sleep(2)
        self.players[0].reset_cursor_pos(854, 354) # Random Stage is selected by default
    
    async def set_hazards(self, hazards: bool):
        """
        On stage select, toggles Aether mode (stage hazards)
        """
        if hazards != self.hazards:
            await self.players[0].move_cursor_to(600, 30)
            await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
            self.hazards = hazards
    
    async def select_stage(self, stage: Stage):
        """
        Selects the chosen stage and starts the battle.
        """
        # Only official stages are supported rn
        await self.players[0].move_cursor_to(stage.select_x, stage.select_y)
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
    
    async def exit_versus(self):
        """
        Exits from the character select screen.
        """
        await self.players[0].hold_button_for(BUTTONS.XUSB_GAMEPAD_B, 1.5)
    
    async def quit(self):
        """
        Quits the game from the character select screen.
        """
        await self.exit_versus()
        await asyncio.sleep(2)
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_B)
        await asyncio.sleep(2)
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_DPAD_UP)
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
        await self.players[0].press_button(BUTTONS.XUSB_GAMEPAD_A)
