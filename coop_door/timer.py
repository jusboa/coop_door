from machine import Timer as MachineTimer

class Timer():
    PERIODIC = 0
    SINGLE_SHOT = 1
    def __init__(self, timeout_ms, timeout_slot, mode=PERIODIC):
        self.machine_timer = MachineTimer()
        self.timeout_slot = timeout_slot
        self.timeout_ms = timeout_ms
        if mode == self.PERIODIC:
            self.mode = self.machine_timer.PERIODIC
        elif mode == self.SINGLE_SHOT:
            self.mode = self.machine_timer.ONE_SHOT
        else:
            self.mode = None

    def start(self):
        self.machine_timer.init(mode=self.mode,
                                period=self.timeout_ms,
                                callback=lambda t : self.timeout_slot())

    def stop(self):
        self.machine_timer.deinit()

            
