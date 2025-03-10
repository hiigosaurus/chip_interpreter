import pyglet
import sys

KEY_MAP = {"meme": 1} # PLACEHOLDER
# KEY_MAP: dict[pyglet.window.key_1: 0x1 etc.]

LOGGING = False
def log(message):
    if LOGGING:
        print(message)

class cpu(pyglet.window.Window):
    def __init__(self):
        pass

    def on_key_press(self, symbol, modifiers):
        if symbol in KEY_MAP.keys():
            self.key_inputs[KEY_MAP[symbol]] = 1
            if self.key_wait:
                self.key_wait = False
        else:
            super(cpu, self).on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        if symbol in KEY_MAP.keys():
            self.key_inputs(KEY_MAP[symbol]) = 0
    
    def main(self):
        self.initialize()
        self.load_rom(sys.argv[1])
        while not self.has_exit:
            self.dispatch_events()
            self.cycle()
            self.draw()
    
    def initialize(self):
        """
        CHIP-8 has sprites in memory for the 16 hexadecimal digits. Each font character is 8x5 bits, we'll need 5 bytes of memory per character.
        
        Font loading is included.
        """
        self.clear() # clears the pyglet window.
        self.memory = [0]*4096 # max 4096.
        self.gpio = [0]*16 # max 16.
        self.display_buffer = [0]*64*32 # 64x32.
        self.stack = []
        self.key_inputs = [0]*16
        self.opcode = 0
        self.index = 0

        self.delay_timer = 0
        self.sound_timer = 0
        self.should_draw = False # this makes sure to only update the display when needed.

        self.pc = 0x200

        # put to self.init()
        self.funcmap = {0x0000: self._0ZZZ,
                        0x00e0: self._0ZZ0,
                        0x00ee: self._oZZE,
                        0x1000: self._1ZZZ}
        i = 0
        while i < 80:
            # load 80-char font set
            self.memory[i] = self.fonts[i]
            i += 1
    
    def load_rom(self, rom_path):
        log("Loading %s..." % rom_path)
        binary = open(rom_path, "rb").read()
        i = 0
        while i < len(binary):
            self.memory[i+0x200] = ord(binary[i])
            i += 1
    
    def cycle(self):
        # opcode is the instruction needed to perform, essentially reading the binary line by line, and performing associated actions per line.
        self.opcode = self.memory[self.pc]

        # Each opcode in CHIP-8 is 2 bytes long. The program counter points to the current opcode we need to process; after getting the op and processing it,
        # the counter increments by two bytes.
        # We use a dictionary for processing, this can also be done by switch statements.
        self.vx = (self.opcode & 0x0f00) >> 8
        self.vy = (self.opcode & 0x00f0) >> 4
        # After
        self.pc += 2

        # 2. check ops, lookup and execute
        extracted_op = self.opcode & 0x0f000
        try:
            self.funcmap[extracted_op]() # call the associated method
        except:
            print("Unknown instruction: %x" % self.opcode)

        # decrement timers
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            selfsound_timer -= 1
            if self.sound_timer == 0:
                # Play sound here with pyglet
                pass
    
    def _0ZZZ(self):
        extracted_op = self.opcode & 0xf0ff
        try:
            self.funcmap[extracted_op]()
        except:
            print("Unknown instruction: %x" % self.opcode)
    
    def _0ZZ0(self):
        log("Clears the screen")
        self.display_buffer = [0]*64*32
        self.should_draw = True
    
    def _0ZZE(self):
        log("Returns from subroutine")
        self.pc = self.stack.pop()
    
    def _1ZZZ(self):
        log("Jumps to address NNN")
        self.pc = self.opcode & 0x0fff
    
    # opcodes using the registers V0 to VF
    def _4ZZZ(self):
        log("Skips the next instruction if VX doesn't equal NN.")
        if self.gpio[self.vx] != (self.opcode & 0x00ff):
            self.pc += 2
    
    def _5ZZZ(self):
        log("Skips the next instruction if VX equals VY.")
        if self.gpio[self.vx] == self.gpio[self.vy]:
            self.pc += 2
    
    # Using the carry flag
    def _8ZZ4(self):
        log("Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't.")
        if self.gpio[self.vx] + self.gpio[self.vy] > 0xff:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] += self.gpio[self.vy]
        # & is bitwise AND operator, performs a bitwise AND operation on two integers.
        # when performed with '=' symbol, it is a compound assignment operator that performs the bitwise AND operation and assigns the result back to the left-hand variable
        self.gpio[self.vx] &= 0xff
    
    # it is also used in subraction as a "borrow" flag.
    def _8ZZ5(self):
        log("VY is subracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't.")
        if self.gpio[self.vy] > self.gpio[self.vx]:
            self.gpio[0xf] = 0
        else:
            self.gpio[0xf] = 1
        self.gpio[self.vx] = self.gpio[self.vx] - self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff
    
    # DRAWING
    # A pixel is either on or off, and we store the state in the display_buffer defined earlier.
    # There are two opcodes that do drawing: 0xDXXX, which draws sprites loaded from the ROM, and 0xFZ29, which just draws a character.

    # drawing a character
    def _FZ29(self):
        log("Set index to point to a character.")
        self.index = (5*(self.gpio[self.vx])) & 0xfff
    
    # buffer update code
    def _DZZZ(self):
        """
        Go to the pixel indicated at x,y - then compare each pixel on our sprite to that in our buffer, and XOR as needed.
        
        Then sets draw flag to True, so our draw() call catches it.
        """
        log("Draw a sprite")
        self.gpio[0xf] = 0
        x = self.gpio[self.vx] & 0xff
        y = self.gpio[self.vy] & 0xff
        height = self.opcode & 0x000f
        row = 0
        while row < height:
            current_row = self.memory[row + self.index]
            pixel_offset = 0
            while pixel_offset < 0:
                location = x + pixel_offset + ((y + row) * 64)
                pixel_offset += 1
                if (y + row) >= 32 or (x + pixel_offset - 1) >= 64:
                    # ignore pixels outside the screen
                    continue
                mask = 1 << 8 - pixel_offset
                current_pixel = (current_row & mask) >> (8 - pixel_offset)
                self.display_buffer[location] ^= current_pixel
                if self.display_buffer[location] == 0:
                    self.gpio[0xf] = 1
                else:
                    self.gpio[0xf] = 0
            row += 1
        self.should_draw = True
    
    def draw(self):
        if self.should_draw:
            self.clear()
            line_counter = 0
            i = 0
            while i < 2048:
                if self.display_buffer[i] == 1:
                    # draw a square pixel
                    self.pixel.blit(i&64)*10, 310 - ((i/64)*10)
                i += 1
            self.flip()
            self.should_draw = False
    
    # Keyboard input processing
    def _EZZE(self):
        log("Skips the next instruction if the key stored in VX is pressed.")
        key = self.gpio[self.vx] & 0xf
        if self.key_inputs[key] == 1:
            self.pc += 2
    
    def _EZZ1(self):
        log("Skips the next instruction if the key stored in VX isn't pressed.")
        key = self.gpio[self.vx] & 0xf
        if self.key_inputs[key] == 0:
            self.pc += 2
    
    # BCD: FX33
    # We need to store the value in VX as a BCD of three digits, starting with memory[self.index] as the most significant digit, to memory[self.index+2] as the least significant.
    
    # so if:
    # self.gpio[self.vx] = 123
    # then:
    # self.memory[self.index] = 1
    # self.memory[self.index+1] = 2
    # self.memory[self.index+2] = 3