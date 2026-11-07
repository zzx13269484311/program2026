# 公开数据来源与处理记录

更新时间：2026-11-07

## 1. 数据来源与处理记录

### 1.1 PPE_Detection_V1

- Kaggle：https://www.kaggle.com/datasets/beyzakucuk/ppe-detection-v1
- 原始来源：Roboflow `ppe-6-classes-ntld9` v6
- 许可证：MIT
- 原始规模：17,264 张图片，6 类：
  - `boots`
  - `gloves`
  - `goggles`
  - `helmet`
  - `person`
  - `vest`
- 实际标注：分割多边形格式，转换为检测外接框后使用。
- 本项目使用：
  - `person`
  - `goggles`
- 实际导入：3,400 张图片。
  - train：2,500 张，person 5,897 框，goggles 477 框。
  - val：450 张，person 784 框，goggles 213 框。
  - test：450 张，person 723 框，goggles 279 框。
- 处理脚本：`scripts/convert_ppe.py`
- 说明：原始数据含增强图片；同一来源图片可能在训练集中出现多次，但未发现跨训练/验证/测试集的完全重复。

### 1.2 D-Fire

- Kaggle：https://www.kaggle.com/datasets/sayedgamal99/smoke-fire-detection-yolo
- 原始项目：https://github.com/gaia-solutions-on-demand/DFireDataset
- 许可证说明：Kaggle 元数据为 CC0；原始 D-Fire 图片仍受其来源条款约束，使用时应引用原论文。
- 原始规模：超过 21,000 张图片，YOLO 框格式。
- 原始类别：
  - `0 smoke`
  - `1 fire`
- 本项目使用：
  - `smoke` → 项目类别 4
  - `fire` → 项目类别 5
  - 另选少量无目标图片作为负样本。
- 实际导入：2,200 张图片。
  - train：1,600 张，smoke 1,415 框，fire 2,488 框，负样本 192 张。
  - val：300 张，smoke 276 框，fire 543 框，负样本 36 张。
  - test：300 张，smoke 265 框，fire 492 框，负样本 36 张。
- 处理脚本：`scripts/convert_dfire.py`

### 1.3 Open Images Coat 子集（尝试后未采用）

- 数据说明：https://storage.googleapis.com/openimages/web/index.html
- 标注数据：Open Images V5 validation/test bbox annotations。
- 使用类别：
  - `Coat`：`/m/01xygc`
  - `Person`：`/m/01g317`
- 目的：尝试作为 `lab_coat` 的公开真实数据替代来源。
- 处理方法：
  1. 选择同时含 `Coat` 和 `Person` 的图片。
  2. 要求 Coat 框与 Person 框重叠。
  3. 计算 Coat 框内低饱和度、高亮度像素比例。
  4. 保留白色比例超过阈值的候选。
  5. 生成预览图供人工复核。
- 处理脚本：`scripts/fetch_openimages_labcoat.py`
- 实际结果：
  - validation/test 中同时含 `Coat` 和 `Person` 的图片只有 77 张。
  - 白色比例过滤后只剩 11 张候选。
  - 人工查看 contact sheet 后，大部分是时装外套、白大衣或衣物局部，不是实验室白大褂。
  - 因此没有把该子集加入训练数据。
- 结论：Open Images `Coat` 不能可靠替代 `lab_coat`。

## 2. 尝试但未直接采用的数据

### 2.1 CPPE-5

- 地址：https://github.com/Rishit-dagli/CPPE-Dataset
- 许可证：Apache-2.0
- 类别：`Coverall`、`Face_Shield`、`Gloves`、`Goggles`、`Mask`
- 未采用原因：PPE_Detection_V1 已提供更多 `Goggles` 和 `Person` 数据；`Coverall` 与 `lab_coat` 语义不同，不能直接混用。

### 2.2 公开白大褂视频和模型

- 视频：https://github.com/susiur/Labcoat-detection
- 模型：https://github.com/seymaakorkmaz/Lab-Coat-Detection-Model
- 视频许可证：MIT。
- 模型仓库没有明确许可证，且模型为 YOLOv5 格式，不能直接由当前 YOLO11 运行时加载。
- 测试结果：
  - 模型可以加载，类别中包含 `lab-coat`。
  - 在公开演示视频的 10 个采样帧中只检测到 1 个低置信度结果。
  - 查看该帧后确认，人物穿的是深色普通上衣，不是实验室白大褂，属于误报。
- 结论：没有作为最终训练数据来源，也没有把误报标签写入数据集。

### 2.3 其他尝试

- 浏览器搜索 Roboflow 公共数据集：当前 Work 环境禁用了本地浏览器控制，无法直接检索和登录导出。
- 图片生成工具：当前会话未提供可用的内置图片生成工具；CLI 备用方案需要额外的 API 凭据，未使用。

### 2.3 其他 PPE 数据

部分 Kaggle/Roboflow PPE 数据只有头盔、反光背心或口罩，缺少护目镜或实验室服；未直接混入，避免类别语义不一致。

## 3. 当前缺口

- `lab_coat`：目前依靠 Open Images 白色 Coat 候选，仍需人工复核。
- `obstacle`：公开数据一般为道路、铁路或室外障碍物，与实验室通道语义不一致，暂未直接采用。
- 最终测试集：公开数据不能替代真实摄像头场景，后续仍应补充少量手机拍摄的安全道具场景。

## 4. 数据完整性要求

- 图片和标签必须同名。
- 负样本必须有空 `.txt` 文件。
- 不同来源的标签必须映射到项目六类 ID。
- 训练、验证、测试之间不得出现完全重复图片。
- 所有数据在使用前必须通过：

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_dataset.py
```
