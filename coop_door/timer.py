from machine.timer import Timer as MachineTimer

class Timer():
    def __init__(self, timeout_ms, timeout_slot):
        self.machine_timer = MachineTimer()
        self.timeout_slot = timeout_slot
        self.timeout_ms = timeout_ms

    def start(self):
        self.machine_timer.init(period=self.timeout_ms, callback=self.timeout_slot)

    def stop(self):
        self.machine_timer.deinit()

            
