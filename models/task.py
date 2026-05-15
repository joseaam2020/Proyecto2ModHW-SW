from typing import List, Optional
from models.product import Product

class Task:
    """Represents a task in the process workflow.

    Attributes:
        id (int): Task ID.
        task_time (int): Number of ticks needed to finish a product.
        queue (List[Product]): List of products that are queued.
        product_in_process (Optional[Product]): Reference to the product being processed.
        state (str): 'P' for processing, 'NP' for not processing.
        current_time (int): Current tick.
        next_task (Optional['Task']): Reference to the next task in the process.
    """

    def __init__(self, id: int, task_time: int):
        """Initializes a Task.

        Args:
            id (int): Task ID.
            task_time (int): Number of ticks needed to finish a product.
        """
        self.id: int = id
        self.task_time: int = task_time
        self.queue: List[Product] = []
        self.product_in_process: Optional[Product] = None
        self.state: str = 'NP'
        self.current_time: int = 1
        self.next_task: Optional['Task'] = None

    def set_next_task(self, next_task: 'Task') -> None:
        """Sets the next task in the process.

        Args:
            next_task (Task): Reference to the next task.
        """
        self.next_task = next_task

    def add_product(self, product: Product) -> None:
        """Adds a product to the task's queue.

        Args:
            product (Product): The product to be added to the queue.
        """
        product.change_task(self.id)
        product.change_state_quequed()
        self.queue.append(product)

    def tick(self) -> None:
        """Advances the task by one tick, processing products as needed."""
        #print(f"Queue for Task {self.id}: {self.queue}")
        if self.state == 'NP' and self.queue:
            self.product_in_process = self.queue.pop(0)
            self.product_in_process.change_state_processing()
            self.state = 'P'
        elif self.state == 'P':
            if self.current_time == self.task_time:
                self.current_time = 1
                if self.next_task is None:
                    self.product_in_process.change_state_done()
                else:
                    self.next_task.add_product(self.product_in_process)

                if self.queue:
                    self.product_in_process = self.queue.pop(0)
                    self.product_in_process.change_state_processing()
                else:
                    self.product_in_process = None
                    self.state = 'NP'
            else:
                self.current_time += 1