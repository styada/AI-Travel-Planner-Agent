

class SupervisorAgent:
    def __init__(self, name):
        self.name = name

    def oversee(self, task):
        print(f"{self.name} is overseeing the task: {task}")