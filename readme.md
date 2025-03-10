1. Input
2. Output
3. CPU
4. Memory

Inputs:
16-button keyboard. In python, we just need to store key input states and check these per cycle:
    self.key_inputs = [0]*16

Output:
For output, the machine uses a 64x32 display, and a simpe sound buzzer. The display is basically just an array of pixels that are either in the on or off state:
    self.display_buffer = [0]*32*64 # 64*32

Memory:
CHIP8 has memory that can hold up to 4086 bytes. This includes the interpreter istself, the fonts, and where it loads the program it is supposed to run. In python, this will be:
    self.memory = [0]*4096 # max 4096

Registers:
The CHIP8 has 16 8-bit registers (referred as Vx where x is the register number in Cogwood's CHIP-8 technical reference). These are generally used to store values for operations. The last register, Vf, is mostly used for flags and should be avoided for use in programs.
In python, we will be storing our register values as:
    self.gpio = [0]*16 # 16 zeroes
It also has 2 timer registers, that cause delays by decrementing to 0 for each cycle, wasting an operation in the process. In python, this will be as simple as defining two variables that we'll decrement per cycle.
    self.sound_timer = 0
    self.delay_timer = 0

It has an index register which is 16-bit.
    self.index = 0

The program counter is also 16-bit.
    self.pc = 0

There is also a stack pointer, which incluides the address of the topmost stack element. The stack has at most 16 elements in it at any given time. Since we're doing this in python, which as a list that we can pop/append to, we can ignore this and just make a list:
    self.stack = []