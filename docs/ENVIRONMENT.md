# 环境记录

阶段 1 验收日期：2026-11-07

结论：通过。Python 3.10、CUDA PyTorch、YOLO11n、OpenCV、FastAPI、Vue3 和 Git 均已实际运行验证。

## 机器与系统

| 项目 | 值 |
|---|---|
| 操作系统 | Windows 11 Pro `10.0.26200`，64 位 |
| CPU 架构 | x86-64 |
| GPU | NVIDIA GeForce RTX 4090 Laptop GPU |
| 显存 | 16376 MiB |
| NVIDIA 驱动 | `616.56` |
| CUDA UMD | `13.4` |
| CUDA Toolkit / `nvcc` | 未安装；本阶段不需要 |

## 软件版本

| 软件 | 版本 |
|---|---|
| Python | `3.10.11` |
| pip | `26.3` |
| PyTorch | `2.14.1+cu130` |
| PyTorch CUDA 构建 | `13.0` |
| torchvision | `0.29.1+cu130` |
| Ultralytics | `8.4.204` |
| OpenCV | `5.0.0` |
| FastAPI | `0.162.0` |
| Uvicorn | `0.54.0` |
| pytest | `9.2.0` |
| Node.js | `24.20.0` LTS |
| npm | `11.19.0` |
| Vue | `3.5.45` |
| Vite | `6.4.5` |
| @vitejs/plugin-vue | `5.2.4` |
| Git | `2.56.0.windows.4` |

## 安装命令

```powershell
winget install --id Python.Python.3.10 -e --version 3.10.11 --scope user
winget install --id Git.Git -e --version 2.56.0.4 --scope user
winget install --id OpenJS.NodeJS.LTS -e --version 24.20.0 --scope user
```

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip==26.3
python -m pip install -r .\requirements-stage1.txt
```

## 版本锁定

```powershell
python -m pip install -r .\requirements.lock.txt --extra-index-url https://download.pytorch.org/whl/cu130
npm.cmd --prefix .\frontend list --depth=0
```

## 验收结果

| 验收项 | 实际结果 |
|---|---|
| Python 3.10 虚拟环境 | 通过，`3.10.11` |
| NVIDIA 驱动识别 | 通过，驱动 `616.56`，CUDA UMD `13.4` |
| PyTorch CUDA 构建 | 通过，`torch 2.14.1+cu130` |
| GPU 可用性 | 通过，`torch.cuda.is_available() == True` |
| GPU 实算 | 通过，RTX 4090 Laptop，compute capability `8.9`，512×512 矩阵乘法结果有效 |
| YOLO11n | 通过，5 个检测：`bus` × 1、`person` × 4 |
| OpenCV 视频 | 通过，640×360、24 FPS、48 帧全部解码 |
| FastAPI | 通过，`/api/health` 返回 `status: ok`，`/docs` 返回 HTTP 200 |
| API 自动化测试 | 通过，`2 passed` |
| Vue3 构建 | 通过，Vite `6.4.5` |
| Vue → FastAPI 代理 | 通过，页面 HTTP 200，代理 `/api/health` 返回 `ok` |
| Git | 已初始化，分支 `main` |

## 已知环境说明

- 本机未安装完整 CUDA Toolkit；PyTorch 的 CUDA 运行库随 wheel 提供，因此 `nvcc` 不是本阶段必需项。
- PowerShell 默认执行策略可能阻止 `npm.ps1`；使用 `npm.cmd`。
- 当前 `Starlette 1.7.0` 的进程内 `TestClient` 在本机 `Python 3.10 + httpx2 2.14.0` 组合下会阻塞；因此测试改用真实 Uvicorn 子进程，反而更接近实际启动方式。
- 首次安装 PyTorch 时官方源速度较慢，已使用分段下载后从本地 wheel 安装；安装结果与官方 CUDA wheel 一致。
