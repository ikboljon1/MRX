import time
# Важно: импортируем vision_manager здесь, внутри воркера
from brain import vision_manager


def vision_process_worker(task_queue, result_queue):
    """
    Эта функция будет выполняться в отдельном процессе.
    Она ждет заданий в task_queue, выполняет их и кладет результат в result_queue.
    """
    print("[VisionWorker] Процесс анализа зрения запущен.")

    while True:
        try:
            # .get() - это блокирующая операция. Процесс будет "спать",
            # пока в очередь не придет новое задание.
            command = task_queue.get()

            if command == "analyze":
                print("[VisionWorker] Получена команда 'analyze'. Начинаю анализ...")
                start_time = time.time()

                # Выполняем тяжелую задачу
                detected_people = vision_manager.identify_and_analyze_people()

                end_time = time.time()
                print(f"[VisionWorker] Анализ завершен за {end_time - start_time:.2f} сек. Отправляю результат.")

                # Кладем результат в очередь для основного процесса
                result_queue.put(detected_people)

            elif command == "shutdown":
                print("[VisionWorker] Получена команда 'shutdown'. Процесс завершается.")
                break

        except Exception as e:
            print(f"[VisionWorker ERROR] В процессе анализа произошла ошибка: {e}")