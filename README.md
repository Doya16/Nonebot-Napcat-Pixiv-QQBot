# 写出完整的 README.md 为纯文本文件方便下载使用

readme_full_text = """
# 🎨 Nonebot-Napcat-pixivAPI 插件

基于 [NoneBot2](https://v2.nonebot.dev/) 和 [Napcat](https://github.com/kaedejun/Napcat) 的 Pixiv 插图获取插件。  
支持通过 QQ 聊天命令获取 Pixiv 热门插画、关键词搜索、用户插图，并带有图片过滤和定时撤回等功能。

## 功能特性

- 支持关键词搜索和 Pixiv 排行榜（日/周/月）
- 支持指定用户插图获取（支持随机或最新模式）
- 自动过滤 R-18 / 血腥 / 暴力 等敏感内容
- 插图自动缓存并使用 Napcat 临时目录发送
- 支持自动撤回（默认 60 秒，仅群聊）
- 每人请求冷却时间限制（默认 20 秒）

## 安装方式

1. 克隆本仓库：

   ```bash
   git clone https://github.com/Doya16/Nonebot-Napcat-pixivAPI.git

2. 安装依赖：

   ```bash
   pip install pixivpy3 httpx

3. 将 pixiv_plugin.py 注册为 NoneBot 插件，或整理为标准插件目录。

## Pixiv Refresh Token 获取方法

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

## Refresh Token 配置方式
  你可以选择以下任意一种方式配置 token：

  ## 方法一：直接在插件中设置（简单但不推荐）
  在 pixiv_plugin.py 文件中找到：
    
    ```bash
    REFRESH_TOKEN = "你的 refresh_token"

  ## 方法二：使用 .env 文件（推荐）
  在项目根目录创建 .env 文件并添加内容：
  
    ```bash
    PIXIV_REFRESH_TOKEN=你的 refresh_token

  并在代码中引用：
  
      ```bash
      import os
      REFRESH_TOKEN = os.getenv("PIXIV_REFRESH_TOKEN")
  
