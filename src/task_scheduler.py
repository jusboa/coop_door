from machine import Timer

class Task:
    def __init__(self, callback, period_tick):
        self.timer_tick = period_tick
        self.period_tick = period_tick
        self.callback = callback

    def tick(self):
        self.timer_tick -= 1
        if self.timer_tick <= 0:
            self.callback()
            self.timer_tick = self.period_tick

class TaskScheduler:
    def __init__(self, base_period_ms=10):
        self.timer = Timer()
        self.base_period_ms = base_period_ms
        self.tasks = []

    def start(self):
        self.timer.init(period=self.base_period_ms, callback=self.wakeup)

    def wakeup(self, timer):
        for task in self.tasks:
            task.tick()

    def add_task(self, callback, period_ms):
        self.tasks.append(Task(callback, round(period_ms / self.base_period_ms)))
