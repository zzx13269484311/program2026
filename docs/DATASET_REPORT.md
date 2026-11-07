# 数据集当前报告

生成日期：2026-11-07

## 1. 总体状态

| 项目 | 数量 |
|---|---:|
| 总图片 | 5,600 |
| 训练集 | 4,100 |
| 验证集 | 750 |
| 测试集 | 750 |
| 总标注框 | 13,852 |
| 验证错误 | 0 |
| 验证警告 | 18 |

验证命令：

```powershell
Set-Location "D:\program\weizhixianjue"
.\.venv\Scripts\python.exe .\scripts\validate_dataset.py
```

验证报告：

```text
vision\datasets\weizhixianjue\reports\validation.json
```

## 2. 标注框统计

| 数据集 | 图片 | 标注框 | person | goggles | smoke | fire | lab_coat | obstacle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 4,100 | 10,277 | 5,897 | 477 | 1,415 | 2,488 | 0 | 0 |
| val | 750 | 1,816 | 784 | 213 | 276 | 543 | 0 | 0 |
| test | 750 | 1,759 | 723 | 279 | 265 | 492 | 0 | 0 |

## 3. 含目标图片数量

| 数据集 | person | goggles | smoke | fire | lab_coat | obstacle |
|---|---:|---:|---:|---:|---:|---:|
| train | 2,294 | 347 | 1,268 | 962 | 0 | 0 |
| val | 306 | 166 | 242 | 198 | 0 | 0 |
| test | 283 | 191 | 238 | 185 | 0 | 0 |

## 4. 已使用来源

| 来源 | 使用类别 | 许可证 / 注意 |
|---|---|---|
| PPE_Detection_V1 | person、goggles | MIT |
| D-Fire | smoke、fire | Kaggle 元数据 CC0；原始图片保留来源条款 |

## 5. 当前缺口

### `lab_coat`

没有可靠公开数据：

- Open Images `Coat` 过滤后只有 11 张候选，且大部分不是实验室白大褂。
- 公开白大褂视频模型测试出现误报。
- 未把不可靠标签写入数据集。

### `obstacle`

公开障碍物数据主要是道路、铁路、自动驾驶或室外场景，和“实验室通道障碍物”语义不一致，暂未加入。

## 6. 训练判断

当前数据可以用于训练 `person`、`goggles`、`smoke`、`fire` 四类基线，但**不能认为已经完成六类模型**。

建议：

1. 先训练四类模型，确认数据和训练链路可用。
2. 补充可靠的 `lab_coat` 数据后，再加入第五类。
3. 补充实验室/室内通道的 `obstacle` 数据后，再加入第六类。

## 7. 数据质量说明

- 18 条警告均为训练集内部增强图片完全重复，不存在跨 train/val/test 的完全重复图片。
- `person` 与 `goggles` 主要来自施工 PPE 场景。
- `smoke` 与 `fire` 来自 D-Fire 的户外、工业或监控场景。
- 公开数据不能代替最终的真实摄像头测试集。
