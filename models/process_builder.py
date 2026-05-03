from models.process import Process  
from models.task import Task

class ProcessBuilder:
    def __init__(self, id: int):
        self.process = Process(id=id)
        self.prev_task = None
        self.task_counter = 0

    def add_task(self, task_time: int):
        self.task_counter += 1
        task = Task(id=self.task_counter, task_time=task_time)
        if self.prev_task:
            self.prev_task.set_next_task(task)
        self.process.add_task(task)
        self.prev_task = task
        return self

    def build(self):
        return self.process