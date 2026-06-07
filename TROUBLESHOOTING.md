# 🔧 故障排除指南

## 问题描述

运行游戏时出现错误：
```
FileNotFoundError: The path does not exist: 
...mediapipe/modules/hand_landmark/hand_landmark_tracking_cpu.binarypb
```

这是 **mediapipe** 包损坏或版本不兼容导致的，与改进代码无关。

---

## 💡 解决方案

### 方案1：使用修复脚本（推荐）

双击运行 `fix_mediapipe.bat`，它会自动：
1. 卸载损坏的 mediapipe
2. 安装兼容版本
3. 验证安装是否成功

修复完成后，双击 `run_improved.bat` 启动改进版游戏。

---

### 方案2：手动修复

打开命令提示符，执行以下命令：

```bash
cd "C:\Users\kong\Desktop\projects\SnakeGame\SnakeGame版本2"
venv\Scripts\activate
pip uninstall mediapipe -y
pip install mediapipe==0.8.11
```

如果 0.8.11 版本安装失败，尝试最新版：
```bash
pip install mediapipe
```

---

### 方案3：重新创建虚拟环境

如果上述方法都不行，重建虚拟环境：

```bash
cd "C:\Users\kong\Desktop\projects\SnakeGame\SnakeGame版本2"

# 删除旧虚拟环境
rmdir /s /q venv

# 创建新虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install opencv-python
pip install cvzone
pip install mediapipe
pip install numpy
```

---

### 方案4：使用系统Python（临时方案）

如果虚拟环境一直有问题，可以在系统级别安装依赖：

```bash
# 使用系统Python安装（不推荐，但可以快速测试）
pip install opencv-python cvzone mediapipe numpy

# 然后直接运行
python main_improved.py
```

---

## 🎮 运行游戏

### 使用批处理脚本（推荐）

- **改进版**：双击 `run_improved.bat`
- **原版**：双击 `run_original.bat`

### 使用命令行

```bash
cd "C:\Users\kong\Desktop\projects\SnakeGame\SnakeGame版本2"
venv\Scripts\activate
python main_improved.py
```

---

## 🔍 验证安装

在虚拟环境中测试：

```bash
venv\Scripts\activate
python -c "from cvzone.HandTrackingModule import HandDetector; print('成功！')"
```

如果输出"成功！"说明环境正常。

---

## ⚠️ 常见问题

### 问题1：Python版本不兼容

**症状**：mediapipe 安装失败

**解决**：mediapipe 支持 Python 3.7-3.10，检查你的Python版本：
```bash
python --version
```

如果版本不在范围内，需要安装兼容的Python版本。

---

### 问题2：摄像头无法打开

**症状**：
```
错误：无法打开摄像头！
```

**解决**：
1. 检查摄像头是否被其他程序占用（如QQ、微信、Zoom）
2. 检查摄像头权限设置
3. 尝试更换摄像头编号：修改代码中的 `cv2.VideoCapture(0)` 改为 `cv2.VideoCapture(1)`

---

### 问题3：donut.png 文件不存在

**症状**：
```
错误：食物图片文件不存在: donut.png
```

**解决**：确保 `donut.png` 文件在同一目录下。如果丢失，可以使用任何 PNG 图片替代。

---

### 问题4：手势识别不准确

**解决**：
1. 确保光线充足
2. 手势与摄像头距离适中（30-60cm）
3. 调整 `detectionCon` 参数（在代码中搜索）：
   ```python
   detector = HandDetector(detectionCon=0.6, maxHands=1)  # 降低检测阈值
   ```

---

## 📋 依赖版本信息

推荐的依赖版本组合：

```
opencv-python==4.5.5.64
cvzone==1.5.6
mediapipe==0.8.11
numpy==1.21.6
```

或者使用最新稳定版：

```
opencv-python>=4.5.0
cvzone>=1.5.0
mediapipe>=0.8.11
numpy>=1.19.0
```

---

## 🆘 仍然无法解决？

请提供以下信息：

1. Python版本：`python --version`
2. 操作系统版本
3. 完整的错误信息（截图或复制文本）
4. 尝试过的解决方案

可能的诊断命令：

```bash
# 检查Python版本
python --version

# 检查已安装的包
pip list

# 检查mediapipe是否正确安装
python -c "import mediapipe; print(mediapipe.__version__)"

# 检查cvzone是否正确安装
python -c "import cvzone; print(cvzone.__version__)"

# 检查opencv是否正确安装
python -c "import cv2; print(cv2.__version__)"
```

---

## ✅ 成功标志

当你看到以下输出时，说明游戏正常启动：

```
摄像头分辨率: 1280x720

游戏控制说明：
- 伸出食指控制蛇移动
- 按 P 键暂停/继续游戏
- 按 R 键重新开始
- 按 Q 或 ESC 退出游戏

游戏开始！
```

然后应该会弹出游戏窗口。

---

## 🎯 快速诊断流程

```
1. 运行 fix_mediapipe.bat
   ├─ 成功 → 运行 run_improved.bat
   └─ 失败 → 进行步骤2

2. 检查Python版本
   ├─ 3.7-3.10 → 进行步骤3
   └─ 其他版本 → 安装兼容的Python

3. 手动重装mediapipe
   ├─ 成功 → 运行游戏
   └─ 失败 → 进行步骤4

4. 重建虚拟环境
   ├─ 成功 → 运行游戏
   └─ 失败 → 使用系统Python
```

---

**祝你游戏顺利！** 🎮✨
