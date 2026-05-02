# class Product implementation
class Product:
	"""Represents a product in the system.

	Attributes:
		id (any): Product ID.
		state (str): Product state ('P' for processing, 'Q' for queued, 'D' for done).
		task (any): Reference to the assigned task.
		process (any): Reference to the assigned process.
	"""

	def __init__(self, id, task, process):
		"""Initializes a Product with default state 'Q' (queued).

		Args:
			id (any): Product ID.
			task (any): Reference to the assigned task.
			process (any): Reference to the assigned process.
		"""
		self.id = id
		self.state = 'Q'
		self.task = task
		self.process = process

	def change_state_processing(self):
		"""Changes the product state to 'P' (processing)."""
		self.state = 'P'

	def change_state_quequed(self):
		"""Changes the product state to 'Q' (queued)."""
		self.state = 'Q'

	def change_state_done(self):
		"""Changes the product state to 'D' (done)."""
		self.state = 'D'

	def change_task(self, next_task):
		"""Changes the associated task.

		Args:
			next_task (any): The new task to associate with the product.
		"""
		self.task = next_task

	def change_process(self, next_process):
		"""Changes the associated process.

		Args:
			next_process (any): The new process to associate with the product.
		"""
		self.process = next_process
