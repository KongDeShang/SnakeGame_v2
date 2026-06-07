"""
MediaPipe 兼容性补丁

新版 mediapipe (0.10.x) 移除了 mp.solutions 模块，
而 cvzone 依赖旧的 mp.solutions.hands API。
此模块在 mediapipe 上添加向后兼容层。
"""

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import types
import os


# ============ 尝试导入新版 drawing_utils，没有则自己实现 ============

try:
    from mediapipe.tasks.python.vision import drawing_utils as _mp_drawing
    _HAS_DRAWING_UTILS = True
except ImportError:
    _HAS_DRAWING_UTILS = False


def _draw_landmarks(image, landmark_list, connections, **kwargs):
    """
    在图像上绘制手部关键点和连接线。
    同时兼容新版 mediapipe 的 drawing_utils 和自实现版本。
    """
    if _HAS_DRAWING_UTILS:
        _mp_drawing.draw_landmarks(image, landmark_list, connections, **kwargs)
        return

    # 自实现：用 cv2 绘制关键点和连接线
    import cv2
    h, w, _ = image.shape
    # 画连接线
    for start_idx, end_idx in connections:
        if (start_idx < len(landmark_list) and end_idx < len(landmark_list)):
            lm_start = landmark_list[start_idx]
            lm_end = landmark_list[end_idx]
            x1, y1 = int(lm_start.x * w), int(lm_start.y * h)
            x2, y2 = int(lm_end.x * w), int(lm_end.y * h)
            cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # 画关键点
    for lm in landmark_list:
        cx, cy = int(lm.x * w), int(lm.y * h)
        cv2.circle(image, (cx, cy), 4, (255, 0, 0), cv2.FILLED)


class DrawingSpec:
    """模拟旧版 drawing_utils.DrawingSpec"""
    def __init__(self, color=(0, 0, 0), thickness=1, circle_radius=1):
        self.color = color
        self.thickness = thickness
        self.circle_radius = circle_radius


# ============ 兼容性结果类 ============

class NormalizedLandmark:
    """模拟旧版 mp.solutions 的 NormalizedLandmark"""
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class NormalizedLandmarkList:
    """模拟旧版的 NormalizedLandmarkList"""
    def __init__(self, landmarks):
        self._landmarks = landmarks

    @property
    def landmark(self):
        return self._landmarks

    def __len__(self):
        return len(self._landmarks)

    def __getitem__(self, idx):
        return self._landmarks[idx]


class Classification:
    """模拟旧版的 Classification"""
    def __init__(self, index=0, score=0.0, label=""):
        self.index = index
        self.score = score
        self.label = label


class ClassificationList:
    """模拟旧版的 ClassificationList"""
    def __init__(self, classifications):
        self.classification = classifications

    @property
    def classifications(self):
        return self.classification


class HandsResult:
    """模拟旧版 mp.solutions.hands 的 process() 返回结果"""
    def __init__(self, hand_landmarks_list=None, handedness_list=None):
        self.multi_hand_landmarks = hand_landmarks_list or []
        self.multi_handedness = handedness_list or []


# ============ HandLandmarker 封装 ============

# HAND_CONNECTIONS - 手部连接定义 (与旧版兼容)
HAND_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 4),          # 拇指
    (0, 5), (5, 6), (6, 7), (7, 8),          # 食指
    (0, 9), (9, 10), (10, 11), (11, 12),     # 中指
    (0, 13), (13, 14), (14, 15), (15, 16),   # 无名指
    (0, 17), (17, 18), (18, 19), (19, 20),   # 小指
    (5, 9), (9, 13), (13, 17)                # 掌骨
])


