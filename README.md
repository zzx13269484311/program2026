# 危知先觉

面向化工实验室危化品作业的动态风险闭环监护系统。

当前进度：**阶段 2：六类数据集与 YOLO11n 基线**（已导入 5,600 张公开图片；`lab_coat` 和 `obstacle` 数据仍待补齐）。

## 技术栈

| 模块 | 技术 |
|---|---|
| 语言 | Python 3.10.11 |
| 深度学习 | PyTorch + CUDA |
| 目标检测 | Ultralytics YOLO11n |
| 视频处理 | OpenCV |
| 后端 | FastAPI + Uvicorn |
| 前端 | Vue 3 + Vite |
| 版本控制 | Git |

## 已验证环境（2026-11-07）

| 项目 | 精确版本 / 配置 |
|---|---|
| 操作系统 | Windows 11 Pro `10.0.26200`，64 位 |
| GPU | NVIDIA GeForce RTX 4090 Laptop GPU，16 GB |
| NVIDIA 驱动 | `616.56` |
| CUDA UMD | `13.4` |
| Python | `3.10.11`，64 位 |
| pip | `26.3` |
| PyTorch | `2.14.1+cu130` |
| torchvision | `0.29.1+cu130` |
| PyTorch CUDA 构建 | `13.0` |
| Ultralytics | `8.4.204` |
| OpenCV | `5.0.0`（包版本 `5.0.0.93`） |
| FastAPI | `0.162.0` |
| Uvicorn | `0.54.0` |
| pytest | `9.2.0` |
| Node.js | `24.20.0` LTS |
| npm | `11.19.0` |
| Vue | `3.5.45` |
| Vite | `6.4.5` |
| Git | `2.56.0.windows.4` |

说明：本机没有安装完整 CUDA Toolkit，`nvcc` 不可用；PyTorch 的 CUDA 运行库由 wheel 提供，因此不影响本项目。未来如需自行编译 CUDA 扩展，再单独安装 CUDA Toolkit。

## 目录结构

```text
weizhixianjue/
├── backend/            # FastAPI 后端
├── vision/             # 检测、跟踪、数据集与权重
├── risk_engine/        # 时空风险规则引擎
├── permit/             # 动态作业许可与事件闭环
├── frontend/           # Vue 3 前端
├── simulation/         # 模拟视频、场景与证据
├── scripts/            # 环境与验收脚本
├── tests/              # 自动化测试
└── docs/               # 阶段验收与环境记录
```

## 阶段 2：数据集

数据集规范和六类标签说明：

```text
vision\datasets\weizhixianjue\README.md
```

创建数据集目录：

```powershell
.\.venv\Scripts\python.exe .\scripts\init_dataset.py
```

导入并标注数据后，验证图片、标签、类别和重复情况：

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_dataset.py
```

阶段 2 分阶段计划与验收标准：

```text
docs\STAGE2_PLAN.md
```

当前数据状态：

- 已导入 5,600 张公开图片。
- 已覆盖 `person`、`goggles`、`smoke`、`fire`。
- `lab_coat` 与 `obstacle` 尚无可靠公开数据。
- 数据统计见 `docs\DATASET_REPORT.md`。

## 首次启动

在 PowerShell 中进入项目目录：

```powershell
cd "D:\program\weizhixianjue"
.\.venv\Scripts\Activate.ps1
```

如果需要在另一台 Windows 机器上复现，先安装锁定版本的基础工具：

```powershell
winget install --id Python.Python.3.10 -e --version 3.10.11 --scope user
winget install --id Git.Git -e --version 2.56.0.4 --scope user
winget install --id OpenJS.NodeJS.LTS -e --version 24.20.0 --scope user
```

然后创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip==26.3
python -m pip install -r .\requirements-stage1.txt
```

若激活脚本被执行策略阻止，可仅对当前 PowerShell 窗口放行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

验证环境：

```powershell
python .\scripts\check_environment.py
python .\scripts\verify_opencv_video.py
python .\vision\verify_yolo.py
python -m pytest
```

`pytest` 会启动一个临时 Uvicorn 服务并检查真实 HTTP 响应。请让脚本使用默认的 `127.0.0.1` 端口范围。

启动后端：

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

访问 `http://127.0.0.1:8000/docs` 或 `http://127.0.0.1:8000/api/health`。

另开一个 PowerShell 窗口启动前端：

```powershell
cd "D:\program\weizhixianjue\frontend"
npm.cmd install
npm.cmd run dev
```

访问 `http://127.0.0.1:5173`。

前端生产构建检查：

```powershell
npm.cmd run build
```

> PowerShell 可能拦截 `npm.ps1`；使用 `npm.cmd` 可绕过该问题。

## 环境记录

- `docs/ENVIRONMENT.md`：机器、版本、安装命令和验收结果。
- `docs/STAGE1_ACCEPTANCE.md`：阶段 1 验收清单与证据。
- `docs/PROJECT_STRUCTURE.md`：完整目录结构和各目录职责。
- `requirements-stage1.txt`：直接依赖的精确版本。
- `requirements.lock.txt`：完整 Python 环境锁定。
- `frontend/package-lock.json`：前端完整依赖锁定。

## 边界

- 仅覆盖化工实验室危化品取用与加热作业。
- 使用模拟场景和带标签的安全道具，不使用真实危险化学品或真实火焰。
- 风险等级由规则引擎判定；大模型只生成解释和整改建议。
