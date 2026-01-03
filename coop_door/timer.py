from machine import Timer as MachineTimer

class Timer():
    PERIODIC = 0
    SINGLE_SHOT = 1
    def __init__(self, timeout_ms, timeout_slot=None, mode=PERIODIC):
        self.machine_timer = MachineTimer()
        self.timeout_slot = timeout_slot
        self.timeout_ms = timeout_ms
        if mode == self.PERIODIC:
            self.mode = self.machine_timer.PERIODIC
        elif mode == self.SINGLE_SHOT:
            self.mode = self.machine_timer.ONE_SHOT
        else:
            self.mode = None
        self.is_active = False

    def start(self):
        self.is_active = True
        self.machine_timer.init(mode=self.mode,
                                period=self.timeout_ms,
                                callback=self._timeout)
    def _timeout(self, t):
        self.is_active = False
        if self.timeout_slot is not None:
            self.timeout_slot()

    def stop(self):
        self.machine_timer.deinit()
        self.is_active = False

            
    def active(self):
        return self.is_active
