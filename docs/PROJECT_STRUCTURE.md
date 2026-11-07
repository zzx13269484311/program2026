# 项目结构说明

项目根目录：`D:\program\weizhixianjue`

当前阶段：阶段 1 已完成；阶段 2（六类数据集与 YOLO11n 基线）正在进行。

## 顶层结构

```text
D:\program\weizhixianjue\
├── .venv\                  # Python 3.10 本地虚拟环境（不提交 Git）
├── .git\                   # Git 仓库数据
├── backend\                # FastAPI 后端
├── vision\                 # 视觉检测、权重、数据集和验收脚本
├── risk_engine\            # 时空风险规则引擎（阶段 4 实现）
├── permit\                 # 动态作业许可与事件闭环（阶段 5 实现）
├── frontend\               # Vue 3 + Vite 前端
├── simulation\             # 模拟视频、场景、证据和检测输出
├── scripts\                # 环境检查和 OpenCV 视频验收脚本
├── tests\                  # 自动化测试
├── docs\                   # 环境、验收和结构文档
├── work\                   # 本地临时文件、日志和离线安装包（不提交 Git）
├── .gitignore              # Git 忽略规则
├── .gitattributes          # 跨平台换行规范
├── .python-version         # Python 3.10.11
├── pytest.ini              # pytest 测试目录
├── README.md               # 项目入口说明
├── requirements-data.txt   # 数据下载与转换工具
├── requirements-stage1.txt # 阶段 1 直接依赖
└── requirements.lock.txt   # 完整 Python 依赖锁定
```

## 主要目录

### `backend\`

```text
backend\
├── __init__.py
├── main.py                 # FastAPI 应用、CORS、健康检查接口
├── api\                    # 后续 HTTP 路由
├── services\               # 后续业务服务
└── database\               # 后续 SQLite 数据访问
```

当前可用接口：

- `GET /`：服务基本信息。
- `GET /api/health`：返回 `status: ok`。
- `GET /docs`：FastAPI 自动接口文档。

### `vision\`

```text
vision\
├── verify_yolo.py          # YOLO11n 加载、图片推理和验收
├── datasets\               # 六类目标数据集
│   └── weizhixianjue\
│       ├── data.yaml       # 六类标签和训练/验证/测试路径
│       ├── README.md       # 标注规范和数据划分规则
│       ├── raw\            # 原始图片
│       ├── images\         # train / val / test 图片
│       ├── labels\         # train / val / test YOLO 标签
│       └── reports\        # 数据验证报告
└── weights\                # yolo11n.pt 等模型权重（不提交 Git）
```

阶段 1 已验证 `yolo11n.pt` 能完成图片检测。阶段 2 正在进行六类数据整理，并将在验证通过后加入训练和评估代码。

### `frontend\`

```text
frontend\
├── src\
│   ├── App.vue             # 阶段 1 页面和后端状态检查
│   ├── main.js             # Vue 入口
│   └── style.css           # 页面样式
├── index.html              # Vite HTML 入口
├── vite.config.js          # 5173 端口和 /api 代理到 FastAPI
├── package.json            # 前端脚本和直接依赖
├── package-lock.json       # 前端完整依赖锁定
└── node_modules\           # 本地 npm 依赖（不提交 Git）
```

启动后访问 `http://127.0.0.1:5173`。页面通过 Vite 代理请求 `http://127.0.0.1:8000/api/health`。

### `risk_engine\`

预留阶段 4 的 ROI、持续时间、多事件共现、风险评分和事件生成代码。

### `permit\`

预留阶段 5 的作业申请、条件核验、签发、监护、撤销、整改和复核流程。

### `simulation\`

```text
simulation\
├── videos\                 # OpenCV 测试视频和后续模拟场景视频
├── scenarios\              # 脚本化演示场景
└── evidence\               # 截图、检测结果和后续事件证据
```

阶段 1 的证据图片位于 `simulation\evidence\yolo_stage1\stage1_bus.jpg`。

### `scripts\`

- `check_environment.py`：检查 Python、软件版本、CUDA 和 GPU 实算。
- `init_dataset.py`：创建数据集目录并校验六类契约。
- `convert_ppe.py`：PPE 数据转换和类别映射。
- `convert_dfire.py`：D-Fire 数据转换、框裁剪和负样本处理。
- `fetch_openimages_labcoat.py`：公开 lab_coat 候选尝试脚本。
- `preview_dataset.py`：生成带检测框的数据预览。
- `validate_dataset.py`：图片、标签、类别、坐标和重复项验证。
- `verify_opencv_video.py`：生成并读取本地 MP4，验证 OpenCV 视频链路。

### `tests\`

- `test_api.py`：启动真实 Uvicorn 子进程，检查 `/` 和 `/api/health`。

### `docs\`

- `ENVIRONMENT.md`：机器、精确版本、安装命令和验收结果。
- `STAGE1_ACCEPTANCE.md`：阶段 1 验收清单与证据。
- `STAGE2_PLAN.md`：阶段 2 计划和当前阻塞项。
- `DATASET_REPORT.md`：当前数据量、类别分布和缺失类别。
- `DATASET_SOURCES.md`：公开数据来源、许可证和处理记录。
- `PROJECT_STRUCTURE.md`：本结构说明。

### `work\`

仅用于本机临时数据，不进入 Git：

- 离线 PyTorch wheel。
- 公开数据压缩包和解压后的原始数据。
- 数据转换清单、预览和日志。
- Uvicorn、Vite 和前端联调日志。
- 临时调试文件。

## 不进入 Git 的内容

- `.venv\`
- `frontend\node_modules\`
- `frontend\dist\`
- `vision\weights\*.pt`
- `simulation\videos\*`
- `simulation\evidence\*`
- `work\`
- 缓存、日志和环境变量文件

这些文件仍保留在 `D:\program\weizhixianjue`，只是不提交到 Git。

## 阶段 1 启动入口

```powershell
cd "D:\program\weizhixianjue"
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd "D:\program\weizhixianjue\frontend"
npm.cmd run dev
```
