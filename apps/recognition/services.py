"""
Сервис распознавания лиц
Заглушка для разработки без face_recognition
"""
from typing import List, Tuple, Optional
from django.conf import settings

# Флаг доступности библиотеки face_recognition
FACE_RECOGNITION_AVAILABLE = False

try:
    import numpy as np
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    np = None
    face_recognition = None


class FaceRecognitionService:
    """
    Сервис для распознавания и сравнения лиц
    В режиме разработки без face_recognition возвращает заглушки
    """
    
    def __init__(self):
        self.tolerance = getattr(settings, 'FACE_RECOGNITION_TOLERANCE', 0.6)
        self.model = getattr(settings, 'FACE_ENCODING_MODEL', 'large')
        self.available = FACE_RECOGNITION_AVAILABLE
    
    def get_face_locations(self, image_path: str) -> List[Tuple[int, int, int, int]]:
        """
        Находит все лица на изображении
        Возвращает список координат (top, right, bottom, left)
        """
        if not self.available:
            print("[DEV] face_recognition не установлен, пропускаем распознавание")
            return []
        
        try:
            image = face_recognition.load_image_file(image_path)
            return face_recognition.face_locations(image, model='hog')
        except Exception as e:
            print(f"Ошибка определения лиц: {e}")
            return []
    
    def get_face_encodings(self, image_path: str) -> List:
        """
        Получает кодировки (embeddings) всех лиц на изображении
        128-мерный вектор для каждого лица
        """
        if not self.available:
            print("[DEV] face_recognition не установлен, пропускаем распознавание")
            return []
        
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model='hog')
            encodings = face_recognition.face_encodings(
                image, 
                face_locations,
                model=self.model
            )
            return encodings
        except Exception as e:
            print(f"Ошибка кодирования лиц: {e}")
            return []
    
    def get_face_data(self, image_path: str) -> List[dict]:
        """
        Получает и координаты, и кодировки всех лиц
        """
        if not self.available:
            print("[DEV] face_recognition не установлен, пропускаем распознавание")
            return []
        
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model='hog')
            encodings = face_recognition.face_encodings(
                image, 
                face_locations,
                model=self.model
            )
            
            faces = []
            for location, encoding in zip(face_locations, encodings):
                faces.append({
                    'location': {
                        'top': location[0],
                        'right': location[1],
                        'bottom': location[2],
                        'left': location[3]
                    },
                    'encoding': encoding.tolist()
                })
            return faces
        except Exception as e:
            print(f"Ошибка обработки лиц: {e}")
            return []
    
    def compare_faces(
        self, 
        known_encoding: List[float], 
        unknown_encoding: List[float]
    ) -> Tuple[bool, float]:
        """
        Сравнивает два лица
        Возвращает (совпадение, расстояние)
        """
        if not self.available:
            return False, 0.0
        
        try:
            known = np.array(known_encoding)
            unknown = np.array(unknown_encoding)
            
            distance = face_recognition.face_distance([known], unknown)[0]
            match = distance <= self.tolerance
            confidence = max(0, 1 - distance) * 100
            
            return match, confidence
        except Exception as e:
            print(f"Ошибка сравнения лиц: {e}")
            return False, 0.0
    
    def find_matching_faces(
        self,
        target_encoding: List[float],
        face_encodings: List[Tuple[str, List[float]]]
    ) -> List[Tuple[str, float]]:
        """
        Ищет совпадения целевого лица среди множества лиц
        """
        if not self.available:
            return []
        
        try:
            target = np.array(target_encoding)
            
            matches = []
            for face_id, encoding in face_encodings:
                unknown = np.array(encoding)
                distance = face_recognition.face_distance([target], unknown)[0]
                
                if distance <= self.tolerance:
                    confidence = max(0, 1 - distance) * 100
                    matches.append((face_id, confidence))
            
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches
        except Exception as e:
            print(f"Ошибка поиска лиц: {e}")
            return []


# Singleton instance
face_service = FaceRecognitionService()
