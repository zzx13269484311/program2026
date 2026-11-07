# 阶段 2 计划：六类数据集与 YOLO11n 基线

## 1. 阶段目标

完成六类目标数据集的整理、标注、验证和 YOLO11n 基线训练。阶段 2 只解决“模型能不能检测六类目标”，不同时开发风险规则、动态许可和三维看板。

六类目标：

```text
person
lab_coat
goggles
obstacle
smoke
fire
```

## 2. 分阶段验收

### 2A 数据规范与目录

- [x] 冻结六类标签。
- [x] 建立数据集目录。
- [x] 建立 `data.yaml`。
- [x] 编写标注规范。
- [x] 编写目录初始化脚本。
- [x] 编写数据验证脚本。

### 2B 数据采集与导入

- [x] 收集公开 PPE 数据。
- [x] 收集公开 fire/smoke 数据。
- [x] 转换为当前六类 YOLO 目录格式。
- [ ] 采集 300 到 500 张模拟实验室图片。
- [ ] 补充弱光、遮挡、反光和负样本。
- [ ] 补齐可靠的 `lab_coat` 数据。
- [ ] 补齐室内通道 `obstacle` 数据。
- [x] 按视频/来源划分训练集、验证集和测试集。
- [x] 完成当前公开数据验证。

通过标准：

- `validate_dataset.py` 无错误退出。
- 图片和标签一一对应。
- 类别 ID 和坐标全部合法。
- 训练集、验证集和测试集之间没有重复图片。

### 2C YOLO11n 基线训练

- [ ] 使用预训练权重启动训练。
- [ ] 固定图像尺寸、batch、epoch 和随机种子。
- [ ] 保存训练配置和日志。
- [ ] 输出最佳权重和最后权重。

### 2D 模型评估

- [ ] 计算 mAP50 和 mAP50-95。
- [ ] 输出各类别指标。
- [ ] 输出混淆矩阵。
- [ ] 检查误报和漏报样本。
- [ ] 形成阶段 2 指标报告。

## 3. 当前状态

当前完成：

- **2A 数据规范与目录**。
- PPE 数据转换：3,400 张图片。
- D-Fire 数据转换：2,200 张图片。
- 当前合计 5,600 张图片，验证无错误。

当前阻塞项：

- `lab_coat` 没有可靠公开数据。
- `obstacle` 没有与实验室通道语义一致的公开数据。

详见 `docs/DATASET_REPORT.md`。

## 4. 立即执行

```powershell
Set-Location "D:\program\weizhixianjue"
.\.venv\Scripts\python.exe .\scripts\init_dataset.py
```

数据导入并标注后执行：

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_dataset.py
```
