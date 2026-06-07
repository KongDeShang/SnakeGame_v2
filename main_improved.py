# ──────────────────────────────────────────────
#  🐍 Neon Snake Game — Hand Gesture Control
#  Author: KongDeShang
#  GitHub: https://github.com/KongDeShang/SnakeGame_v2
#  License: Custom — Non-commercial + Attribution required
#  ── 个人/学习使用免费 · 禁止商用 · 转载须署名 ──
# ──────────────────────────────────────────────

"""
SnakeGame v2 — 改进版 (Enhanced)
==================================
基于摄像头手势控制的霓虹贪吃蛇游戏。

v3 改进要点:
  - 🐛 修复 _smooth_gesture 死判断 bug
  - ⚡ 性能优化: 手势检测隔帧执行 + 渲染预分配
  - ✨ 奖励食物: 金色特殊食物, 3秒限时, 3分值
  - 🔊 音效反馈: 吃食物/奖励/死亡 简单音效 (winsound, 零依赖)
  - ⏱ 开始画面: 伸出食指才开始, 不再自动倒计时
  - 📊 高级统计: 游戏结束显示时长/蛇长/食物数
  - 🧩 数据结构: Particle/Popup 用 dataclass 重构
  - 📝 完整类型注解 + 方法拆分

v4 改进要点:
  - 🎨 颜色主题系统: 每5分进阶, 蛇身/UI/网格/粒子全换色
  - ✨ 蛇身炫酷升级: 流光脉冲 + 随主题变色 + 幻彩外发光
  - 💎 蛇体粒子尾迹
  - 🎮 开始画面: 伸出食指开始, 不再自动倒计时
  - ✊ 死亡后握拳→张开手掌重新开始
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# 兼容新版 mediapipe 的补丁（必须在 cvzone 之前导入）
import mediapipe_compat  # noqa: F401

import cv2
import cvzone
import numpy as np
from cvzone.HandTrackingModule import HandDetector

# ── 音效系统 ──
try:
    import pygame
    import pygame.sndarray
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False
    print("[Audio] pygame 未安装，音效已禁用。 pip install pygame")


# ──────────────────────────────────────────────
#  游戏状态 & 配置
# ──────────────────────────────────────────────

class GameState(Enum):
    """游戏状态枚举。"""
    COUNTDOWN = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3


class GameConfig:
    """游戏配置常量 —— 修改参数前请确认含义。"""

    # ── 蛇 ──
    SNAKE_HEAD_RADIUS: int = 30
    SNAKE_BODY_WIDTH_OUTER: int = 42
    SNAKE_BODY_WIDTH_MAIN: int = 18
    SNAKE_BODY_WIDTH_INNER: int = 5
    INITIAL_LENGTH: int = 150
    LENGTH_INCREMENT: int = 50
    MAX_LENGTH: int = 800
    SAFE_COLLISION_RADIUS: int = 60
    SELF_COLLISION_IMMUNE_DIST: int = 400      # 自碰免疫距离(px)：蛇头后 N px 内的身体不参与碰撞
    SELF_COLLISION_GRACE_FRAMES: int = 10      # 自碰容忍帧数：连续 N 帧检测到碰撞才判死亡

    # ── 边界 ──
    BOUNDARY_MARGIN: int = 40

    # ── 渲染 ──
    GRID_SPACING: int = 80
    GRID_COLOR: tuple[int, int, int] = (80, 30, 110)
    BACKGROUND_ALPHA: float = 0.45
    GRID_ALPHA: float = 0.55

    # ── 食物 ──
    FOOD_PULSE_RING_BASE: int = 9

    # ── 奖励食物 ──
    BONUS_ENABLED: bool = True
    BONUS_COOLDOWN: int = 600           # 帧数间隔 (约10秒 @60fps)
    BONUS_DURATION: int = 180           # 持续帧数 (约3 秒)
    BONUS_SCORE: int = 3
    BONUS_COLOR: tuple[int, int, int] = (255, 215, 0)   # 金色

    # ── 粒子 ──
    PARTICLE_COUNT: int = 20
    PARTICLE_PALETTE: list[tuple[int, int, int]] = [
        (0, 255, 200), (0, 200, 255), (200, 255, 50),
        (255, 160, 0), (255, 50, 220),
    ]
    BONUS_PARTICLE_COUNT: int = 40
    BONUS_PARTICLE_COLORS: list[tuple[int, int, int]] = [
        (255, 215, 0), (255, 255, 0), (255, 200, 50),
    ]

    # ── 闪光 ──
    EAT_FLASH_DURATION: int = 12
    EAT_FLASH_ALPHA: float = 0.28

    # ── 弹出文本 ──
    POPUP_LIFE: int = 55

    # ── 手势 ──
    GESTURE_SMOOTH_WINDOW: int = 12

    # ── 难度 ──
    SPEED_INCREASE_INTERVAL: int = 5
    SPEED_MULTIPLIER_INCREMENT: float = 0.1
    MIN_FRAME_SKIP: int = 1

    # ── 文件 ──
    HIGH_SCORE_FILE: str = 'high_score.json'

    # ── 主题进阶 ──
    THEME_INTERVAL: int = 5          # 每5分换一次主题
    SNAKE_TRAIL_PARTICLES: bool = True   # 蛇身粒子尾迹
    SNAKE_TRAIL_INTERVAL: int = 3        # 尾迹粒子生成间隔帧

    # ── V3 蛇身渲染 ──
    SNAKE_COLOR_BANDS: int = 10       # 色带数：平衡梯度精度与 draw call 数量

    # ── V3 CRT 扫描线 ──
    CRT_ENABLED: bool = True          # 启用 CRT 扫描线滤镜
    CRT_ALPHA: float = 0.25           # 扫描线透明度 (0~1)


# ──────────────────────────────────────────────
#  音效控制器
# ──────────────────────────────────────────────

class AudioController:
    """基于 pygame.mixer 的非阻塞音效控制器。

    支持波形生成与 wav 文件加载，所有 play_* 方法非阻塞。
    初始化失败时静默降级为无音效模式。
    """

    def __init__(self, sound_dir: str | None = None) -> None:
        self._initialized: bool = False
        self._sounds: dict[str, Any] = {}  # pygame.mixer.Sound | Any — 类型注解兼容无 pygame 环境
        self._init_mixer(sound_dir)

    # ── 初始化 ────────────────────────────────────

    def _init_mixer(self, sound_dir: str | None) -> None:
        """初始化 pygame.mixer 并加载/生成音效。"""
        if not _HAS_PYGAME:
            return
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self._initialized = True
        except Exception as e:
            print(f"[Audio] mixer 初始化失败（游戏将继续，无音效）: {e}")
            return

        if sound_dir:
            self._load_from_dir(sound_dir)
        if not self._sounds:
            self._generate_default_sounds()

    def _load_from_dir(self, path: str) -> None:
        """从目录加载 .wav 文件。文件名: eat.wav / bonus.wav / die_wall.wav / die_self.wav"""
        for name in ('eat', 'bonus', 'die_wall', 'die_self'):
            fpath = os.path.join(path, f'{name}.wav')
            if os.path.exists(fpath):
                try:
                    self._sounds[name] = pygame.mixer.Sound(fpath)
                except Exception:
                    pass

    # ── 波形生成 ──────────────────────────────────

    def _make_sound(self, freq: float, duration_ms: int,
                    wave_type: str = 'sine', volume: float = 0.3) -> pygame.mixer.Sound:
        """生成指定频率/时长的波形 Sound 对象。"""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n, endpoint=False)

        if wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave_type == 'sawtooth':
            wave = 2 * (freq * t - np.floor(freq * t + 0.5))
        else:  # sine
            wave = np.sin(2 * np.pi * freq * t)

        # 包络：避免爆音
        fade = np.linspace(1, 0, n) ** 2
        wave = wave * fade
        pcm = np.column_stack((
            (wave * volume * 32767 * 0.5).astype(np.int16),
            (wave * volume * 32767 * 0.5).astype(np.int16),
        ))  # 立体声双声道
        return pygame.sndarray.make_sound(pcm)

    def _generate_default_sounds(self) -> None:
        """生成默认音效集。"""
        self._sounds['eat'] = self._make_sound(880, 80, 'sine', 0.30)
        self._sounds['bonus'] = self._make_sound(1200, 120, 'sine', 0.35)
        self._sounds['die_wall'] = self._make_sound(300, 200, 'square', 0.20)
        self._sounds['die_self'] = self._make_sound(200, 300, 'square', 0.20)

    # ── 播放接口 ──────────────────────────────────

    def play_eat(self) -> None:
        if self._initialized and 'eat' in self._sounds:
            self._sounds['eat'].play()

    def play_bonus(self) -> None:
        if self._initialized and 'bonus' in self._sounds:
            self._sounds['bonus'].play()

    def play_die_wall(self) -> None:
        if self._initialized and 'die_wall' in self._sounds:
            self._sounds['die_wall'].play()

    def play_die_self(self) -> None:
        if self._initialized and 'die_self' in self._sounds:
            self._sounds['die_self'].play()

    def close(self) -> None:
        """释放 mixer 资源。"""
        if self._initialized:
            try:
                pygame.mixer.quit()
            except Exception:
                pass


# ──────────────────────────────────────────────
#  颜色主题系统
#  ─ score 每升 5 分进阶一级, 共 6 级
# ──────────────────────────────────────────────

@dataclass
class ColorTheme:
    """一个完整的视觉主题配色。"""
    name: str
    # 蛇身渐变 (BGR)
    body_start: tuple[int, int, int]
    body_end: tuple[int, int, int]
    # 蛇头
    head_base: tuple[int, int, int]
    head_eye_bg: tuple[int, int, int]
    # UI
    ui_score: tuple[int, int, int]
    ui_level: tuple[int, int, int]
    # 边框脉冲
    border_a: tuple[int, int, int]
    border_b: tuple[int, int, int]
    # 网格
    grid: tuple[int, int, int]
    # 食物光圈
    food_ring: tuple[int, int, int]
    # 吃食物闪光
    flash_color: tuple[int, int, int]
    # pause / game-over 脉冲色
    pause_base: tuple[int, int, int]
    gameover_base: tuple[int, int, int]
    # 粒子调色板 (body sparkles)
    sparkle_palette: list[tuple[int, int, int]]


THEMES: list[ColorTheme] = [
    ColorTheme(
        name='NEON',
        body_start=(40, 15, 70),     # 深紫
        body_end=(200, 255, 0),      # 青
        head_base=(40, 15, 70),
        head_eye_bg=(255, 230, 0),
        ui_score=(0, 255, 200),
        ui_level=(255, 180, 0),
        border_a=(100, 180, 0),
        border_b=(255, 255, 0),
        grid=(80, 30, 110),
        food_ring=(0, 255, 160),
        flash_color=(0, 255, 160),
        pause_base=(200, 200, 60),
        gameover_base=(60, 60, 200),
        sparkle_palette=[(0, 255, 200), (0, 200, 255), (200, 255, 50)],
    ),
    ColorTheme(
        name='INFERNO',
        body_start=(20, 20, 120),    # 暗红
        body_end=(50, 180, 255),     # 亮橙
        head_base=(20, 20, 100),
        head_eye_bg=(255, 200, 50),
        ui_score=(50, 200, 255),
        ui_level=(0, 140, 255),
        border_a=(0, 100, 200),
        border_b=(50, 255, 255),
        grid=(40, 20, 80),
        food_ring=(50, 200, 255),
        flash_color=(50, 200, 255),
        pause_base=(255, 180, 80),
        gameover_base=(50, 50, 200),
        sparkle_palette=[(50, 200, 255), (0, 140, 255), (100, 255, 255)],
    ),
    ColorTheme(
        name='ELECTRIC',
        body_start=(60, 20, 20),     # 深蓝
        body_end=(255, 200, 0),      # 亮蓝
        head_base=(60, 20, 20),
        head_eye_bg=(255, 255, 100),
        ui_score=(255, 200, 0),
        ui_level=(255, 255, 100),
        border_a=(200, 100, 0),
        border_b=(255, 255, 100),
        grid=(60, 30, 20),
        food_ring=(255, 200, 0),
        flash_color=(255, 200, 0),
        pause_base=(200, 200, 100),
        gameover_base=(60, 60, 200),
        sparkle_palette=[(255, 200, 0), (255, 255, 100), (200, 255, 200)],
    ),
    ColorTheme(
        name='SOLAR',
        body_start=(20, 40, 80),     # 深琥珀
        body_end=(20, 255, 255),     # 金色
        head_base=(20, 40, 80),
        head_eye_bg=(255, 255, 200),
        ui_score=(20, 255, 255),
        ui_level=(0, 215, 255),
        border_a=(0, 150, 200),
        border_b=(20, 255, 255),
        grid=(30, 30, 60),
        food_ring=(20, 255, 240),
        flash_color=(20, 255, 255),
        pause_base=(255, 215, 100),
        gameover_base=(60, 60, 200),
        sparkle_palette=[(20, 255, 255), (0, 215, 255), (200, 255, 200)],
    ),
    ColorTheme(
        name='AURORA',
        body_start=(80, 10, 60),     # 深紫罗兰
        body_end=(220, 255, 100),    # 青绿
        head_base=(80, 10, 60),
        head_eye_bg=(255, 200, 200),
        ui_score=(220, 255, 100),
        ui_level=(200, 100, 200),
        border_a=(180, 80, 150),
        border_b=(220, 255, 100),
        grid=(60, 20, 60),
        food_ring=(180, 255, 150),
        flash_color=(180, 255, 150),
        pause_base=(220, 180, 180),
        gameover_base=(80, 60, 200),
        sparkle_palette=[(220, 255, 100), (200, 100, 200), (180, 255, 150)],
    ),
    ColorTheme(
        name='PRISM',
        body_start=(180, 60, 180),   # 紫
        body_end=(60, 180, 255),     # 橙 → 每帧还追加彩虹偏移
        head_base=(180, 60, 180),
        head_eye_bg=(255, 255, 255),
        ui_score=(255, 200, 100),
        ui_level=(200, 100, 255),
        border_a=(255, 100, 100),
        border_b=(100, 255, 255),
        grid=(100, 30, 80),
        food_ring=(255, 200, 100),
        flash_color=(255, 200, 100),
        pause_base=(255, 200, 200),
        gameover_base=(100, 60, 200),
        sparkle_palette=[(255, 200, 100), (200, 100, 255), (100, 255, 200),
                         (255, 100, 200), (200, 255, 100)],
    ),
]


def get_theme(score: int) -> ColorTheme:
    """根据分数返回对应的颜色主题。"""
    idx = min(score // GameConfig.THEME_INTERVAL, len(THEMES) - 1)
    return THEMES[idx]


# ──────────────────────────────────────────────
#  数据结构
# ──────────────────────────────────────────────

@dataclass
class Particle:
    """单个粒子。"""
    x: float
    y: float
    vx: float
    vy: float
    life: int
    max_life: int
    size: int
    color: tuple[int, int, int]


@dataclass
class Popup:
    """浮动 "+N" 文字。"""
    x: int
    y: int
    life: int
    max_life: int
    text: str = '+1'
    color: tuple[int, int, int] = (0, 255, 200)


@dataclass
class BonusFood:
    """奖励食物状态。"""
    active: bool = False
    pos: tuple[int, int] = (0, 0)
    timer: int = 0                     # 剩余帧数
    cooldown: int = 0                  # 冷却帧数


@dataclass
class GameStats:
    """单局游戏统计。"""
    start_time: float = 0.0
    foods_eaten: int = 0
    max_snake_length: float = 0.0
    highest_level: int = 0
    total_distance: float = 0.0


# ──────────────────────────────────────────────
#  自定义异常
# ──────────────────────────────────────────────

class SnakeGameError(Exception):
    """游戏基类异常。"""


class FoodImageError(SnakeGameError):
    """食物图片相关错误。"""


class CameraError(SnakeGameError):
    """摄像头相关错误。"""


# ──────────────────────────────────────────────
#  游戏主类
# ──────────────────────────────────────────────

class SnakeGameClass:
    """贪吃蛇游戏核心类。"""

    def __init__(self, path_food: str, frame_w: int, frame_h: int,
                 audio: AudioController | None = None) -> None:
        # ── 加载食物图片 ──
        if not os.path.exists(path_food):
            raise FoodImageError(f"食物图片文件不存在: {path_food}")
        self.img_food: np.ndarray = cv2.imread(path_food, cv2.IMREAD_UNCHANGED)
        if self.img_food is None:
            raise FoodImageError(f"无法读取食物图片: {path_food}")
        self.h_food: int
        self.w_food: int
        self.h_food, self.w_food, _ = self.img_food.shape

        self.frame_w: int = frame_w
        self.frame_h: int = frame_h
        self.frame_count: int = 0

        # ── 预计算资源 ──
        self._grid: np.ndarray = self._make_grid(frame_w, frame_h)
        self._overlay_mask_full: np.ndarray = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)
        cv2.rectangle(self._overlay_mask_full, (0, 0), (frame_w, frame_h),
                      (255, 255, 255), -1)  # 用白色填充

        # ── 手势 ──
        self.gesture_smooth_queue: deque[tuple[int, int]] = deque(
            maxlen=GameConfig.GESTURE_SMOOTH_WINDOW
        )
        self._last_hand_position: tuple[int, int] = (frame_w // 2, frame_h // 2)

        # ── FPS ──
        self._fps_time: float = time.time()
        self._fps_frame_count: int = 0
        self.current_fps: float = 0.0

        # ── 音效 ──
        self.audio: AudioController = audio or AudioController()

        # ── 游戏状态 ──
        self.state: GameState = GameState.COUNTDOWN
        self.high_score: int = self._load_high_score()

        # ── 游戏运行时数据（由 _reset 填充） ──
        self.points: list[tuple[int, int]] = []
        self.lengths: list[float] = []
        self.current_length: float = 0.0
        self.allowed_length: float = 0.0
        self.previous_head: tuple[int, int] = (0, 0)
        self.score: int = 0
        self.eat_flash: int = 0
        self.particles: list[Particle] = []
        self.popups: list[Popup] = []
        self.food_point: tuple[int, int] = (0, 0)
        self.bonus: BonusFood = BonusFood()
        self.stats: GameStats = GameStats()
        self.frame_skip_counter: int = 0
        self._collision_grace_counter: int = 0   # 自碰容忍帧计数器

        # ── 颜色主题 ──
        self.current_theme: ColorTheme = get_theme(0)
        self.trail_particle_counter: int = 0

        self._reset()

    # ──────── 内部工具 ────────

    @staticmethod
    def _make_grid(w: int, h: int, color: tuple[int, int, int] | None = None,
                   spacing: int | None = None) -> np.ndarray:
        """预计算静态霓虹网格覆盖层."""
        if spacing is None:
            spacing = GameConfig.GRID_SPACING
        if color is None:
            color = GameConfig.GRID_COLOR
        grid = np.zeros((h, w, 3), dtype=np.uint8)
        for x in range(0, w, spacing):
            cv2.line(grid, (x, 0), (x, h), color, 1)
        for y in range(0, h, spacing):
            cv2.line(grid, (0, y), (w, y), color, 1)
        return grid

    def _rebuild_grid(self, color: tuple[int, int, int]) -> None:
        """用新颜色重建网格。"""
        self._grid = self._make_grid(self.frame_w, self.frame_h, color)

    def _update_theme(self) -> None:
        """根据当前分数刷新颜色主题及网格。"""
        new_theme = get_theme(self.score)
        if new_theme.name != self.current_theme.name:
            self.current_theme = new_theme
            self._rebuild_grid(new_theme.grid)

    def _reset(self) -> None:
        """重置游戏状态（开始新对局）。"""
        self.points.clear()
        self.lengths.clear()
        self.current_length = 0.0
        self.allowed_length = float(GameConfig.INITIAL_LENGTH)
        self.previous_head = (self.frame_w // 2, self.frame_h // 2)
        self._last_hand_position = self.previous_head
        self.score = 0
        self.eat_flash = 0
        self.particles.clear()
        self.popups.clear()
        self.food_point = self._new_food_location()
        self.bonus = BonusFood()
        self.stats = GameStats(start_time=time.time())
        self.frame_skip_counter = 0
        self.gesture_smooth_queue.clear()
        self.state = GameState.COUNTDOWN
        self.current_theme = get_theme(0)
        self.trail_particle_counter = 0
        self._collision_grace_counter = 0

    # ──────── 存档 ────────

    @staticmethod
    def _script_dir() -> str:
        """返回当前脚本所在目录."""
        return os.path.dirname(os.path.abspath(__file__))

    def _load_high_score(self) -> int:
        """加载最高分."""
        try:
            score_path = os.path.join(self._script_dir(), GameConfig.HIGH_SCORE_FILE)
            if os.path.exists(score_path):
                with open(score_path, 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except Exception as e:
            print(f"加载最高分失败: {e}")
        return 0

    def _save_high_score(self) -> None:
        """保存最高分."""
        try:
            score_path = os.path.join(self._script_dir(), GameConfig.HIGH_SCORE_FILE)
            with open(score_path, 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except Exception as e:
            print(f"保存最高分失败: {e}")

    def _check_and_save_high_score(self) -> None:
        """如果当前分数超过最高分则持久化."""
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

    # ──────── 食物 ────────

    def _new_food_location(self) -> tuple[int, int]:
        """生成不会与蛇身重叠的食物坐标。"""
        mx, my = self.w_food // 2, self.h_food // 2
        margin = GameConfig.BOUNDARY_MARGIN + self.w_food // 2
        x_lo, x_hi = margin + mx, self.frame_w - margin - mx - 1
        y_lo, y_hi = margin + my, self.frame_h - margin - my - 1

        if x_lo >= x_hi or y_lo >= y_hi:
            # 极端小画面回退
            return (self.frame_w // 2, self.frame_h // 2)

        for _ in range(100):
            pos = (random.randint(x_lo, x_hi), random.randint(y_lo, y_hi))
            if not self._is_food_on_snake(pos):
                return pos
        return (random.randint(x_lo, x_hi), random.randint(y_lo, y_hi))

    def _is_food_on_snake(self, food_pos: tuple[int, int]) -> bool:
        """检查坐标是否与蛇身重叠。"""
        fx, fy = food_pos
        radius = self.w_food // 2 + 20
        r2 = radius * radius
        for px, py in self.points:
            dx, dy = fx - px, fy - py
            if dx * dx + dy * dy < r2:
                return True
        return False

    def _try_spawn_bonus(self) -> None:
        """尝试生成奖励食物（冷却到期且不在蛇身上）。"""
        if not GameConfig.BONUS_ENABLED:
            return
        if self.bonus.active or self.bonus.cooldown > 0:
            return
        pos = self._new_food_location()
        self.bonus.active = True
        self.bonus.pos = pos
        self.bonus.timer = GameConfig.BONUS_DURATION

    def _eat_bonus(self) -> None:
        """吃到奖励食物。"""
        fx, fy = self.bonus.pos
        self._spawn_particles(fx, fy, count=GameConfig.BONUS_PARTICLE_COUNT,
                              palette=GameConfig.BONUS_PARTICLE_COLORS)
        self.popups.append(Popup(
            x=fx, y=fy, life=GameConfig.POPUP_LIFE,
            max_life=GameConfig.POPUP_LIFE,
            text=f'+{GameConfig.BONUS_SCORE}', color=(255, 215, 0),
        ))
        self.score += GameConfig.BONUS_SCORE
        self.allowed_length = min(
            self.allowed_length + GameConfig.LENGTH_INCREMENT,
            GameConfig.MAX_LENGTH
        )
        self.audio.play_bonus()
        self.bonus.active = False
        self.bonus.cooldown = GameConfig.BONUS_COOLDOWN

    # ──────── 粒子 & 弹窗 ────────

    def _spawn_particles(self, x: int, y: int, count: Optional[int] = None,
                         palette: Optional[list[tuple[int, int, int]]] = None) -> None:
        """生成粒子爆炸效果。"""
        if count is None:
            count = GameConfig.PARTICLE_COUNT
        if palette is None:
            palette = GameConfig.PARTICLE_PALETTE

        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 12)
            life = random.randint(20, 48)
            self.particles.append(Particle(
                x=float(x), y=float(y),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=life, max_life=life,
                size=random.randint(3, 9),
                color=random.choice(palette),
            ))

    def _draw_particles(self, img: np.ndarray) -> None:
        """更新并绘制所有粒子。"""
        alive: list[Particle] = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vx *= 0.91
            p.vy *= 0.91
            p.life -= 1
            if p.life > 0:
                a = p.life / p.max_life
                size = max(1, int(p.size * a))
                col = tuple(int(c * a) for c in p.color)
                ix, iy = int(p.x), int(p.y)
                if 0 <= ix < self.frame_w and 0 <= iy < self.frame_h:
                    cv2.circle(img, (ix, iy), size, col, -1, cv2.LINE_AA)
                alive.append(p)
        self.particles = alive

    def _draw_popups(self, img: np.ndarray) -> None:
        """绘制浮动分数文字。"""
        alive: list[Popup] = []
        for popup in self.popups:
            popup.life -= 1
            if popup.life > 0:
                a = popup.life / popup.max_life
                elapsed = popup.max_life - popup.life
                col = tuple(int(c * a) for c in popup.color)
                px = max(0, min(popup.x - 20, self.frame_w - 80))
                py = max(30, popup.y - int(elapsed * 2.0))
                self._neon_text(img, popup.text, (px, py), 1.8, col, 2)
                alive.append(popup)
        self.popups = alive

    # ──────── 渲染工具 ────────

    @staticmethod
    def _neon_text(img: np.ndarray, text: str, pos: tuple[int, int],
                   scale: float, color: tuple[int, int, int],
                   thickness: int = 2) -> None:
        """三层发光霓虹文字。"""
        dark = tuple(c // 5 for c in color)
        mid = tuple(c // 2 for c in color)
        for w, col in [
            (thickness + 10, dark),
            (thickness + 5, mid),
            (thickness, color),
        ]:
            cv2.putText(img, text, pos, cv2.FONT_HERSHEY_DUPLEX,
                        scale, col, w, cv2.LINE_AA)

    @staticmethod
    def _dark_overlay(img: np.ndarray, alpha: float = 0.6) -> np.ndarray:
        """在图像上叠加深色半透明层。"""
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (img.shape[1], img.shape[0]), (0, 0, 0), -1)
        return cv2.addWeighted(img, 1 - alpha, overlay, alpha, 0)

    def _get_speed_multiplier(self) -> float:
        """基于分数计算速度倍率。"""
        return 1.0 + (self.score // GameConfig.SPEED_INCREASE_INTERVAL) * \
               GameConfig.SPEED_MULTIPLIER_INCREMENT

    def _smooth_gesture(self, new_point: tuple[int, int]) -> tuple[int, int]:
        """移动平均平滑手势坐标。"""
        self.gesture_smooth_queue.append(new_point)
        total_x = 0
        total_y = 0
        for p in self.gesture_smooth_queue:
            total_x += p[0]
            total_y += p[1]
        n = len(self.gesture_smooth_queue)
        return (total_x // n, total_y // n)

    def _update_fps(self) -> None:
        """每秒更新一次 FPS 计数。"""
        self._fps_frame_count += 1
        now = time.time()
        elapsed = now - self._fps_time
        if elapsed >= 1.0:
            self.current_fps = self._fps_frame_count / elapsed
            self._fps_frame_count = 0
            self._fps_time = now

    # ──────── 渲染方法 ────────

    def _draw_background(self, img: np.ndarray) -> np.ndarray:
        """变暗摄像头画面并叠加霓虹网格。"""
        img = cv2.convertScaleAbs(img, alpha=GameConfig.BACKGROUND_ALPHA, beta=0)
        return cv2.addWeighted(img, 1.0, self._grid, GameConfig.GRID_ALPHA, 0)

    def _draw_snake_body(self, img: np.ndarray) -> None:
        """绘制蛇身: 使用 cv2.polylines 批量绘制，大幅减少 draw calls。"""
        n = len(self.points)
        if n < 2:
            return

        theme = self.current_theme
        bw_out = GameConfig.SNAKE_BODY_WIDTH_OUTER
        bw_main = GameConfig.SNAKE_BODY_WIDTH_MAIN
        bw_inner = GameConfig.SNAKE_BODY_WIDTH_INNER
        num_bands = GameConfig.SNAKE_COLOR_BANDS
        denom = max(n - 1, 1)

        pulse_pos = (self.frame_count * 0.015) % 1.0
        sR, sG, sB = theme.body_start
        eR, eG, eB = theme.body_end
        is_prism = theme.name == 'PRISM'

        # ── 将 points 转为 numpy 数组 ──
        pts_arr = np.array(self.points, dtype=np.int32)

        # ── 按色带分组，每组调用一次 polylines ──
        # 原始代码: n*3 次 cv2.line → 现在: num_bands*3 次 cv2.polylines
        for b in range(num_bands):
            start_i = b * (n - 1) // num_bands
            end_i = (b + 1) * (n - 1) // num_bands + 1
            if end_i - start_i < 2:
                end_i = start_i + 2
            if end_i > n:
                break

            # overlap 前一组的最后一个点，防止接缝可见断裂
            seg = pts_arr[max(0, start_i - 1):end_i].reshape((-1, 1, 2))
            t_mid = (start_i + (end_i - start_i) / 2) / denom

            # ── 渐变色 ──
            color = (
                int(sR + (eR - sR) * t_mid),
                int(sG + (eG - sG) * t_mid),
                int(sB + (eB - sB) * t_mid),
            )

            if is_prism:
                hue = (t_mid + self.frame_count * 0.008) % 1.0
                rainbow = (
                    int(128 + 127 * math.sin(hue * 2 * math.pi)),
                    int(128 + 127 * math.sin(hue * 2 * math.pi + 2.094)),
                    int(128 + 127 * math.sin(hue * 2 * math.pi + 4.188)),
                )
                color = (
                    min(255, (color[0] + rainbow[0]) // 2),
                    min(255, (color[1] + rainbow[1]) // 2),
                    min(255, (color[2] + rainbow[2]) // 2),
                )

            # ── 外发光层（脉冲宽度） ──
            wave = abs(math.sin((t_mid - pulse_pos) * math.pi * 3))
            pulse_width = bw_out + int(12 * wave)
            outer_col = tuple(c // 4 for c in color)
            cv2.polylines(img, [seg], False, outer_col, pulse_width, cv2.LINE_AA)

            # ── 主色层 ──
            cv2.polylines(img, [seg], False, color, bw_main, cv2.LINE_AA)

            # ── 高光层 ──
            bright = tuple(min(255, c + 130) for c in color)
            cv2.polylines(img, [seg], False, bright, bw_inner, cv2.LINE_AA)

            # ── 流光亮点 ──
            if abs(t_mid - pulse_pos) < 0.08:
                glow = int(255 * (1 - abs(t_mid - pulse_pos) / 0.08))
                if glow > 60:
                    hl_col = (
                        min(255, color[0] + glow),
                        min(255, color[1] + glow),
                        min(255, color[2] + glow),
                    )
                    cv2.polylines(img, [seg], False, hl_col, bw_main + 6, cv2.LINE_AA)

        # ── 蛇身粒子尾迹 ──
        if GameConfig.SNAKE_TRAIL_PARTICLES and n > 3:
            self.trail_particle_counter += 1
            if self.trail_particle_counter >= GameConfig.SNAKE_TRAIL_INTERVAL:
                self.trail_particle_counter = 0
                mid_idx = n // 2
                mx, my = self.points[mid_idx]
                self._spawn_particles(mx, my, count=2,
                                      palette=theme.sparkle_palette)

    def _draw_snake_head(self, img: np.ndarray) -> None:
        """绘制蛇头（主题色 + 含眼睛）。"""
        if not self.points:
            return
        hx, hy = self.points[-1]
        theme = self.current_theme

        cv2.circle(img, (hx, hy), GameConfig.SNAKE_HEAD_RADIUS, theme.head_base, -1)

        glow_r = GameConfig.SNAKE_HEAD_RADIUS + 12
        glow_a = 0.3 + 0.2 * abs(math.sin(self.frame_count * 0.06))
        glow_col = tuple(min(255, c + 80) for c in theme.head_base)
        overlay = img.copy()
        cv2.circle(overlay, (hx, hy), glow_r, glow_col, -1)
        cv2.addWeighted(overlay, glow_a, img, 1 - glow_a, 0, dst=img)

        cv2.circle(img, (hx, hy), 22, theme.head_eye_bg, -1, cv2.LINE_AA)
        for ex, ey in [(hx - 8, hy - 7), (hx + 8, hy - 7)]:
            cv2.circle(img, (ex, ey), 5, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(img, (ex, ey), 2, (0, 0, 40), -1)

    def _draw_food(self, img: np.ndarray, fx: int, fy: int) -> np.ndarray:
        """绘制食物脉冲光环（主题色）+ PNG 精灵。"""
        ring_r = int(self.w_food // 2 + GameConfig.FOOD_PULSE_RING_BASE *
                     abs(math.sin(self.frame_count * 0.08)))
        cv2.circle(img, (fx, fy), ring_r, self.current_theme.food_ring, 2, cv2.LINE_AA)

        glow_r = ring_r + 8
        glow_col = tuple(c // 3 for c in self.current_theme.food_ring)
        cv2.circle(img, (fx, fy), glow_r, glow_col, 1, cv2.LINE_AA)

        return cvzone.overlayPNG(
            img, self.img_food,
            (fx - self.w_food // 2, fy - self.h_food // 2)
        )

    def _draw_bonus_food(self, img: np.ndarray) -> None:
        """绘制奖励食物（金色闪烁菱形）。"""
        if not self.bonus.active:
            return
        bx, by = self.bonus.pos

        pulse = abs(math.sin(self.frame_count * 0.12))
        radius = 20 + int(6 * pulse)

        glow_r = 35 + int(10 * pulse)
        cv2.circle(img, (bx, by), glow_r, (60, 50, 0), 2, cv2.LINE_AA)

        pts = np.array([
            (bx, by - radius),
            (bx + radius, by),
            (bx, by + radius),
            (bx - radius, by),
        ], np.int32)
        cv2.fillPoly(img, [pts], (255, 215, 0))
        cv2.polylines(img, [pts], True, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.putText(img, '*3', (bx + radius + 5, by + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 215, 0), 2, cv2.LINE_AA)

    def _draw_eat_flash(self, img: np.ndarray) -> np.ndarray:
        """绘制吃食物时的全屏闪光（主题色）。"""
        if self.eat_flash <= 0:
            return img
        a = (self.eat_flash / GameConfig.EAT_FLASH_DURATION) * GameConfig.EAT_FLASH_ALPHA
        flash = img.copy()
        cv2.rectangle(flash, (0, 0), (self.frame_w, self.frame_h),
                      self.current_theme.flash_color, -1)
        img = cv2.addWeighted(img, 1 - a, flash, a, 0)
        self.eat_flash -= 1
        return img

    def _draw_border(self, img: np.ndarray) -> None:
        """游戏区域脉冲边框（双主题色渐变）。"""
        t = abs(math.sin(self.frame_count * 0.04))
        cA, cB = self.current_theme.border_a, self.current_theme.border_b
        col = (
            int(cA[0] + (cB[0] - cA[0]) * t),
            int(cA[1] + (cB[1] - cA[1]) * t),
            int(cA[2] + (cB[2] - cA[2]) * t),
        )
        cv2.rectangle(img, (2, 2), (self.frame_w - 3, self.frame_h - 3), col, 3)

        inner_col = tuple(c // 2 for c in col)
        cv2.rectangle(img, (6, 6), (self.frame_w - 7, self.frame_h - 7), inner_col, 1)

    def _draw_ui(self, img: np.ndarray) -> None:
        """绘制分数、等级、最高分、FPS（主题色）。"""
        theme = self.current_theme
        level = self.score // GameConfig.SPEED_INCREASE_INTERVAL + 1

        self._neon_text(img, theme.name, (30, 35), 0.7, (120, 120, 120), 1)
        self._neon_text(img, f'Score  {self.score}', (30, 75),
                        1.8, theme.ui_score, 2)
        self._neon_text(img, f'Level  {level}', (30, 125),
                        1.2, theme.ui_level, 1)
        self._neon_text(img, f'High  {self.high_score}', (30, 165),
                        0.9, (150, 150, 150), 1)

        fps_text = f'FPS  {int(self.current_fps)}'
        self._neon_text(img, fps_text, (self.frame_w - 140, 50),
                        0.9, (100, 100, 100), 1)

    def _draw_game_over_stats(self, img: np.ndarray) -> None:
        """在 Game Over 画面显示进阶统计。"""
        fw, fh = self.frame_w, self.frame_h
        elapsed = time.time() - self.stats.start_time
        minutes = int(elapsed) // 60
        seconds = int(elapsed) % 60

        stats_lines = [
            f'Time  {minutes:02d}:{seconds:02d}',
            f'Eaten  {self.stats.foods_eaten}',
            f'Length  {int(self.stats.max_snake_length)}',
        ]
        for i, line in enumerate(stats_lines):
            y = fh // 2 + 95 + i * 45
            self._neon_text(img, line, (fw // 2 - 70, y),
                            1.0, (160, 160, 160), 1)

    def _apply_crt_filter(self, img: np.ndarray) -> np.ndarray:
        """CRT 复古扫描线滤镜：在画面上叠加半透明黑色水平细线（间隔 2 像素）。

        使用预分配的 mask 实现零分配后处理，对帧率几乎无影响。
        可通过 GameConfig.CRT_ENABLED / CRT_ALPHA 控制。
        """
        if not GameConfig.CRT_ENABLED:
            return img

        if not hasattr(self, '_crt_lines') or self._crt_lines.shape[:2] != img.shape[:2]:
            h, w = img.shape[:2]
            lines = np.zeros((h, w, 3), dtype=np.uint8)
            lines[1::2, :] = (0, 0, 0)          # 奇数行画黑线
            self._crt_lines = lines
            self._crt_alpha = float(GameConfig.CRT_ALPHA)

        return cv2.addWeighted(img, 1.0, self._crt_lines, self._crt_alpha, 0)

    def _draw_start_screen(self, img: np.ndarray) -> np.ndarray:
        """绘制开始画面：标题 + 主题名 + 操作提示，等待玩家开始。"""
        fw, fh = self.frame_w, self.frame_h
        theme = self.current_theme

        pulse = abs(math.sin(self.frame_count * 0.04))
        title_col = (
            int(theme.ui_score[0] * (0.5 + 0.5 * pulse)),
            int(theme.ui_score[1] * (0.5 + 0.5 * pulse)),
            int(theme.ui_score[2] * (0.5 + 0.5 * pulse)),
        )

        self._neon_text(img, 'SNAKE', (fw // 2 - 180, fh // 2 - 130),
                        4.0, title_col, 3)

        self._neon_text(img, f'-- {theme.name} --', (fw // 2 - 110, fh // 2 - 60),
                        1.2, (160, 160, 160), 1)

        prompt_pulse = abs(math.sin(self.frame_count * 0.06))
        prompt_col = (int(200 * prompt_pulse + 55),
                      int(200 * prompt_pulse + 55),
                      int(200 * prompt_pulse + 55))
        self._neon_text(img, 'Show your finger to start',
                        (fw // 2 - 210, fh // 2 + 30),
                        1.1, prompt_col, 1)

        instructions = [
            'Index finger to control the snake',
            'P = Pause    R = Restart    Q = Quit',
        ]
        for i, txt in enumerate(instructions):
            self._neon_text(img, txt, (fw // 2 - 250, fh // 2 + 100 + i * 45),
                            0.8, (120, 120, 120), 1)

        if self.high_score > 0:
            self._neon_text(img, f'Best  {self.high_score}',
                            (fw // 2 - 60, fh // 2 + 200),
                            1.0, (150, 150, 150), 1)

        return img

    # ──────── 逻辑更新 ────────

    def _update_snake(self, head: tuple[int, int]) -> None:
        """更新蛇的坐标列表。"""
        cx, cy = head
        px, py = self.previous_head
        distance = math.hypot(cx - px, cy - py)

        self.points.append((cx, cy))
        self.lengths.append(distance)
        self.current_length += distance
        self.previous_head = head

        if self.current_length > self.stats.max_snake_length:
            self.stats.max_snake_length = self.current_length

        while self.current_length > self.allowed_length and self.lengths:
            self.current_length -= self.lengths.pop(0)
            self.points.pop(0)

    def _check_boundary_collision(self, head: tuple[int, int]) -> bool:
        """检测蛇头边界碰撞。返回 True 表示撞墙。"""
        cx, cy = head
        m = GameConfig.BOUNDARY_MARGIN
        if cx <= m or cx >= self.frame_w - m or cy <= m or cy >= self.frame_h - m:
            return True
        return False

    def _check_food_collision(self, head: tuple[int, int]) -> bool:
        """检测是否吃到普通食物。"""
        cx, cy = head
        fx, fy = self.food_point
        if abs(cx - fx) < self.w_food // 2 and abs(cy - fy) < self.h_food // 2:
            self._spawn_particles(fx, fy)
            self.popups.append(Popup(
                x=fx, y=fy, life=GameConfig.POPUP_LIFE,
                max_life=GameConfig.POPUP_LIFE,
            ))
            self.food_point = self._new_food_location()
            self.allowed_length = min(
                self.allowed_length + GameConfig.LENGTH_INCREMENT,
                GameConfig.MAX_LENGTH
            )
            self.score += 1
            self.stats.foods_eaten += 1
            self.bonus.cooldown = max(0, self.bonus.cooldown // 2)
            self.eat_flash = GameConfig.EAT_FLASH_DURATION
            self.audio.play_eat()
            return True
        return False

    def _check_bonus_collision(self, head: tuple[int, int]) -> None:
        """检测是否吃到奖励食物。"""
        if not self.bonus.active:
            return
        cx, cy = head
        bx, by = self.bonus.pos
        if math.hypot(cx - bx, cy - by) < 35:
            self._eat_bonus()

    def _check_self_collision(self, head: tuple[int, int]) -> bool:
        """检测蛇头是否与自身碰撞（点→线段距离检测）。

        ⚠️ 旧版用 pointPolygonTest 将蛇身路径隐式闭合为多边形，
           当蛇身弯曲围成环状时蛇头总在多边形内部 → 自动死亡。

        ✅ 新版：蛇头到每段身体线段的最短距离 < 碰撞半径 → 才判碰撞。
           蛇身曲线无论怎样弯曲都不会产生「围成区域」效应。
        """
        pts = self.points
        n = len(pts)
        if n < 3:
            return False

        # ── 物理距离免疫（蛇头附近 N px 不检测） ──
        IMMUNE_DIST = float(GameConfig.SELF_COLLISION_IMMUNE_DIST)
        cum_dist = 0.0
        start_idx = 0
        for i in range(n - 1, 0, -1):
            dx = pts[i][0] - pts[i - 1][0]
            dy = pts[i][1] - pts[i - 1][1]
            cum_dist += math.hypot(dx, dy)
            if cum_dist >= IMMUNE_DIST:
                start_idx = i
                break

        if start_idx < 2:          # 无可检测的有效身体段
            return False

        # ── 碰撞半径(px)：蛇头中心到身体中心线的触发距离 ──
        CR = GameConfig.SNAKE_HEAD_RADIUS + GameConfig.SNAKE_BODY_WIDTH_MAIN
        CR2 = CR * CR
        hx, hy = head

        # ── 逐段检测：点到线段的最短距离 ──
        for seg_i in range(start_idx):
            x1, y1 = pts[seg_i]
            x2, y2 = pts[seg_i + 1]

            abx = x2 - x1
            aby = y2 - y1
            apx = hx - x1
            apy = hy - y1

            ab2 = abx * abx + aby * aby
            if ab2 == 0:
                continue

            # 投影系数 t ∈ [0, 1]
            t = (apx * abx + apy * aby) / ab2
            t = max(0.0, min(1.0, t))

            # 线段上最近点
            cx = x1 + t * abx
            cy = y1 + t * aby

            # 距离平方（免开方）
            dx = hx - cx
            dy = hy - cy
            if dx * dx + dy * dy < CR2:
                return True

        return False

    # ──────── 主更新帧 ────────

    def update(self, img_main: np.ndarray, current_head: tuple[int, int]) -> np.ndarray:
        """主更新循环: 游戏逻辑 + 渲染。"""
        self.frame_count += 1
        self._update_fps()

        img_main = self._draw_background(img_main)

        # ── 开始画面 ──
        if self.state == GameState.COUNTDOWN:
            return self._draw_start_screen(img_main)

        # ── 暂停状态 ──
        if self.state == GameState.PAUSED:
            img_main = self._dark_overlay(img_main, 0.6)
            pulse = abs(math.sin(self.frame_count * 0.05))
            pb = self.current_theme.pause_base
            pause_col = (
                int(pb[0] * (0.7 + 0.3 * pulse)),
                int(pb[1] * (0.7 + 0.3 * pulse)),
                int(pb[2] * (0.7 + 0.3 * pulse)),
            )
            ccx, ccy = self.frame_w // 2, self.frame_h // 2
            self._neon_text(img_main, 'PAUSED', (ccx - 140, ccy - 30), 3.0, pause_col, 2)
            self._neon_text(img_main, 'Press P to continue', (ccx - 200, ccy + 50),
                            1.3, (130, 130, 130), 1)
            self._draw_ui(img_main)
            return img_main

        # ── 游戏结束 ──
        if self.state == GameState.GAME_OVER:
            img_main = self._dark_overlay(img_main, 0.75)
            pulse = abs(math.sin(self.frame_count * 0.05))
            gob = self.current_theme.gameover_base
            go_col = (
                int(gob[0] * (0.3 + 0.7 * pulse)),
                int(gob[1] * (0.3 + 0.7 * pulse)),
                int(gob[2] * (0.3 + 0.7 * pulse)),
            )
            ccx, ccy = self.frame_w // 2, self.frame_h // 2
            self._neon_text(img_main, 'GAME  OVER', (ccx - 210, ccy - 80), 3.0, go_col, 2)
            self._neon_text(img_main, f'Score  {self.score}', (ccx - 100, ccy),
                            2.2, (0, 220, 255), 2)

            if self.score >= self.high_score:
                self._neon_text(img_main, 'NEW HIGH SCORE!', (ccx - 180, ccy + 60),
                                1.5, (255, 200, 0), 2)
            else:
                self._neon_text(img_main, f'High Score  {self.high_score}',
                                (ccx - 140, ccy + 60), 1.5, (180, 180, 180), 1)

            self._draw_game_over_stats(img_main)

            rp = abs(math.sin(self.frame_count * 0.06))
            restart_col = (int(130 + 125 * rp), int(130 + 125 * rp), int(130 + 125 * rp))
            self._neon_text(img_main, 'Clench fist -> open hand  or  press R',
                            (ccx - 340, ccy + 210), 1.1, restart_col, 1)
            return img_main

        # ══════════════════════════════════════
        #  PLAYING
        # ══════════════════════════════════════

        self._update_theme()

        speed_mult = self._get_speed_multiplier()
        frame_skip = max(GameConfig.MIN_FRAME_SKIP, int(3 / speed_mult))

        self.frame_skip_counter += 1
        if self.frame_skip_counter >= frame_skip:
            self.frame_skip_counter = 0
        else:
            return self._render_playing(img_main)

        self._update_snake(current_head)

        if self._check_boundary_collision(current_head):
            self.state = GameState.GAME_OVER
            self._check_and_save_high_score()
            self.audio.play_die_wall()
            return self._render_playing(img_main)

        self._check_food_collision(current_head)

        if self.bonus.active:
            self.bonus.timer -= 1
            if self.bonus.timer <= 0:
                self.bonus.active = False
                self.bonus.cooldown = GameConfig.BONUS_COOLDOWN
        else:
            self.bonus.cooldown -= 1
            self._try_spawn_bonus()
        self._check_bonus_collision(current_head)

        level = self.score // GameConfig.SPEED_INCREASE_INTERVAL + 1
        if level > self.stats.highest_level:
            self.stats.highest_level = level

        # ── 自碰检测（带容忍帧数，滤除手抖误触） ──
        if self._check_self_collision(current_head):
            self._collision_grace_counter += 1
            grace = GameConfig.SELF_COLLISION_GRACE_FRAMES
            if self._collision_grace_counter >= grace:
                self.state = GameState.GAME_OVER
                self._check_and_save_high_score()
                self.audio.play_die_self()
                return self._render_playing(img_main)
        else:
            self._collision_grace_counter = 0

        return self._render_playing(img_main)

    def _render_playing(self, img_main: np.ndarray) -> np.ndarray:
        """渲染 PLAYING 状态画面。"""
        fx, fy = self.food_point

        self._draw_particles(img_main)
        self._draw_snake_body(img_main)
        self._draw_snake_head(img_main)
        img_main = self._draw_food(img_main, fx, fy)
        self._draw_bonus_food(img_main)
        self._draw_popups(img_main)
        img_main = self._draw_eat_flash(img_main)
        self._draw_ui(img_main)
        self._draw_border(img_main)

        return img_main

    # ──────── 外部控制 ────────

    def toggle_pause(self) -> None:
        """切换暂停/继续。"""
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING


# ──────────────────────────────────────────────
#  主程序入口
# ──────────────────────────────────────────────

def main() -> None:
    """主函数：初始化摄像头 / 检测器 / 游戏并进入主循环。"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：无法打开摄像头！")
        print("请检查：")
        print("1. 摄像头是否正确连接")
        print("2. 摄像头是否被其他程序占用")
        print("3. 摄像头权限是否允许")
        return

    cap.set(3, 1280)
    cap.set(4, 720)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"摄像头分辨率: {frame_w}x{frame_h}")

    try:
        detector = HandDetector(detectionCon=0.8, maxHands=1)
    except Exception as e:
        print(f"错误：无法初始化手势检测器: {e}")
        cap.release()
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    food_path = os.path.join(script_dir, "donut.png")

    # 初始化音效控制器
    audio = AudioController()

    try:
        game = SnakeGameClass(food_path, frame_w, frame_h, audio)
    except SnakeGameError as e:
        print(f"错误：{e}")
        audio.close()
        cap.release()
        return

    print("\n游戏控制说明：")
    print("- 伸出食指控制蛇移动")
    print("- 按 P 键暂停/继续游戏")
    print("- 按 R 键重新开始")
    print("- 按 Q 或 ESC 退出游戏")
    print("\n游戏开始！\n")

    # GAME_OVER 重新开始手势：握拳 → 张开手掌
    # 0=等待握拳 1=已握拳等待张开 2=触发重开
    restart_gesture_phase: int = 0

    while True:
        success, img = cap.read()
        if not success:
            print("警告：无法读取摄像头画面")
            break

        img = cv2.flip(img, 1)

        # ── 手势检测 ──
        try:
            hands, img = detector.findHands(img, flipType=False)
        except Exception as e:
            print(f"手势检测错误: {e}")
            hands = []

        # ── 处理手势 ──
        if hands:
            hand = hands[0]
            fingers = detector.fingersUp(hand)

            if game.state == GameState.COUNTDOWN:
                if fingers[1]:
                    game.state = GameState.PLAYING
                    game.stats.start_time = time.time()
                    print("游戏开始！")
                head = game.previous_head

            elif game.state == GameState.GAME_OVER:
                is_fist = all(f == 0 for f in fingers[1:])
                is_open = all(f == 1 for f in fingers[1:])

                if is_fist:
                    if restart_gesture_phase == 0:
                        print("检测到握拳，请张开手掌重新开始")
                    restart_gesture_phase = 1
                elif is_open and restart_gesture_phase == 1:
                    restart_gesture_phase = 0
                    game._reset()
                    game.state = GameState.PLAYING
                    game.stats.start_time = time.time()
                    print("游戏重新开始！")
                else:
                    restart_gesture_phase = 0

                head = game.previous_head

            elif game.state == GameState.PLAYING:
                lm_list = hand['lmList']
                raw_x, raw_y = lm_list[8][:2]
                point_index = (
                    max(0, min(raw_x, frame_w - 1)),
                    max(0, min(raw_y, frame_h - 1)),
                )
                if fingers[1]:
                    game._last_hand_position = game._smooth_gesture(point_index)
                head = game._last_hand_position
            else:
                head = game.previous_head
        else:
            head = game._last_hand_position if game.state == GameState.PLAYING else game.previous_head

        img = game.update(img, head)
        img = game._apply_crt_filter(img)          # CRT 扫描线后处理

        cv2.imshow("Neon Snake v4 by KongDeShang", img)
        key = cv2.waitKey(1)

        if key in (ord('r'), ord('R')):
            if game.state == GameState.GAME_OVER:
                game._reset()
                game.state = GameState.PLAYING
                game.stats.start_time = time.time()
                print("游戏重新开始！")
            else:
                game._reset()
                print("回到开始画面")
        elif key in (ord('p'), ord('P')):
            game.toggle_pause()
            if game.state == GameState.PAUSED:
                print("游戏已暂停")
            elif game.state == GameState.PLAYING:
                print("游戏继续")
        elif key in (ord('q'), ord('Q'), 27) or \
                cv2.getWindowProperty("Snake Game", cv2.WND_PROP_VISIBLE) < 1:
            print(f"\n游戏结束！最终分数: {game.score}")
            if 0 < game.score == game.high_score:
                print(f"恭喜！新纪录: {game.high_score}")
            break

    cap.release()
    cv2.destroyAllWindows()
    audio.close()
    print("感谢游玩！")


if __name__ == '__main__':
    main()
