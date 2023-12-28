import time
import multiprocessing

# Function to calculate square and put the result in a queue
def calculate_square(num, result_queue):
    result = num * num
    result_queue.put((num, result))

if __name__ == "__main__":
    numbers = [1, 2, 3, 4, 5]

    # Without multiprocessing
    start_time = time.time()
    for num in numbers:
        result = num * num
        print(f"The square of {num} is: {result}")
    end_time = time.time()
    print(f"Execution time without multiprocessing: {end_time - start_time} seconds")

    # With multiprocessing
    start_time = time.time()
    result_queue = multiprocessing.Queue()

    processes = []
    for num in numbers:
        process = multiprocessing.Process(target=calculate_square, args=(num, result_queue))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    # Get results from the queue and print
    while not result_queue.empty():
        num, result = result_queue.get()
        print(f"The square of {num} is: {result}")

    end_time = time.time()
    print(f"Execution time with multiprocessing: {end_time - start_time} seconds")
