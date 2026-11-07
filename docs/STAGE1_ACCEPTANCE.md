# 阶段 1 验收清单

项目：危知先觉——面向化工实验室危化品作业的动态风险闭环监护系统

本阶段只验证工程基础，不训练模型，不实现风险引擎。

## 验收项

- [x] 1. Python 为 3.10.x，且项目使用独立 `.venv`。
- [x] 2. NVIDIA 驱动、CUDA 版本与 PyTorch 构建互相兼容。
- [x] 3. PyTorch 能识别 GPU，并完成一次真实 GPU 矩阵运算。
- [x] 4. Ultralytics 能加载 `yolo11n.pt` 并完成一张图片的检测。
- [x] 5. OpenCV 能创建、读取并解码本地测试视频。
- [x] 6. FastAPI 能启动，`/api/health` 返回 `status: ok`。
- [x] 7. 自动化 API 测试通过。
- [x] 8. Vue3 页面能启动，并成功请求 FastAPI。
- [x] 9. Git 仓库和项目目录骨架存在。
- [x] 10. `docs/ENVIRONMENT.md` 已记录精确版本与复现命令。

## 最终验收结果（2026-11-07）

| 项目 | 证据 |
|---|---|
| Python | `3.10.11`，项目 `.venv` |
| GPU / CUDA | RTX 4090 Laptop，驱动 `616.56`，CUDA UMD `13.4`，PyTorch CUDA `13.0` |
| GPU 实算 | 512×512 矩阵乘法成功，`cuda.status = pass` |
| YOLO11n | 5 个检测：`bus` × 1、`person` × 4 |
| OpenCV | 640×360、24 FPS、48 帧全部解码 |
| FastAPI | `/api/health` 返回 `ok`，`/docs` 返回 HTTP 200 |
| API 测试 | `2 passed` |
| 前端 | Vue 构建通过；页面 HTTP 200；Vite 代理 `/api/health` 返回 `ok` |
| Git | 仓库已初始化，分支 `main` |

## 必跑命令

```powershell
.\.venv\Scripts\Activate.ps1
python .\scripts\check_environment.py
python .\scripts\verify_opencv_video.py
python .\vision\verify_yolo.py
python -m pytest
```

## 通过标准

- 所有脚本退出码为 `0`。
- 环境脚本输出中 `cuda.status` 为 `pass`。
- YOLO 脚本输出 `PASS`，且至少检测到 1 个目标。
- OpenCV 脚本至少解码 1 帧。
- API 测试全部通过。
- 浏览器打开前端后，页面显示后端状态为 `ok`。

任何一步失败都应停止，不带病进入下一阶段。
