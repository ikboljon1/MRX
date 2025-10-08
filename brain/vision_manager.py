# mrx_project/brain/vision_manager.py

import cv2
from deepface import DeepFace
import time
import os
import numpy as np
from memory import people_manager  # Импортируем нашу новую базу данных

# --- НАСТРОЙКИ ---
CAMERA_INDEX = 0     
DETECTOR_BACKEND = 'opencv'  # 'opencv' - самый быстрый для Raspberry Pi

_BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BRAIN_DIR)
FACES_DB_PATH = os.path.join(_PROJECT_ROOT, 'memory', 'faces')

# Убедимся, что папка для лиц существует
os.makedirs(FACES_DB_PATH, exist_ok=True)

# Глобальная переменная для хранения кадра с незнакомцем для последующего запоминания
last_unknown_face_img = None


def identify_and_analyze_people():
    """
    Захватывает кадр, находит все лица, пытается их распознать в нашей базе.
    Для каждого лица возвращает его статус (известен/неизвестен) и анализ.
    """
    global last_unknown_face_img
    print("[Vision] Активация камеры для распознавания...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[Vision ERROR] Не удалось получить доступ к камере.")
        return []

    time.sleep(1)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("[Vision ERROR] Не удалось захватиться кадр.")
        return []

    print("[Vision] Кадр получен. Поиск и анализ лиц...")
    results = []
    try:
        # DeepFace находит все лица на изображении
        all_faces_analysis = DeepFace.analyze(
            img_path=frame,
            actions=['gender', 'age', 'emotion'],
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False
        )

        for i, face_data in enumerate(all_faces_analysis):
            # Для каждого найденного лица пытаемся его распознать
            try:
                # find() ищет самое похожее лицо в папке FACES_DB_PATH
                recognition_result = DeepFace.find(
                    img_path=face_data['face'],
                    db_path=FACES_DB_PATH,
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=False
                )

                if not recognition_result[0].empty:
                    identity = recognition_result[0].iloc[0]['identity']
                    name = os.path.splitext(os.path.basename(identity))[0]
                    person_data = people_manager.get_person_data(name)
                    results.append({
                        "status": "known",
                        "name": name,
                        "emotion": face_data['dominant_emotion'],
                        "data": person_data
                    })
                    print(f"[Vision] Узнал: {name}")
                else:
                    raise ValueError("Не найдено совпадений")

            except Exception as e:
                # Если лицо не найдено в базе, считаем его незнакомцем
                last_unknown_face_img = face_data['face']  # Сохраняем лицо для возможного знакомства
                # Конвертируем numpy типы в стандартные Python типы для JSON
                age = int(face_data.get('age', 0))
                gender = face_data.get('dominant_gender', 'Unknown')
                emotion = face_data.get('dominant_emotion', 'Unknown')

                results.append({
                    "status": "unknown",
                    "gender": gender,
                    "age": age,
                    "emotion": emotion
                })
                print(f"[Vision] Обнаружен незнакомец (Пол: {gender}, Возраст: ~{age})")

        return results

    except Exception as e:
        print(f"[Vision] В ходе анализа лиц произошла ошибка или лица не найдены: {e}")
        return []


def learn_new_person(name):
    """Сохраняет последнее увиденное лицо незнакомца под новым именем."""
    if last_unknown_face_img is None:
        print("[Vision ERROR] Нет лица для запоминания.")
        return False

    # DeepFace возвращает BGR, а cv2 сохраняет в BGR, так что конвертация не нужна
    face_filename = f"{name}.jpg"
    face_path = os.path.join(FACES_DB_PATH, face_filename)

    # Умножаем на 255, так как DeepFace возвращает нормализованное изображение (0-1)
    face_to_save = (last_unknown_face_img * 255).astype(np.uint8)

    cv2.imwrite(face_path, face_to_save)

    # Добавляем базовую информацию в нашу JSON-базу
    # Анализируем еще раз, чтобы получить данные
    try:
        analysis = DeepFace.analyze(last_unknown_face_img, actions=['gender', 'age'], enforce_detection=False)[0]
        person_info = {
            "gender": analysis.get('dominant_gender'),
            "age_at_first_sight": int(analysis.get('age')),
            "notes": "Познакомились в машине."
        }
        people_manager.add_or_update_person(name, person_info)
        print(f"[Vision] Успешно запомнил '{name}'. Фото сохранено в {face_path}")
        return True
    except Exception as e:
        print(f"[Vision ERROR] Не удалось проанализировать и сохранить данные для '{name}': {e}")
        return False