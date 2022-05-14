import asyncio
from cv2 import magnitude
import vgamepad
from vgamepad import XUSB_BUTTON as BUTTONS
from roabet.db import Character

PLAYER_SPACING = 238 # This is exact

# Since lag may cause positions to drift, we don't need everything to be super exact.
# My standard is to round values to the nearest 5.
PIXELS_PER_SECOND = 440

class Player:
    """
    Represents a player's controller.
    """
    
    def __init__(self, num, *, woken=True):
        """
        Connects a new controller with the given player num.
        The module itself doesn't guarantee num matches with the actual controller port,
        so please initialize them in order. Cursor positions are also uninitialized.
        """
        self.num: int = num
        self.gamepad = vgamepad.VX360Gamepad()
        self.cursor_x: int = 0
        self.cursor_y: int = 0
        self.cursor_workshop: int = 0
        self.woken = woken

        self.difficulty: int = 5
        self.workshop_length: int = 0
    
    def horiz_offset(self):
        return PLAYER_SPACING * (self.num - 1)
    
    def set_workshop_length(self, n):
        self.workshop_length = n
    
    async def hold_button_for(self, button, time: float):
        """
        Holds down button for time seconds, then releases it.
        """
        self.gamepad.press_button(button)
        self.gamepad.update()
        await asyncio.sleep(time)
        self.gamepad.release_button(button)
        self.gamepad.update()
    
    async def press_button(self, button):
        """
        A single firm button press with a pause after.
        """
        await self.hold_button_for(button, 0.15)
        await asyncio.sleep(0.15)
    
    async def init_com_player(self):
        """
        First-time setup to initialize this player as a COM player.
        Not needed afterwards, the game remembers our settings even if we exit out and play
        a different mode.
        """
        # The cursor moves at a different speed across the player card, so it's easier to just hardcode
        # Once we're a COM, though, we don't have to worry about this anymore.
        if self.woken:
            await self.hold_button_for(BUTTONS.XUSB_GAMEPAD_DPAD_DOWN, 0.3)
            await self.hold_button_for(BUTTONS.XUSB_GAMEPAD_DPAD_LEFT, 0.3)
            await self.press_button(BUTTONS.XUSB_GAMEPAD_A)
            self.cursor_x = 55 + self.horiz_offset()
            self.cursor_y = 335
        else:
            await self.press_button(BUTTONS.XUSB_GAMEPAD_A)
            self.woken = True
            await self.hold_button_for(BUTTONS.XUSB_GAMEPAD_DPAD_UP, 0.1)
            await self.hold_button_for(BUTTONS.XUSB_GAMEPAD_DPAD_LEFT, 0.3)
            await self.press_button(BUTTONS.XUSB_GAMEPAD_A)
            self.cursor_x = 55 + self.horiz_offset()
            self.cursor_y = 325

    def reset_cursor_pos(self, x=None, y=216):
        """
        Recalibrates the cursor to its default position, or to a given position.
        """
        self.cursor_x = x if x is not None else 120 + self.horiz_offset()
        self.cursor_y = y
        # self.cursor_workshop = 0 # does this happen sometimes?

    async def move_cursor_to(self, x: int, y: int):
        """
        Used to navigate the fighters menu. Use the dpad to move the cursor to the given position.
        """
        delta_x = x - self.cursor_x
        delta_y = y - self.cursor_y

        if delta_x > 0:
            await self.hold_button_for(BUTTONS.XUSB_GAMEPAD_DPAD_RIGHT, delta_x / PIXELS_PER_SECOND)
        elif delta_x < 0:
            await self.hold_button_for(BUTTONS.XUSB_GAMEPAD_DPAD_LEFT, -delta_x / PIXELS_PER_SECOND)
        
        if delta_y > 0:
            await self.hold_button_for(BUTTONS.XUSB_GAMEPAD_DPAD_DOWN, delta_y / PIXELS_PER_SECOND)
        elif delta_y < 0:
            await self.hold_button_for(BUTTONS.XUSB_GAMEPAD_DPAD_UP, -delta_y / PIXELS_PER_SECOND)
        
        self.cursor_x = x
        self.cursor_y = y
    
    async def cancel_character(self):
        await self.press_button(BUTTONS.XUSB_GAMEPAD_B)
    
    async def select_character(self, character: Character, *, set_condensed=False):
        """
        Selects the chosen Character.
        """
        await self.move_cursor_to(character.select_x, character.select_y)
        await self.press_button(BUTTONS.XUSB_GAMEPAD_A)
        if not character.official:
            if set_condensed:
                await self.press_button(BUTTONS.XUSB_GAMEPAD_Y)

            current_z = self.cursor_workshop // 16
            current_x = (self.cursor_workshop % 16) // 4
            current_y = self.cursor_workshop % 4
            target_z = character.workshop_index // 16
            target_x = (character.workshop_index % 16) // 4
            target_y = character.workshop_index % 4

            # 15 fighters = only 1 page. 16 fighters = 2 pages because of the random button
            max_z = self.workshop_length // 16
            last_page_length = ((self.workshop_length + 1) % 16) or 16

            if target_z != current_z:
                if min(current_z, target_z) + max_z + 1 - max(current_z, target_z) < abs(current_z - target_z):
                    direction = (BUTTONS.XUSB_GAMEPAD_RIGHT_SHOULDER if current_z > target_z 
                        else BUTTONS.XUSB_GAMEPAD_LEFT_SHOULDER)
                    magnitude = min(current_z, target_z) + max_z + 1 - max(current_z, target_z)
                    if current_x * 4 + current_y >= last_page_length:
                        # moving thru last page will move cursor to end of last page
                        current_x = (last_page_length - 1) // 4
                        current_y = (last_page_length - 1) % 4
                else:
                    direction = (BUTTONS.XUSB_GAMEPAD_RIGHT_SHOULDER if current_z < target_z 
                        else BUTTONS.XUSB_GAMEPAD_LEFT_SHOULDER)
                    magnitude = abs(current_z - target_z)
                    if target_z == max_z and current_x * 4 + current_y >= last_page_length:
                        # adjust to end of last page
                        current_x = (last_page_length - 1) // 4
                        current_y = (last_page_length - 1) % 4
                for _ in range(magnitude):
                    await self.press_button(direction)
            
            if current_y > target_y:
                # move up first
                for _ in range(current_y - target_y):
                    await self.press_button(BUTTONS.XUSB_GAMEPAD_DPAD_UP)

            for _ in range(abs(target_x - current_x)):
                await self.press_button(BUTTONS.XUSB_GAMEPAD_DPAD_LEFT if target_x < current_x 
                    else BUTTONS.XUSB_GAMEPAD_DPAD_RIGHT)
            
            if current_y < target_y:
                # move down last
                for _ in range(target_y - current_y):
                    await self.press_button(BUTTONS.XUSB_GAMEPAD_DPAD_DOWN)
            
            self.cursor_workshop = character.workshop_index

            await self.press_button(BUTTONS.XUSB_GAMEPAD_A)
            await asyncio.sleep(character.load_time) # give character time to load

    async def set_difficulty(self, level: int):
        """
        Sets COM difficulty to the chosen value.
        """
        if level > self.difficulty:
            await self.move_cursor_to(210 + self.horiz_offset(), 505)
        elif level < self.difficulty:
            await self.move_cursor_to(125 + self.horiz_offset(), 505)
        for _ in range(abs(level - self.difficulty)):
            await self.press_button(BUTTONS.XUSB_GAMEPAD_A)
        
        self.difficulty = level
