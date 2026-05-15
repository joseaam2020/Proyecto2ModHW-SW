from models.process_builder import ProcessBuilder
from models.product import Product

class PipelineBuilder:
    def __init__(self, processes_data,products_data):
        self.processes_data = processes_data
        self.products_data = products_data
        self.processes = []
        self.products = []

    def build(self):
        for pid, pdata in enumerate(self.processes_data, 1):
            builder = ProcessBuilder(pid)
            for task_time in pdata['tasks']:
                builder.add_task(task_time)
            self.processes.append(builder.build())

        for i, process in enumerate(self.processes):
            if i > 0:
                process.previous = self.processes[i-1]
            if i < len(self.processes) - 1:
                process.next = self.processes[i+1]
            process.is_first = (i == 0)
            process.is_last = (i == len(self.processes) - 1)

        for product_id in self.products_data:
            product = Product(id=product_id)
            self.products.append(product)
            self.processes[0].add_product(product)

        self.processes[0].setup()

        return self.processes
