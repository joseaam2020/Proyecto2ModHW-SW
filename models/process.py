from typing import List, Optional
from product import Product
from task import Task

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
                self.products.remove(product)

    def setup(self) -> None:
        """Performs any necessary setup for the process before starting."""
        for product in self.products:
            self.tasks[0].add_product(product)
