import re

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pydantic import BaseModel

from alu_gauntlet_helper.app_context import APP_CONTEXT
from alu_gauntlet_helper.utils.utils import parse_time


class RaceInfo(BaseModel):
    track: str | None = None
    car: str | None = None
    rank: int | None = None
    time: int | None = None
    time_str: str | None = None

class AttrRange:
    def __init__(self, _min: float, _max: float):
        self.min = _min
        self.max = _max

    def contains(self, value: float) -> bool:
        return self.min <= value <= self.max

    def scale(self, value: float) -> 'AttrRange':
        return AttrRange(self.min * value, self.max * value)

    @staticmethod
    def tolerance(value: float, tolerance: float) -> 'AttrRange':
        return AttrRange(value - tolerance, value + tolerance)

class RectAttrs:
    def __init__(self, area_ratio: AttrRange, aspect_ratio: AttrRange, canny: AttrRange):
        self.area_ratio = area_ratio
        self.aspect_ratio = aspect_ratio
        self.canny = canny

race_box_attrs = RectAttrs(
    AttrRange(0.05, 0.1),
    AttrRange.tolerance(0.5, 0.1),
    AttrRange(50, 150)
)


def find_race_boxes(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    race_boxes = find_rectangles(image, race_box_attrs)
    race_boxes = sorted(race_boxes, key=lambda b: b["x"])

    result = []
    for race_box in race_boxes:
        cropped = crop(image, race_box['x'], race_box['y'], race_box['w'], race_box['h'])
        res = recognize_text_in_rectangle(cropped)
        result.append(parse_race(res))

    return result

car_regex = re.compile(r'[A-Z0-9 -+]{2,}')
rank_regex = re.compile(r'([0-9],)?[0-9]{3}')
time_regex = re.compile(r'[0-9]{2}:[0-9]{2}\.[0-9]{3}')

def parse_race(text: str) -> RaceInfo:
    info = RaceInfo()

    lines = [l for l in text.splitlines() if l and "RACE" not in l]
    print(len(lines), ": ", lines)
    index = len(lines) - 1

    while index >= 0:
        time_match = time_regex.search(lines[index])
        index -= 1
        if time_match:
            info.time_str = time_match.group(0)
            info.time = parse_time(time_match.group(0))
            break

    while index >= 0:
        rank_match = rank_regex.search(lines[index])
        index -= 1
        if rank_match:
            info.rank = int(rank_match.group(0).replace(",", ""))
            break

    while index >= 0:
        cars_autocomplete = APP_CONTEXT.cars_service.autocomplete(lines[index])
        index -= 1
        if cars_autocomplete and len(cars_autocomplete) == 1:
            info.car = cars_autocomplete[0].name
            break

    return info


def find_rectangles(image, attrs: RectAttrs):
    output_image = image.copy()

    # 2. Преобразование в оттенки серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3. Применение детектора краев Canny
    # Canny лучше всего подходит для поиска сильных градиентов (контрастов)
    # на границах, игнорируя при этом плавные градиенты внутри объектов и фона.
    # Значения (50, 150) — это нижний и верхний пороги. Их, возможно, придется настроить.
    edges = cv2.Canny(gray, attrs.canny.min, attrs.canny.max, apertureSize=3)
    #

    # --- Опциональный Шаг: Морфологические операции ---
    # Небольшое закрытие (close) может помочь соединить разрывы в краях,
    # вызванные градиентом или обводкой.
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1) # Расширение
    edges = cv2.erode(edges, kernel, iterations=1)  # Сжатие
    # ---

    # 4. Поиск контуров
    # Ищем внешние контуры на изображении, содержащем только края
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width = image.shape[:2]
    area_range = attrs.area_ratio.scale(height * width)

    rectangles_found = []

    # 5. Обход, фильтрация и аппроксимация
    for contour in contours:
        if not area_range.contains(cv2.contourArea(contour)):
            continue

        perimeter = cv2.arcLength(contour, True)
        # Аппроксимация. Коэффициент 0.04 - типичное начальное значение.
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)

        # Проверка, что контур имеет 4 вершины (прямоугольник)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            if w < 10 or h < 10 or not attrs.aspect_ratio.contains(float(w) / h):
                continue

            cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 3)
            rectangles_found.append({"x": x, "y": y, "w": w, "h": h})
            # print(f"Найден прямоугольник: x={x}, y={y}, w={w}, h={h}")

    cv2.imshow("Canny Edges", edges)
    cv2.imshow("Detected Rectangles", output_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return rectangles_found




def crop(image, x: int, y: int, w: int, h: int):
    return image[y:y + h, x:x + w]

# Укажите путь к исполняемому файлу tesseract.exe,
# если он не находится в PATH вашей системы.
# ЗАМЕНИТЕ ЭТОТ ПУТЬ В СООТВЕТСТВИИ С ВАШЕЙ УСТАНОВКОЙ:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def recognize_text_in_rectangle(image) -> str:
    # 3. Преобразование из BGR (OpenCV) в RGB (требуется для PIL/Tesseract)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # ALLOWED_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:"
    # custom_config = '--oem 3 --psm 6 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:"'

    # 4. Распознавание текста с помощью Tesseract
    # Tesseract лучше работает с объектами PIL.Image
    text = pytesseract.image_to_string(
        Image.fromarray(image),
        lang='eng', # Используйте языки, которые могут встречаться
        # config=custom_config
    )

    # Очистка текста от лишних символов (переносов строк и пробелов)
    return text.strip()