class Hands:
    """
    模拟旧版 mp.solutions.hands.Hands 类
    内部使用新版 HandLandmarker API
    """

    def __init__(self, static_image_mode=False, max_num_hands=2,
                 model_complexity=1, min_detection_confidence=0.5,
                 min_tracking_confidence=0.5):
        self.static_image_mode = static_image_mode
        self.max_num_hands = max_num_hands
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        running_mode = vision.RunningMode.IMAGE

        # 查找 hand_landmarker.task 模型文件
        model_path = self._find_model_file()

        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=running_mode,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self._detector = vision.HandLandmarker.create_from_options(options)

    @staticmethod
    def _find_model_file():
        """查找 hand_landmarker.task 模型文件"""
        # 1. 优先查找项目目录（与 mediapipe_compat.py 同目录）
        compat_dir = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(compat_dir, "hand_landmarker.task")
        if os.path.exists(local_path):
            return local_path

        # 2. 查找当前工作目录
        cwd_path = os.path.join(os.getcwd(), "hand_landmarker.task")
        if os.path.exists(cwd_path):
            return cwd_path

        # 3. 查找 mediapipe 包目录
        mp_dir = os.path.dirname(mp.__file__)
        for root, dirs, files in os.walk(mp_dir):
            for f in files:
                if f.endswith('.task') and 'hand' in f.lower():
                    return os.path.join(root, f)

        # 4. 如果找不到，给出明确提示
        raise FileNotFoundError(
            "找不到 hand_landmarker.task 模型文件。\n"
            f"请从以下地址下载并放在 {compat_dir} 目录：\n"
            "https://storage.googleapis.com/mediapipe-models/"
            "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
        )

    def process(self, image_rgb):
        """
        处理 RGB 图像，返回兼容旧版 API 的结果

        Args:
            image_rgb: RGB 格式的 numpy 数组

        Returns:
            HandsResult 对象 (兼容 old api)
        """
        if image_rgb is None:
            return HandsResult()

        # 创建 mp.Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        try:
            result = self._detector.detect(mp_image)
        except Exception:
            return HandsResult()

        if not result.hand_landmarks:
            return HandsResult()

        # 转换 landmarks
        hand_landmarks_list = []
        handedness_list = []

        for idx, landmarks in enumerate(result.hand_landmarks):
            # 转换 landmarks
            landmark_list = []
            for lm in landmarks:
                landmark_list.append(NormalizedLandmark(
                    x=lm.x, y=lm.y, z=lm.z
                ))
            hand_landmarks_list.append(NormalizedLandmarkList(landmark_list))

            # 转换 handedness
            if idx < len(result.handedness):
                h = result.handedness[idx]
                cls_list = []
                for cat in h:
                    cls_list.append(Classification(
                        index=cat.index,
                        score=cat.score,
                        label=cat.category_name
                    ))
                handedness_list.append(ClassificationList(cls_list))
            else:
                handedness_list.append(ClassificationList([
                    Classification(index=0, score=0.0, label="Unknown")
                ]))

        return HandsResult(
            hand_landmarks_list=hand_landmarks_list,
            handedness_list=handedness_list
        )

    def close(self):
        """释放资源"""
        if hasattr(self, '_detector'):
            self._detector.close()


# ============ 打补丁到 mediapipe ============

def _apply_patch():
    """将旧版 solutions API 添加到 mediapipe 模块"""

    # 创建 solutions 模块
    if not hasattr(mp, 'solutions'):
        solutions_module = types.ModuleType('mediapipe.solutions')
        solutions_module.__package__ = 'mediapipe.solutions'
        solutions_module.__path__ = []
        solutions_module.__file__ = __file__

        # 创建 hands 子模块
        hands_module = types.ModuleType('mediapipe.solutions.hands')
        hands_module.Hands = Hands
        hands_module.HAND_CONNECTIONS = HAND_CONNECTIONS
        hands_module.__package__ = 'mediapipe.solutions.hands'

        # drawing_utils - 兼容新版或自实现版本
        drawing_utils_module = types.ModuleType('mediapipe.solutions.drawing_utils')
        drawing_utils_module.draw_landmarks = _draw_landmarks
        drawing_utils_module.DrawingSpec = DrawingSpec

        solutions_module.hands = hands_module
        solutions_module.drawing_utils = drawing_utils_module
        mp.solutions = solutions_module

        # 同时也添加到 sys.modules 以便其他模块直接导入
        import sys
        sys.modules['mediapipe.solutions'] = solutions_module
        sys.modules['mediapipe.solutions.hands'] = hands_module
        sys.modules['mediapipe.solutions.drawing_utils'] = drawing_utils_module


# 自动应用补丁
_apply_patch()
