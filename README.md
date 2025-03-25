# 写出完整的 README.md 为纯文本文件方便下载使用

readme_full_text = """
# 🎨 Nonebot-Napcat-pixivAPI 插件

基于 [NoneBot2](https://v2.nonebot.dev/) 和 [Napcat]([https://github.com/kaedejun/Napcat](https://github.com/NapNeko/NapCatQQ)) 的 Pixiv 插图获取插件。  
支持通过 QQ 聊天命令获取 Pixiv 热门插画、关键词搜索、用户插图，并带有图片过滤和定时撤回等功能。

# 一、 功能特性

- 支持关键词搜索和 Pixiv 排行榜（日/周/月）
- 支持指定用户插图获取（支持随机或最新模式）
- 自动过滤 R-18 / 血腥 / 暴力 等敏感内容
- 插图自动缓存并使用 Napcat 临时目录发送
- 支持自动撤回（默认 60 秒，仅群聊）
- 每人请求冷却时间限制（默认 20 秒）

# 二、 安装方式

1. 克隆本仓库：

   ```bash
   git clone https://github.com/Doya16/Nonebot-Napcat-pixivAPI.git

2. 安装依赖：

   ```bash
   pip install pixivpy3 httpx

3. 将 pixiv_plugin.py 注册为 NoneBot 插件，或整理为标准插件目录。

# 三、 Pixiv Refresh Token 获取方法

插件需要 Pixiv 的 refresh_token 进行认证。
## 快速获取步骤：
  1. 运行授权脚本

      ```bash
      python pixiv_auth.py login
      
  2. 浏览器登录 Pixiv 后，在开发者工具 Network 中搜索 callback?，找到 URL 中的 code=XXXXXX
  3. 将 code 粘贴回终端，即可获得：

     ```bash
     access_token: XXXXXXXXXX
     refresh_token: XXXXXXXXXX
  详细图文步骤请参阅 pixiv授权码获取教程.txt。

# 四、 Refresh Token 配置方式
  你可以选择以下任意一种方式配置 token：

  ### 方法一：直接在插件中设置（简单但不推荐）
  在 pixiv_plugin.py 文件中找到：
   ```bash
       REFRESH_TOKEN = "你的 refresh_token"
   ```

### 方法二：使用 .env 文件（推荐）
  在项目根目录创建 .env 文件并添加内容：
  
   ```bash
    PIXIV_REFRESH_TOKEN=你的 refresh_token
   ```
并在代码中引用：  
   ```bash
      import os
      REFRESH_TOKEN = os.getenv("PIXIV_REFRESH_TOKEN")
   ```

  ### `.pixiv r` 获取插图

| 命令 | 功能说明 |
|------|----------|
| `.pixiv r` | 获取 Pixiv 日榜中 1 张图（默认） |
| `.pixiv r 遐蝶 3` | 获取关键词“遐蝶”的插图 3 张 |
| `.pixiv r 遐蝶 week 2` | 获取“遐蝶”在周榜中的插图 |
| `.pixiv r month` | 获取月榜随机插图 |

### `.pixiv u` 获取用户作品

| 命令 | 功能说明 |
|------|----------|
| `.pixiv u Nhimm` | 获取用户 Nhimm 的最新作品 |
| `.pixiv u Nhimm random 2` | 随机获取 Nhimm 的 2 张作品 |
| `.pixiv u Nhimm latest 3` | 获取最新 3 张作品 |

## 其他说明

- 插图下载目录：`cache/pixiv_download/`
- 临时发送目录：`NAPCAT_TEMP_DIR`（需手动设置路径）
- 插图发送后将在群聊中 60 秒自动撤回
- 插件自动跳过敏感内容（关键词过滤）

## 开源协议

MIT License


## 致谢

本项目受以下优秀开源项目启发并构建：

- [NoneBot2](https://github.com/nonebot/nonebot2)：现代 Python 异步聊天机器人框架
- [PixivPy](https://github.com/upbit/pixivpy)：Pixiv 非官方 API 封装库
- [Napcat]([https://github.com/kaedejun/Napcat](https://github.com/NapNeko/NapCatQQ))：轻量化、易部署的 QQ 机器人框架
- [httpx](https://www.python-httpx.org/)：现代化异步 HTTP 客户端
- 本插件由 [@Doya16](https://github.com/Doya16) 开发和维护

