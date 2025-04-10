import os
import time
import random
import json
import asyncio
import httpx
import shutil
import uuid

from nonebot import on_message, get_driver
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment, PrivateMessageEvent
from pixivpy3 import AppPixivAPI

# 配置
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(PLUGIN_DIR, "cache", "pixiv_token.json")
CACHE_DIR = os.path.join(PLUGIN_DIR, "cache", "pixiv_download")
NAPCAT_TEMP_DIR = r"D:\QQFiles\NapCat\temp"

RECALL_SECONDS = 45  # 自动撤回时间
COOLDOWN_SECONDS = 45  # 冷却时间（秒）
cooldowns = {}

os.makedirs(CACHE_DIR, exist_ok=True)

# access_token 读取必须配合群聊插件使用
# 本私聊插件只是阅读群聊插件生成的access token
def get_access_token():
    if not os.path.exists(TOKEN_PATH):
        print("[私聊插件] ❌ 暂未找到 access_token 文件")
        return None
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("access_token")
    except Exception as e:
        print(f"[私聊插件] ❌ 读取 access_token 失败: {e}")
        return None

# Pixiv API 初始化
api = AppPixivAPI()
access_token = get_access_token()
if access_token:
    api.access_token = access_token
    print("[私聊插件] ✅ access_token 加载成功")

# 通用冷却检查函数
async def check_cooldown(bot: Bot, event: MessageEvent) -> bool:
    uid = str(event.user_id)
    now = time.time()
    if uid in cooldowns and now - cooldowns[uid] < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - cooldowns[uid]))
        await bot.send(event, f"🕓 阁下的请求还在冷却中，请等待 {remaining} 秒后再试。")
        return False
    cooldowns[uid] = now
    return True

def refresh_token_from_file():
    token = get_access_token()
    if token:
        api.access_token = token


# 帮助指令
def help_rule(event: MessageEvent):
    return event.get_plaintext().strip().lower() == ".pixiv help"

def help_private_rule(event: MessageEvent) -> bool:
    return isinstance(event, PrivateMessageEvent) and help_rule(event)

pixiv_help = on_message(rule=help_private_rule, priority=1, block=True)

# 使用说明文案嵌入
@pixiv_help.handle()
async def _(bot: Bot, event: MessageEvent):
    if not await check_cooldown(bot, event):
        return
    await bot.send(event, MessageSegment.text(
        "🎨 私聊 Pixiv 插图帮助：\n"
        ".pixiv id [作品ID]\n"
        ".pixiv r [关键词] [数量]\n"
        ".pixiv r [关键词] [day/week/month] [数量]\n"
        ".pixiv u [用户名] [random/latest] [数量]\n"
        ".pixiv hot [关键词] [数量]\n"
        ".pixiv r18 [关键词] [数量]\n"
        ".pixiv r18 [关键词] [day/week/month] [数量]\n"
        ".pixiv r18开头的命令只会返回tag中带有 R18 的图片\n"
        "\n已开启 R-18 显示，但不支持多图发送。"
    ))

# .pixiv id命令的实现
def id_rule(event: MessageEvent):
    return event.get_plaintext().strip().lower().startswith(".pixiv id")

def id_private_rule(event: MessageEvent) -> bool:
    return isinstance(event, PrivateMessageEvent) and id_rule(event)

pixiv_id = on_message(rule=id_private_rule, priority=1, block=True)

@pixiv_id.handle()
async def _(bot: Bot, event: MessageEvent):
    refresh_token_from_file()
    if not await check_cooldown(bot, event):
        return
    text = event.get_plaintext().strip()
    parts = text.split()
    if len(parts) < 3 or not parts[2].isdigit():
        await bot.send(event, "❗ 格式应为 .pixiv id [作品ID]")
        return
    illust_id = int(parts[2])
    try:
        illust = api.illust_detail(illust_id).illust
        if not illust:
            await bot.send(event, f"⚠️ 未找到 ID 为 {illust_id} 的插图")
            return
        await send_images(bot, event, [illust])
    except Exception as e:
        await bot.send(event, f"❌ 获取失败: {e}")

# .pixiv r18命令的实现
def r18_rule(event: MessageEvent):
    return event.get_plaintext().strip().lower().startswith(".pixiv r18")

def r18_private_rule(event: MessageEvent) -> bool:
    return isinstance(event, PrivateMessageEvent) and r18_rule(event)

pixiv_r18 = on_message(rule=r18_private_rule, priority=1, block=True)

