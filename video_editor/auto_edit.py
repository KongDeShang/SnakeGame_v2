#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SnakeGame 抖音自动剪辑器  v1.0
================================
根据 config.json 配置，自动拼接素材并输出 9:16 竖屏抖音视频。

用法:
    pip install -r requirements.txt
    python auto_edit.py

功能:
    - 自动拼接视频片段 + 转场
    - 字幕叠加 (中文支持)
    - BGM 自动时长匹配
    - 可选 librosa 踩点对齐
    - 16:9 → 9:16 竖屏裁切
    - 音效叠加
    - 结尾引导卡片
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import numpy as np

# ── moviepy v2 导入 ──────────────────────────────────────────
try:
    from moviepy import (
        VideoFileClip,
        AudioFileClip,
        ImageClip,
        TextClip,
        CompositeVideoClip,
        CompositeAudioClip,
        concatenate_videoclips,
        concatenate_audioclips,
    )
    from moviepy.video.fx import (
        CrossFadeIn,
        MultiplySpeed,
        MakeLoopable,
    )
    from moviepy.audio.fx import (
        MakeAudioFadeIn,
        MakeAudioFadeOut,
    )
    import moviepy.video.fx as vfx_module
except ImportError:
    print("❌ 请先安装依赖: pip install -r requirements.txt")
    print("   核心依赖: moviepy>=2.0.0 numpy")
    sys.exit(1)

# ── 可选 librosa（踩点检测） ─────────────────────────────────
HAS_LIBROSA = False
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    print("ℹ️ [可选] 安装 librosa 可启用BGM踩点对齐: pip install librosa")


# ═════════════════════════════════════════════════════════════
#  配置加载
# ═════════════════════════════════════════════════════════════

def load_config(path: str = "config.json") -> dict:
    """加载并校验配置文件"""
    if not os.path.exists(path):
        print(f"❌ 配置文件不存在: {path}")
        print(f"   请参考 config.json 模板")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # 基本校验
    if "segments" not in cfg or not cfg["segments"]:
        print("❌ 配置中缺少 segments 或为空")
        sys.exit(1)

    return cfg


# ═════════════════════════════════════════════════════════════
#  字体检测（中文支持）
# ═════════════════════════════════════════════════════════════

