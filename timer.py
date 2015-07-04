import time

class Timer():
    """Timer.


    """
    def start_timer(self):
        self.start = time.time()

    def stop_timer(self):
        self.end = time.time()

    def elapsed_time(self):
        return self.end - self.start