@pixiv_r18.handle()
async def _(bot: Bot, event: MessageEvent):
    refresh_token_from_file()
    if not await check_cooldown(bot, event):
        return

    text = event.get_plaintext().strip()
    parts = text.split()
    if len(parts) < 3:
        await bot.send(event, "❗ 格式应为 .pixiv r18 [关键词] [数量]")
        return

    tag = parts[2]
    num = 1
    for part in parts[3:]:
        if part.isdigit():
            num = min(int(part), 6)

    illusts = []
    seen_ids = set()
    max_pages = 10
    pages = 0

    try:
        res = api.search_illust(tag)
        while res and res.illusts and pages < max_pages:
            for i in res.illusts:
                if i.id in seen_ids:
                    continue
                if i.tags and any(tag.name.lower() == "r-18" for tag in i.tags):
                    illusts.append(i)
                    seen_ids.add(i.id)

            pages += 1
            if res.next_url:
                next_qs = api.parse_qs(res.next_url)
                res = api.search_illust(**next_qs)
            else:
                break

        if not illusts:
            await bot.send(event, "⚠️ 未找到 R-18 插图")
            return

        selected = random.sample(illusts, min(num, len(illusts)))
        await send_images(bot, event, selected)

    except Exception as e:
        await bot.send(event, f"❌ 获取 R-18 插图失败：{e}")

# 图片下载与发送（含自动撤回）
async def send_images(bot: Bot, event: MessageEvent, illusts: list):
    user_dir = os.path.join(CACHE_DIR, str(event.user_id))
    os.makedirs(user_dir, exist_ok=True)

    messages = []
    message_ids = []
    sent_temp_paths = []

    async with httpx.AsyncClient() as client:
        for illust in illusts:
            url = (
                illust.meta_single_page.get("original_image_url")
                if illust.meta_single_page else None
            )
            if not url and illust.meta_pages:
                url = illust.meta_pages[0].image_urls.get("original")
            if not url and illust.image_urls:
                url = (
                    illust.image_urls.get("original")
                    or illust.image_urls.get("large")
                    or illust.image_urls.get("medium")
                )
            if not url:
                continue

            try:
                r = await client.get(url, headers={"Referer": "https://www.pixiv.net/"}, timeout=15)
                ext = ".jpg" if "jpeg" in r.headers.get("Content-Type", "") else ".png"
                filename = f"{illust.id}{ext}"
                path = os.path.join(user_dir, filename)
                with open(path, "wb") as f:
                    f.write(r.content)

                temp_filename = f"{uuid.uuid4().hex}{ext}"
                temp_path = os.path.join(NAPCAT_TEMP_DIR, temp_filename)
                shutil.copy(path, temp_path)
                sent_temp_paths.append(temp_path)
                messages.append(MessageSegment.image(f"file://{temp_path}"))

            except Exception as e:
                print(f"[Pixiv私聊插件] ❌ 下载失败: {e}")
                continue

    if messages:
        try:
            notice = await bot.send(event, f"📷 已获取 {len(messages)} 张插图，{RECALL_SECONDS} 秒后将自动撤回。")
            if isinstance(notice, dict) and "message_id" in notice:
                message_ids.append(notice["message_id"])
        except Exception as e:
            print(f"[Pixiv私聊插件] ❌ 提示发送失败：{e}")

        for msg in messages:
            try:
                result = await bot.send(event, msg)
                if isinstance(result, dict) and "message_id" in result:
                    message_ids.append(result["message_id"])
            except Exception as e:
                print(f"[Pixiv私聊插件] ❌ 图片发送失败：{e}")

        # 启动撤回 + 清理
        async def recall_and_cleanup():
            await asyncio.sleep(RECALL_SECONDS)
            for mid in message_ids:
                try:
                    await bot.call_api("delete_msg", message_id=mid)
                    print(f"[Pixiv私聊插件] ✅ 撤回消息 {mid}")
                except Exception as e:
                    print(f"[Pixiv私聊插件] ⚠️ 撤回失败：{e}")

            for temp_path in sent_temp_paths:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        print(f"[Pixiv私聊插件] ✅ 删除临时文件: {temp_path}")
                except Exception as e:
                    print(f"[Pixiv私聊插件] ⚠️ 删除临时文件失败: {e}")

            try:
                shutil.rmtree(user_dir, ignore_errors=True)
                print(f"[Pixiv私聊插件] ✅ 清理用户缓存目录: {user_dir}")
            except Exception as e:
                print(f"[Pixiv私聊插件] ⚠️ 删除缓存目录失败: {e}")

        asyncio.create_task(recall_and_cleanup())
    else:
        await bot.send(event, "❌ 所有图片发送失败")

def pixiv_r_rule(event: MessageEvent):
    return isinstance(event, PrivateMessageEvent) and event.get_plaintext().strip().lower().startswith(".pixiv r ")

