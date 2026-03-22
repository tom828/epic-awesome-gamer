# 🎮 Epic Kiosk - 自动驾驶领取系统

![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)
![Python](https://img.shields.io/badge/Python-3.12-yellow?logo=python)
![Status](https://img.shields.io/badge/Status-Stable-green)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)

**Epic Kiosk** 是一个基于 Docker 的全自动 Epic Games 免费游戏领取工具。支持多账号托管、智能验证码识别、错峰调度，一键部署即可使用。

> 🌐 **公益站点**：[https://epic.910501.xyz/](https://epic.910501.xyz/) - 免费体验，无需自建

<p align="center">
  <img src="assets/image_2.png" alt="Epic Kiosk Dashboard" width="100%" style="max-width: 800px;">
</p>

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🚀 **自动驾驶** | 一键启动，自动完成登录、验证码、游戏领取 |
| 🔐 **Cookie 托管** | 首次登录后保存 Cookie，后续无需重复登录 |
| 🤖 **AI 验证码** | 使用 Qwen 视觉模型智能识别 hCaptcha |
| 🚦 **错峰调度** | 智能随机延迟，避免多账号同时触发风控 |
| 🛡️ **防滥用保护** | IP 限流 + 恶意账号检测 |
| 🐳 **一键部署** | Docker Compose 本地编译，支持 x86/ARM |

---

## 🚀 快速开始

### 方式一：Linux 一键部署（推荐）

适用于：云服务器、VPS、Linux 主机

```bash
curl -fsSL https://raw.githubusercontent.com/10000ge10000/epic-kiosk/main/install.sh | bash
```

**脚本功能**：
- ✅ 自动检测系统架构（x86_64 / ARM64）
- ✅ 自动安装 Docker 和 Docker Compose
- ✅ 交互式引导获取 API Key
- ✅ 自动克隆项目并本地编译启动

**首次部署约需 5-10 分钟**（下载依赖 + 编译镜像）

---

### 方式二：手动部署

适用于：已有 Docker 环境的 Linux / macOS / Windows 主机

#### 步骤

**1. 克隆项目**

```bash
git clone https://github.com/10000ge10000/epic-kiosk.git
cd epic-kiosk
```

**2. 修改配置**

方式一（推荐）：创建 `.env` 文件

```bash
cp .env.example .env
# 编辑 .env 文件，填写你的 API Key
```

方式二：直接修改 `docker-compose.yml` 文件中的 API Key

```yaml
- SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 替换为你的 Key
```

**3. 启动项目**

```bash
docker compose up -d --build
```

**首次启动约需 5-10 分钟**（下载依赖 + 编译镜像）

---

#### ⚠️ 部署前必读

1. **修改 API Key**：获取地址 [https://cloud.siliconflow.cn/i/OVI2n57p](https://cloud.siliconflow.cn/i/OVI2n57p)（注册送 ¥16 代金券）

2. **端口冲突**：默认端口 `18000`，如需修改请编辑 `docker-compose.yml` 第 51 行

3. **部署完成后访问**：`http://服务器IP:18000`

---

## 📖 使用说明

### 添加账号
1. 输入 Epic 邮箱和密码
2. 点击「启动引擎」
3. 系统自动处理登录和验证码

### 查看资产
- 点击「资产清单」Tab 查看已领取游戏
- 点击游戏封面跳转 Epic 商店

### 删除账号
- 输入密码后点击红色删除按钮
- 系统将彻底清除数据库和本地数据

---

## ⚙️ 配置说明

### 🤖 AI 模型配置（已优化）

| 类型 | 主模型 | 备用模型 | 用途 |
|------|--------|----------|------|
| 验证码 | Qwen3-VL-32B-Instruct | Qwen3-VL-235B-A22B-Instruct | hCaptcha 图像识别 |
| 主力 | Qwen2.5-7B-Instruct（免费） | Qwen2.5-72B-Instruct | 文本任务 |

**智能切换机制**：
- 验证码连续失败 2 次后，自动切换到备用模型（235B 参数，识别能力更强）
- API 调用异常时自动切换备用模型
- 成功后自动重置，优先使用性价比更高的主模型

### 💰 费用估算

- 验证码主模型（32B）：¥12/百万 tokens
- 验证码备用模型（235B）：¥7/百万 tokens（按 A22B 模式计费）
- 主力模型：**免费**
- ¥16 代金券 ≈ **1000+ 次领取任务**

---

## 📁 项目结构

```
epic-kiosk/
├── app/                    # 核心代码
│   ├── main.py             # FastAPI 后端
│   ├── worker.py           # 任务调度器
│   ├── deploy.py           # 浏览器自动化
│   └── services/           # 业务逻辑
├── templates/              # 前端页面
├── data/                   # 持久化数据
│   ├── images/             # 游戏海报
│   ├── user_data/          # 用户 Cookie
│   └── logs/               # 日志文件
├── docker-compose.yml      # 容器编排
├── install.sh              # 一键部署脚本
├── Dockerfile              # Web 镜像
└── Dockerfile.worker       # Worker 镜像
```

---

## 🔒 安全机制

### IP 保护
- 1 分钟内最多 3 次请求
- 超限后临时封禁 1 小时
- 同一 IP 提交 >5 个不同账号 → 永久封禁

### 账号保护
- 同一邮箱任务互斥
- 已存储账号需验证密码
- 自动清理浏览器缓存（~2MB/账号）

---

## 🐛 故障排查

### 常见问题

**Q: 按钮显示「Requires Base Game」？**
A: 该游戏需要先拥有基础游戏，属于 DLC，跳过即可。

**Q: 验证码一直失败？**
A: 检查 API Key 是否正确，余额是否充足。

**Q: 日志显示「游戏已在库中」？**
A: 该账号已领取过此游戏，正常现象。

**Q: 服务器 IP 被 Cloudflare 拦截？**
A: 数据中心 IP 可能被 Cloudflare 标记，建议配置住宅代理或使用公益站点。

### 查看日志

```bash
# Worker 日志（实时）
docker logs epic-worker --tail 50

# 日志文件（按日期分类）
ls data/logs/
# runtime-2026-03-22.log  error-2026-03-22.log

# 查看当天运行时日志
cat data/logs/runtime-$(date +%Y-%m-%d).log | tail -50

# 查看当天错误日志
cat data/logs/error-$(date +%Y-%m-%d).log
```

### 重新构建

修改代码后需要重新构建镜像：

```bash
# 重新构建 Worker
docker compose build worker
docker compose up -d worker

# 重新构建所有服务
docker compose build --no-cache
docker compose up -d
```

---

## 📚 相关文档

- [API Key 获取指南](docs/API_KEY_GUIDE.md) - SiliconFlow 注册教程
- [快速开始指南](docs/QUICKSTART.md) - 详细部署步骤
- [模型配置说明](docs/MODEL_CONFIG.md) - 模型架构说明

---

## 🤝 致谢

- 原项目：[QIN2DIM/epic-awesome-gamer](https://github.com/QIN2DIM/epic-awesome-gamer)
- AI 服务：[SiliconFlow](https://cloud.siliconflow.cn/i/OVI2n57p)

---

## ⚠️ 免责声明

本项目仅供学习和技术研究使用。请合理使用，遵守 Epic Games 服务条款。开发者不对因使用本项目导致的任何损失承担责任。

---

*Created by [一万](https://github.com/10000ge10000) | 公益站点：[epic.910501.xyz](https://epic.910501.xyz/)*
