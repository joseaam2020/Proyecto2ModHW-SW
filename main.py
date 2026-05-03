from models.process import Process
from models.task import Task
from models.product import Product

if __name__ == "__main__":
    # Create a process
    process = Process(id=1)

    # Create two tasks with task_time 1
    task1 = Task(id=1, task_time=1)
    task2 = Task(id=2, task_time=1)

    # Link tasks
    task1.set_next_task(task2)
    process.add_task(task1)
    process.add_task(task2)

    # Create 5 products and add them to the process
    products = [Product(id=i+1) for i in range(5)]
    for product in products:
        process.add_product(product)

    # Setup process (assign products to first task)
    # The first tick is the setup phase where products are assigned to the first task
    process.setup()

    # Simulate ticks and print reports
    for tick in range(1, 8):

        print(f"\nTick {tick}")
        process.tick()

        report = process.generate_report()

        # Optionally save the report
        Process.save_report(report, tick)

        print(report)
