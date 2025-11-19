# stepper_class_shiftregister_multiprocessing.py
#
# Stepper class for Lab 8 — simultaneous control of multiple stepper motors
# using shift registers and multiprocessing on Raspberry Pi Zero.

import time
import multiprocessing
from multiprocessing import Value
from shifter import Shifter  # custom Shifter class


class Stepper:
    """
    Supports operation of an arbitrary number of stepper motors using
    one or more shift registers.

    A class attribute (shifter_outputs) keeps track of all
    shift register output values for all motors.
    """

    # ===== Class Attributes =====
    num_steppers = 0         # track number of Stepper objects created
    from multiprocessing import Value
    shifter_outputs = Value('i', 0)  # shared 32-bit integer for all motors
      # combined output bits for all motors
    seq = [0b0001, 0b0011, 0b0010, 0b0110,
           0b0100, 0b1100, 0b1000, 0b1001]  # CCW sequence
    delay = 1500             # delay between motor steps [us]
    steps_per_degree = 4096 / 360.0  # 4096 steps per revolution

    # ===== Initialization =====
    def __init__(self, shifter, lock):
        self.s = shifter
        self.angle = Value('d', 0.0)      # current angle (shared across processes)
        self.step_state = 0               # sequence index
        self.shifter_bit_start = 4 * Stepper.num_steppers # starting bit in 8-bit reg
        self.lock = lock

        Stepper.num_steppers += 1

    # ===== Utility =====
    def __sgn(self, x):
        if x == 0:
            return 0
        return int(abs(x) / x)

    # ===== One step =====
    def __step(self, dir):
        """Take one step in the given direction (+1 or -1)."""
        self.step_state = (self.step_state + dir) % 8
        pattern = Stepper.seq[self.step_state] << self.shifter_bit_start

        # Safely modify shared outputs
        with self.lock:
            val = Stepper.shifter_outputs.value
            val &= ~(0b1111 << self.shifter_bit_start)  # clear this motor's bits
            val |= pattern                              # set this motor's bits
            Stepper.shifter_outputs.value = val
            self.s.shiftByte(val)


        # Update angle
        self.angle.value = (self.angle.value +
                            dir / Stepper.steps_per_degree) % 360

    # ===== Rotation worker =====
    def __rotate(self, delta):
        """Rotate the motor by delta degrees (relative)."""
        numSteps = int(Stepper.steps_per_degree * abs(delta))
        dir = self.__sgn(delta)

        for _ in range(numSteps):
            self.__step(dir)
            time.sleep(Stepper.delay / 1e6)

    # ===== Public rotate =====
    def rotate(self, delta):
        """Rotate by delta degrees and wait until done for this motor."""
        time.sleep(0.05)  # small stagger delay
        p = multiprocessing.Process(target=self.__rotate, args=(delta,))
        p.start()
        return p # wait for rotation to complete before continuing
    # ===== Absolute rotation =====
    def goAngle(self, target_angle):
        current = self.angle.value
        delta = target_angle - current

    # Normalize large differences to find the shortest direction
        if delta > 180:
        # Example: current=10, target=350 → delta=340 → better to go -20°
            delta -= 360
        elif delta < -180:
        # Example: current=350, target=10 → delta=-340 → better to go +20°
            delta += 360
        return self.rotate(delta)

    # ===== Zero the motor =====
    def zero(self):
        self.angle.value = 0.0


# ===== Example usage =====
if __name__ == '__main__':
    # Configure shift register
    s = Shifter(data=16, latch=20, clock=21)

    # Shared multiprocessing lock
    lock = multiprocessing.Lock()

    # Create two stepper objects
    m1 = Stepper(s, lock)
    m2 = Stepper(s, lock)

    # Zero both motors
    m1.zero()
    m2.zero()

    # Example motion sequence (both run simultaneously)
    print("Zeroing motors...")
    m1.zero()
    m2.zero()

    # Both start moving at the same time initially
    p1 = m1.goAngle(90)
    p2 = m2.goAngle(-90)
    p1.join()
    p2.join()

    # Next — m1 keeps going while m2 reverses direction
    p1 = m1.goAngle(-45)
    p2 = m2.goAngle(45)
    p1.join()
    p2.join()
    
    # Now only m1 continues through its remaining sequence
    p1 = m1.goAngle(-135)
    p1.join()
    
    p1 = m1.goAngle(135)
    p1.join()
    
    p1 = m1.goAngle(0)
    p1.join()


    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nEnd of test.')
