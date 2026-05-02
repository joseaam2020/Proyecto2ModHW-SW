# class Product implementation
class Product:
	"""Represents a product in the system.

	Attributes:
		id (int): Product ID.
		state (str): Product state ('P' for processing, 'Q' for queued, 'D' for done).
		tid (int): Task ID.
		pid (int): Process ID.
	"""

	def __init__(self, id:int, tid:int, pid:int):
		"""Initializes a Product with default state 'Q' (queued).

		Args:
			id (int): Product ID.
			tid (int): Task ID.
			pid (int): Process ID.
		"""
		self.id: int = id
		self.state: str = 'Q'
		self.tid: int = tid
		self.pid: int = pid

	def change_state_processing(self) -> None:
		"""Changes the product state to 'P' (processing)."""
		self.state = 'P'

	def change_state_quequed(self) -> None:
		"""Changes the product state to 'Q' (queued)."""
		self.state = 'Q'

	def change_state_done(self) -> None:
		"""Changes the product state to 'D' (done)."""
		self.state = 'D'

	def change_task(self, next_tid: int) -> None:
		"""Changes the associated task.

		Args:
			next_tid (int): The new task ID to associate with the product.
		"""
		self.tid: int = next_tid

	def change_process(self, next_pid: int) -> None:
		"""Changes the associated process.

		Args:
			next_pid (int): The new process ID to associate with the product.
		"""
		self.pid: int = next_pid