def find_chinese_font() -> str | None:
    """查找系统中可用的中文字体路径"""
    candidates = [
        # Windows
        "C:/Windows/Fonts/msyh.ttc",        # Microsoft YaHei
        "C:/Windows/Fonts/msyhbd.ttc",       # Microsoft YaHei Bold
        "C:/Windows/Fonts/simhei.ttf",       # SimHei
        "C:/Windows/Fonts/simsun.ttc",       # SimSun
        "C:/Windows/Fonts/deng.ttf",         # DengXian
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Linux
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    return None


# ═════════════════════════════════════════════════════════════
#  节拍检测
# ═════════════════════════════════════════════════════════════

def detect_beats(bgm_path: str) -> tuple[float, list[float]]:
    """用 librosa 检测 BGM 节拍。

    返回:
        tempo: BPM
        beat_times: 每个节拍的时间点列表（秒）
    """
    if not HAS_LIBROSA:
        return 0.0, []

    print("🎵 正在分析BGM节拍...")
    try:
        # 降低采样率加速计算
        y, sr = librosa.load(bgm_path, sr=22050)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, beat_frames = librosa.beat.beat_track(
            onset_envelope=onset_env, sr=sr
        )
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        print(f"    BPM: {tempo:.1f}, 节拍数: {len(beat_times)}")
        return float(tempo), beat_times
    except Exception as e:
        print(f"    ⚠️ 节拍分析失败: {e}")
        return 0.0, []


def align_to_beat(target_time: float, beat_times: list[float]) -> float:
    """将目标时间对齐到最近的节拍点"""
    if not beat_times:
        return target_time
    arr = np.array(beat_times)
    idx = np.argmin(np.abs(arr - target_time))
    return float(arr[idx])


# ═════════════════════════════════════════════════════════════
#  文字工具
# ═════════════════════════════════════════════════════════════

def make_text_clip(
    text: str,
    duration: float,
    fontsize: int = 60,
    color: str = "#FFFFFF",
    stroke_color: str = "black",
    stroke_width: int = 2,
    position: Any = ("center", "bottom"),
    font_path: str | None = None,
    animation: str = "fade_in",
    video_size: tuple[int, int] = (1080, 1920),
) -> ImageClip:
    """创建带动画的文字叠加层。

    moviepy v2 的 TextClip 基于 Pillow，不需要 ImageMagick。
    如果 Pillow 不支持某字体，自动降级为默认字体。
    """
    try:
        txt_clip = TextClip(
            text=text,
            font_size=fontsize,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            font=font_path,
            size=(video_size[0] - 80, None),
            method="caption",
            text_align="center",
        ).with_duration(duration)

        # 位置
        if isinstance(position, list):
            position = tuple(position)
        txt_clip = txt_clip.with_position(position)

        # 动画
        if animation in ("fade_in", "fade"):
            txt_clip = txt_clip.with_effects([CrossFadeIn(0.3)])

        return txt_clip

    except Exception as e:
        print(f"    ⚠️ 文字生成失败 ('{text}'): {e}")
        # 空白占位
        return (
            ImageClip(np.zeros((1, 1, 3), dtype=np.uint8))
            .with_duration(duration)
            .with_opacity(0)
        )


# ═════════════════════════════════════════════════════════════
#  竖屏裁切
# ═════════════════════════════════════════════════════════════

def crop_to_vertical(
    clip: VideoFileClip,
    target_w: int = 1080,
    target_h: int = 1920,
) -> VideoFileClip:
    """将横屏视频裁切为竖屏 9:16（居中裁切）"""
    orig_w, orig_h = clip.w, clip.h
    orig_ratio = orig_w / orig_h
    target_ratio = target_w / target_h  # 9:16 ≈ 0.5625

    if orig_ratio > target_ratio:
        # 原素材更宽（如 16:9）→ 裁左右
        new_w = int(orig_h * target_ratio)
        new_h = orig_h
    else:
        # 原素材更窄 → 裁上下
        new_w = orig_w
        new_h = int(orig_w / target_ratio)

    x1 = max(0, (orig_w - new_w) // 2)
    y1 = max(0, (orig_h - new_h) // 2)

    cropped = clip.cropped(x1=x1, y1=y1, width=new_w, height=new_h)
    return cropped.resized((target_w, target_h))


# ═════════════════════════════════════════════════════════════
#  片段处理
# ═════════════════════════════════════════════════════════════

def process_segment(
    seg: dict,
    idx: int,
    font_path: str | None,
    video_size: tuple[int, int],
    total_segments: int,
    beat_times: list[float] | None = None,
) -> tuple[VideoFileClip | None, float]:
    """处理单个视频片段。

    返回:
        (clip, 片段实际时长)
    """
    filepath = seg["file"]
    seg_text = seg.get("text", "")
    style = seg.get("text_style", {})
    speed = seg.get("speed", 1.0)

    print(f"  [{idx+1}/{total_segments}] {os.path.basename(filepath)}")

    if not os.path.exists(filepath):
        print(f"    ⚠️ 文件不存在，跳过")
        return None, 0.0

    try:
        clip = VideoFileClip(filepath)

        # ── 变速 ──
        if speed != 1.0:
            clip = clip.with_effects([MultiplySpeed(speed)])

        # ── 竖屏裁切 ──
        clip = crop_to_vertical(clip, video_size[0], video_size[1])

        duration = clip.duration

        # ── 节拍对齐（裁剪末尾到最近的节拍点） ──
        if beat_times and duration > 0.5:
            aligned_end = align_to_beat(duration, beat_times)
            if aligned_end < duration - 0.1:
                clip = clip.subclipped(0, aligned_end)
                duration = aligned_end
                print(f"    ↪ 对齐到节拍: {aligned_end:.2f}s")

        # ── 添加文字 ──
        if seg_text:
            txt_clip = make_text_clip(
                text=seg_text,
                duration=duration,
                fontsize=style.get("fontsize", 60),
                color=style.get("color", "#FFFFFF"),
                stroke_color=style.get("stroke_color", "black"),
                stroke_width=style.get("stroke_width", 2),
                position=style.get("position", ("center", "bottom")),
                font_path=font_path,
                animation=style.get("animation", "fade_in"),
                video_size=video_size,
            )
            clip = CompositeVideoClip([clip, txt_clip], size=video_size)

        print(f"    ✅ {duration:.1f}s" + (f" (变速 {speed}x)" if speed != 1.0 else ""))

        return clip, duration

    except Exception as e:
        print(f"    ❌ 处理失败: {e}")
        return None, 0.0


# ═════════════════════════════════════════════════════════════
#  音效系统
# ═════════════════════════════════════════════════════════════

def create_sound_effect_clips(
    sfx_config: dict,
    segment_durations: list[float],
    sfx_names: list[str | None],
) -> list[AudioFileClip]:
    """根据每段的音效配置，创建带时间偏移的音效 AudioClip 列表"""
    result: list[AudioFileClip] = []
    current_time = 0.0

    for dur, name in zip(segment_durations, sfx_names):
        if name and name in sfx_config:
            sfx_path = sfx_config[name]
            if os.path.exists(sfx_path):
                try:
                    sfx_clip = AudioFileClip(sfx_path).with_start(current_time)
                    result.append(sfx_clip)
                except Exception:
                    pass
        current_time += dur

    return result


# ═════════════════════════════════════════════════════════════
#  结尾卡片
# ═════════════════════════════════════════════════════════════

def create_end_card(
    cfg: dict,
    video_size: tuple[int, int],
    font_path: str | None,
) -> ImageClip | None:
    """生成结尾引导画面"""
    if not cfg.get("end_card", {}).get("enabled", True):
        return None

    ec = cfg["end_card"]
    duration = ec.get("duration", 4.0)
    w, h = video_size

    # 纯色背景
    bg_color = ec.get("bg_color", [10, 10, 30])
    bg = ImageClip(np.full((h, w, 3), bg_color, dtype=np.uint8)).with_duration(duration)

    elements: list = [bg]

    # 标题
    title = ec.get("title", "")
    if title:
        elements.append(
            make_text_clip(
                title, duration,
                fontsize=90, color=ec.get("text_color", "#FFD700"),
                stroke_color="black", stroke_width=3,
                position=("center", h // 3),
                font_path=font_path, animation="fade_in",
                video_size=video_size,
            )
        )

    # 副标题
    subtitle = ec.get("subtitle", "")
    if subtitle:
        elements.append(
            make_text_clip(
                subtitle, duration,
                fontsize=50, color=ec.get("subtitle_color", "#AAAAAA"),
                stroke_color="black", stroke_width=1,
                position=("center", h // 2 + 30),
                font_path=font_path, animation="fade_in",
                video_size=video_size,
            )
        )

    # 行动号召
    action = ec.get("action_text", "")
    if action:
        elements.append(
            make_text_clip(
                action, duration,
                fontsize=45, color="#FFFFFF",
                stroke_color="black", stroke_width=1,
                position=("center", "bottom"),
                font_path=font_path, animation="fade_in",
                video_size=video_size,
            )
        )

    # 话题标签
    hashtags = ec.get("hashtags", "")
    if hashtags:
        elements.append(
            make_text_clip(
                hashtags, duration,
                fontsize=35, color="#888888",
                stroke_color="black", stroke_width=1,
                position=("center", h - 120),
                font_path=font_path, animation="fade_in",
                video_size=video_size,
            )
        )

    return CompositeVideoClip(elements, size=video_size).with_duration(duration)


# ═════════════════════════════════════════════════════════════
#  音视频最终合成
# ═════════════════════════════════════════════════════════════

def mix_audio(
    video: VideoFileClip,
    bgm_path: str | None,
    bgm_volume: float = 0.35,
    fade_in: float = 1.0,
    fade_out: float = 2.0,
    sfx_clips: list[AudioFileClip] | None = None,
) -> VideoFileClip:
    """混合 BGM + 音效到视频"""
    audio_tracks = [video.audio]

    # ── BGM ──
    if bgm_path and os.path.exists(bgm_path):
        print("🎵 正在合成BGM...")
        try:
            bgm = AudioFileClip(bgm_path)

            # 裁剪 / 循环到视频长度
            if bgm.duration > video.duration:
                bgm = bgm.subclipped(0, video.duration)
            else:
                n_loops = int(np.ceil(video.duration / bgm.duration))
                bgm = concatenate_audioclips([bgm] * n_loops).subclipped(0, video.duration)

            # 音量 + 渐入渐出
            bgm = bgm.with_volume_scaled(bgm_volume)
            bgm = bgm.with_effects([
                MakeAudioFadeIn(fade_in),
                MakeAudioFadeOut(fade_out),
            ])
            audio_tracks.append(bgm)
        except Exception as e:
            print(f"    ⚠️ BGM处理失败: {e}")

    # ── 音效 ──
    if sfx_clips:
        audio_tracks.extend(sfx_clips)

    # ── 合路 ──
    valid_tracks = [a for a in audio_tracks if a is not None]
    if len(valid_tracks) > 1:
        video = video.with_audio(CompositeAudioClip(valid_tracks))

    return video


# ═════════════════════════════════════════════════════════════
#  主流程
# ═════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 50)
    print("  🐍 SnakeGame 抖音自动剪辑器")
    print("=" * 50)
    print()

    # ── 1. 加载配置 ──
    cfg = load_config("config.json")
    out_cfg = cfg["output"]
    bgm_cfg = cfg.get("bgm", {})
    sfx_cfg = cfg.get("sound_effects", {})
    segments = cfg["segments"]

    video_size = (out_cfg.get("width", 1080), out_cfg.get("height", 1920))
    output_fps = out_cfg.get("fps", 30)

    # ── 2. 检测字体 ──
    font_path = find_chinese_font()
    if font_path:
        print(f"🔤 检测到中文字体: {os.path.basename(font_path)}")
    else:
        print("ℹ️ 未找到中文字体，将使用系统默认")

    # ── 3. BGM 节拍分析 ──
    bgm_path = bgm_cfg.get("file", "bgm/bgm.mp3")
    beat_times: list[float] | None = None
    if bgm_path and os.path.exists(bgm_path) and HAS_LIBROSA:
        _, beat_times = detect_beats(bgm_path)
    elif bgm_path and not os.path.exists(bgm_path):
        print("ℹ️ 未找到BGM文件，视频将无背景音乐")
        bgm_path = None

    # ── 4. 处理每个片段 ──
    print(f"\n🎬 处理 {len(segments)} 个片段...")
    processed: list[VideoFileClip] = []
    durations: list[float] = []
    sfx_names: list[str | None] = []

    clip_counter = 0
    for i, seg in enumerate(segments):
        clip, dur = process_segment(seg, i, font_path, video_size,
                                    len(segments), beat_times)
        if clip is not None:
            processed.append(clip)
            durations.append(dur)
            sfx_names.append(seg.get("sfx"))
            clip_counter += 1

    if not processed:
        print("❌ 没有可用的视频片段，请检查素材")
        sys.exit(1)

    # ── 5. 拼接 + 转场 ──
    print(f"\n🔗 拼接 {clip_counter} 个片段...")
    trans_dur = segments[0].get("transition_duration", 0.3)

    clips_for_concat = []
    for i, clip in enumerate(processed):
        if i == 0:
            clips_for_concat.append(clip)
        else:
            clips_for_concat.append(clip.with_effects([CrossFadeIn(trans_dur)]))

    try:
        final = concatenate_videoclips(clips_for_concat, method="compose")
        print(f"    ✅ 拼接完成: {final.duration:.1f}s")
    except Exception as e:
        print(f"    ⚠️ 转场拼接失败: {e}")
        print(f"    → 回退到无转场模式")
        final = concatenate_videoclips(processed, method="compose")
        print(f"    ✅ 拼接完成: {final.duration:.1f}s")

    # ── 6. 结尾卡片 ──
    end_card = create_end_card(cfg, video_size, font_path)
    if end_card is not None:
        print("🎬 添加结尾卡片...")
        final = concatenate_videoclips([final, end_card], method="compose")

    # ── 7. 音效 ──
    sfx_clips = create_sound_effect_clips(sfx_cfg, durations, sfx_names)
    if sfx_clips:
        print(f"🔊 合成 {len(sfx_clips)} 个音效")

    # ── 8. 混合BGM ──
    final = mix_audio(
        final,
        bgm_path,
        bgm_volume=bgm_cfg.get("volume", 0.35),
        fade_in=bgm_cfg.get("fade_in", 1.0),
        fade_out=bgm_cfg.get("fade_out", 2.0),
        sfx_clips=sfx_clips,
    )

    # ── 9. 输出 ──
    output_path = out_cfg.get("file", "output/snake_game_douyin.mp4")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"\n💾 正在渲染输出视频...")
    print(f"   文件: {output_path}")
    print(f"   分辨率: {video_size[0]}x{video_size[1]}")
    print(f"   时长: {final.duration:.1f}s")
    print(f"   帧率: {output_fps}fps")
    print()

    start_time = time.time()
    try:
        final.write_videofile(
            output_path,
            fps=output_fps,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            threads=4,
            preset="medium",
            logger=None,  # 安静输出
        )
        elapsed = time.time() - start_time
        print(f"\n✅ 渲染完成！耗时 {elapsed:.0f}s")
        print(f"   📁 {os.path.abspath(output_path)}")

        # 文件大小
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   📦 {size_mb:.1f} MB")

    except Exception as e:
        print(f"\n❌ 渲染失败: {e}")
        sys.exit(1)

    # ── 清理 ──
    for clip in processed:
        try:
            clip.close()
        except Exception:
            pass
    try:
        final.close()
    except Exception:
        pass

    print("\n🎉 视频剪辑完成！快去抖音发布吧！")


if __name__ == "__main__":
    main()
