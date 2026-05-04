from typing import List, Optional
from models.product import Product
from models.task import Task
import json
import os 

class Process:
    """Represents a process in the workflow.

    Attributes:
        id (int): Unique identifier for the process.
        tasks (List[Task]): List of tasks associated with the process.
        products (List[Product]): List of products being processed.
        next (Optional[Process]): Reference to the next process.
        last (Optional[Process]): Reference to the process that called this process.
        is_first (bool): True if this is the first process.
        is_last (bool): True if this is the last process.
    """

    def __init__(self, id: int):
        """Initializes a Process.

        Args:
            id (int): Unique identifier for the process.
        """
        self.id: int = id
        self.tasks: List[Task] = []
        self.products: List[Product] = []
        self.next: Optional['Process'] = None
        self.previous: Optional['Process'] = None
        self.is_first: bool = False
        self.is_last: bool = False

    def add_task(self, task: Task) -> None:
        """Adds a task to the process.

        Args:
            task (Task): The task to be added.
        """
        self.tasks.append(task)

    def add_product(self, product: Product) -> None:
        """Adds a product to the process.

        Args:
            product (Product): The product to be added.
        """
        product.change_process(self.id)
        self.products.append(product)

    def set_next_process(self, next_process: 'Process') -> None:
        """Sets the next process in the workflow.

        Args:
            next_process (Process): The next process to be set.
        """
        self.next = next_process

    def set_previous_process(self, previous_process: 'Process') -> None:
        """Sets the previous process in the workflow.

        Args:
            previous_process (Process): The previous process to be set.
        """
        self.previous = previous_process

    def tick(self) -> None:
        """Advances the process by one tick, processing tasks and products as needed."""
        for task in self.tasks:
            task.tick()

        for product in self.products:
            if product.state == 'D' and self.next is not None:
                self.next.add_product(product)
                #TODO: Update or assign product to first task
                self.products.remove(product)

    def setup(self) -> None:
        """Performs any necessary setup for the process before starting."""
        for product in self.products:
            self.tasks[0].add_product(product)
            
    def generate_report(self) -> dict:
        """Generates a report of the current state of the process.

        Returns:
            dict: A dictionary containing the process ID, information about each product,
                and information about each task in the process.
        """
        return {
            "process_id": self.id,
            "products": [
                {"product_id": p.id, "state": p.state, "pid": p.pid, "tid": p.tid}
                for p in self.products
            ],
            "tasks": [
                {
                    "task_id": t.id,
                    "task_time": t.task_time,
                    "queue_product_ids": [p.id for p in t.queue],
                    "state": t.state,
                    "product_in_process_id": t.product_in_process.id if t.product_in_process else None,
                    "current_time": t.current_time,
                }
                for t in self.tasks
            ]
        }

    def save_report(self,tick: int) -> None:
        """Saves the given report as a JSON file in the reports directory.

        Args: report (dict): The report data to be saved.
            tick (int): The current tick number, used to name the report file.
        """
        os.makedirs("reports", exist_ok=True)
        report = self.generate_report()
        file_path : str = f"reports/report_tick_{tick:03d}.json"
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                #print(f"Proceso {self.id} creo y escribio en reporte {tick:03d}}")
                json.dump(report, f, indent=2)
        else:
            with open(file_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"No se pudo cargar json de reporte_tick_{tick:03d}")
                    data = []

            if not isinstance(data, list):
                data = [data]
                    
            data.append(report)
            with open(file_path,"w") as f:
                #print(f"Proceso {self.id} leyo y escribio en reporte {tick:03d}}")
                json.dump(data, f, indent=2) 
                