pixiv_r = on_message(rule=pixiv_r_rule, priority=1, block=True)

@pixiv_r.handle()
async def _(bot: Bot, event: MessageEvent):
    refresh_token_from_file()
    if not await check_cooldown(bot, event):
        return

    text = event.get_plaintext().strip()
    parts = text.split()
    if len(parts) < 3:
        await bot.send(event, "❗ 格式应为 .pixiv r [关键词] [数量] 或 .pixiv r [关键词] [day/week/month] [数量]")
        return

    tag = parts[2]
    mode = None
    num = 1

    for part in parts[3:]:
        if part.isdigit():
            num = min(int(part), 6)
        elif part.lower() in {"day", "week", "month"}:
            mode = part.lower()

    illusts = []
    max_pages = 10
    pages = 0
    seen_ids = set()

    try:
        res = api.illust_ranking(mode=mode) if mode and not tag else api.search_illust(tag)

        while res and res.illusts and pages < max_pages:
            for i in res.illusts:
                if i.id not in seen_ids:
                    illusts.append(i)
                    seen_ids.add(i.id)

            pages += 1
            if res.next_url:
                next_qs = api.parse_qs(res.next_url)
                res = api.illust_ranking(**next_qs) if mode and not tag else api.search_illust(**next_qs)
            else:
                break

        if not illusts:
            await bot.send(event, "⚠️ 未找到插图")
            return

        selected = random.sample(illusts, min(num, len(illusts)))
        await send_images(bot, event, selected)

    except Exception as e:
        await bot.send(event, f"❌ 获取失败: {e}")

def pixiv_u_rule(event: MessageEvent):
    return isinstance(event, PrivateMessageEvent) and event.get_plaintext().strip().lower().startswith(".pixiv u ")

pixiv_u = on_message(rule=pixiv_u_rule, priority=1, block=True)

@pixiv_u.handle()
async def _(bot: Bot, event: MessageEvent):
    refresh_token_from_file()
    if not await check_cooldown(bot, event):
        return

    parts = event.get_plaintext().strip().split()
    if len(parts) < 3:
        await bot.send(event, "❗ 格式应为 .pixiv u [用户名] [random/latest] [数量]")
        return

    username = parts[2]
    mode = "latest"
    num = 1

    for p in parts[3:]:
        if p.isdigit():
            num = min(int(p), 6)
        elif p.lower() in {"random", "latest"}:
            mode = p.lower()

    try:
        result = api.search_user(username)
        if not result.user_previews:
            await bot.send(event, f"❌ 未找到用户「{username}」")
            return

        user_id = result.user_previews[0].user.id
        illusts = []
        offset = 0
        seen_ids = set()

        for _ in range(10):
            res = api.user_illusts(user_id, offset=offset)
            page_illusts = [i for i in res.illusts if i.id not in seen_ids]
            if not page_illusts:
                break
            illusts.extend(page_illusts)
            seen_ids.update(i.id for i in page_illusts)
            if not res.next_url:
                break
            offset += len(res.illusts)

        if not illusts:
            await bot.send(event, "⚠️ 该用户没有可展示作品")
            return

        selected = random.sample(illusts, min(num, len(illusts))) if mode == "random" else illusts[:num]
        await send_images(bot, event, selected)

    except Exception as e:
        await bot.send(event, f"❌ 获取失败: {e}")

def pixiv_hot_rule(event: MessageEvent):
    return isinstance(event, PrivateMessageEvent) and event.get_plaintext().strip().lower().startswith(".pixiv hot ")

pixiv_hot = on_message(rule=pixiv_hot_rule, priority=1, block=True)

@pixiv_hot.handle()
async def _(bot: Bot, event: MessageEvent):
    refresh_token_from_file()
    if not await check_cooldown(bot, event):
        return

    parts = event.get_plaintext().strip().split()
    if len(parts) < 3:
        await bot.send(event, "❗ 格式应为 .pixiv hot [关键词] [数量]")
        return

    tag = parts[2]
    try:
        num = int(parts[3]) if len(parts) > 3 else 1
        num = max(1, min(num, 6))
    except ValueError:
        await bot.send(event, "❗ 数量参数无效，应为数字")
        return

    try:
        res = api.search_illust(tag, sort="popular_desc")
        illusts = [i for i in res.illusts] if res and getattr(res, "illusts", None) else []

        if not illusts:
            await bot.send(event, "⚠️ 未找到热门插图")
            return

        selected = random.sample(illusts, min(num, len(illusts)))
        await send_images(bot, event, selected)

    except Exception as e:
        await bot.send(event, f"❌ 获取热门插图失败：{e}")