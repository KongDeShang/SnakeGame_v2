# 🎬 SnakeGame 抖音自动剪辑器

根据素材和配置，一键生成 9:16 竖屏抖音短视频。

---

## 🚀 使用方法

### 1️⃣ 安装依赖

```bash
cd video_editor
pip install -r requirements.txt
```

> **可选加速：** 安装 librosa 可启用 BGM 踩点对齐
> ```bash
> pip install librosa
> ```

### 2️⃣ 准备素材

把录好的视频片段放到 `videos/` 目录，按顺序命名：

```
videos/
├── 01_hook.mp4          # 开头钩子：手指控制蛇
├── 02_gameplay.mp4      # 玩法展示：吃食物
├── 03_bonus.mp4          # 金色奖励食物
├── 04_theme_switch.mp4  # 主题切换
├── 05_snake_closeup.mp4 # 蛇身流光特写
├── 06_code.mp4          # 代码展示
├── 07_speed_up.mp4      # 加速+死亡
├── 08_gameover.mp4      # GAME OVER画面
├── 09_restart.mp4       # 握拳复活
└── 10_folder.mp4        # 项目文件展示
```

### 3️⃣ 放 BGM

把背景音乐放到 `bgm/bgm.mp3`（支持 mp3/wav）

### 4️⃣ 放音效（可选）

把音效文件放到 `sfx/` 目录：

```
sfx/
├── eat.wav       # 吃食物
├── bonus.wav     # 吃奖励
├── die.wav       # 死亡
└── gameover.wav  # 游戏结束
```

不提供音效文件也不影响运行，只是没有音效。

### 5️⃣ 一键生成

```bash
python auto_edit.py
```

输出文件在 `output/snake_game_douyin.mp4`

---

## ⚙️ 配置说明

编辑 `config.json` 可自定义：

| 配置项 | 说明 |
|--------|------|
| `output` | 输出格式（分辨率/帧率） |
| `bgm` | 背景音乐（音量/渐入渐出） |
| `segments` | 片段列表（文件/文字/样式/变速） |
| `segments[].text` | 该片段叠加的字幕 |
| `segments[].speed` | 播放速度（1.0=正常，1.5=1.5倍速） |
| `segments[].sfx` | 音效名称（对应 sfx/ 目录的文件名） |
| `end_card` | 结尾引导卡（标题/副标题/话题标签） |
| `sound_effects` | 音效文件路径映射 |
| `crop` | 竖屏裁切设置 |

---

## 📁 目录结构

```
video_editor/
├── auto_edit.py           # 主脚本
├── config.json            # 配置（已预填好故事板）
├── requirements.txt       # 依赖
├── README.md              # 本文件
├── videos/                # ← 放你的素材视频
├── bgm/                   # ← 放BGM
│   └── bgm.mp3
├── sfx/                   # ← 放音效（可选）
│   ├── eat.wav
│   ├── bonus.wav
│   ├── die.wav
│   └── gameover.wav
└── output/                # 输出目录（自动生成）
```

---

## 📝 素材录制建议

1. **游戏录屏**：运行游戏后，用 OBS / Windows Game Bar (Win+G) 录屏
2. **每个动作单独录**：吃食物、吃奖励、死亡、重开，各录一段
3. **代码展示**：在 VS Code 中打开 `main_improved.py`，慢速滚动
4. **手部出镜**：用手机拍手在摄像头前操作的画面
5. **横屏录制**：建议 16:9 横屏录制，脚本会自动裁成 9:16 竖屏

---

## ❓ 常见问题

**Q: 中文文字显示乱码/方块？**
A: 脚本会自动检测系统中文字体（微软雅黑/SimHei等），如果没找到，可以手动在 `config.json` 中设置 `font_path`

**Q: 输出视频太大？**
A: 在 `auto_edit.py` 中降低 `bitrate` 参数（默认 8000k，改成 4000k 可减半）

**Q: 如何加自己的文字？**
A: 编辑 `config.json` 中 `segments[].text` 字段，支持修改颜色、大小、位置
