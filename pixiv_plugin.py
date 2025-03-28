import os
import time
import shutil
import random
import asyncio
import httpx

from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.exception import FinishedException
from pixivpy3 import AppPixivAPI

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Message

from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
import uuid
from nonebot.adapters.onebot.v11 import GroupMessageEvent

def pixiv_help_rule(event: MessageEvent) -> bool:
    return isinstance(event, GroupMessageEvent) and event.get_plaintext().strip().lower() == ".pixiv help"



pixiv_help = on_message(rule=pixiv_help_rule, priority=1, block=True)

from nonebot.adapters.onebot.v11 import GroupMessageEvent

def pixiv_id_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().lower().startswith(".pixiv id")


pixiv_id = on_message(rule=pixiv_id_rule, priority=1, block=True)


@pixiv_id.handle()
async def handle_pixiv_id(bot: Bot, event: MessageEvent):
    if not await check_cooldown(bot, event):
        return
    text = event.get_plaintext().strip()
    parts = text.split()

    if len(parts) < 3 or not parts[2].isdigit():
        await bot.send(event=event, message="❗ 格式错误，应为 `.pixiv id [作品ID]`")
        return

    illust_id = int(parts[2])

    try:
        illust = api.illust_detail(illust_id).illust

        if not illust:
            await bot.send(event=event, message=f"⚠️ 未找到作品 ID 为 {illust_id} 的插图")
            return

        if is_sensitive(illust):
            await bot.send(event=event, message="⚠️ 该作品被判断为敏感内容，已过滤")
            return

        await send_images(bot, event, str(event.user_id), [illust])

    except Exception as e:
        print(f"[Pixiv插件] ❌ 通过ID获取插图失败: {e}")
        await bot.send(event=event, message=f"❌ 获取插图失败：{e}")


@pixiv_help.handle()
async def handle_pixiv_help(bot: Bot, event: MessageEvent):
    help_text = (
        "🎨 Pixiv 插图指令帮助\n\n"

        "📥 插图获取示例(支持默认、day、week、month)：\n"
        ".pixiv hot 遐蝶\n"
        "↑ 获取 Pixiv 最热门关键词为“遐蝶”的1张图（默认）\n\n"
        
        ".pixiv hot 遐蝶 3\n"
        "↑ 获取 Pixiv 最热门关键词为“遐蝶”的3张图\n\n"
        
        ".pixiv id 12345678\n"
        "↑ 获取 Pixiv id为“12345678”的图\n\n"
        
        ".pixiv r\n"
        "↑ 获取 Pixiv 日榜中1张图（默认）\n\n"

        ".pixiv r 遐蝶 3\n"
        "↑ 随机获取3张关键词为“遐蝶”的插图（按最新排序）\n\n"

        ".pixiv r 遐蝶 week 3\n"
        "↑ 获取“遐蝶”关键词在 Pixiv 周榜中的3张插图\n\n"

        ".pixiv r week 2\n"
        "↑ 获取 Pixiv 周榜中2张随机图（不带关键词）\n\n"

        "👤 用户作品获取示例：\n"
        ".pixiv u Nhimm\n"
        "↑ 获取用户 Nhimm 的最新1张作品（默认 latest）\n\n"

        ".pixiv u Nhimm random 2\n"
        "↑ 随机获取用户 Nhimm 的2张作品\n\n"

        ".pixiv u Nhimm latest 3\n"
        "↑ 获取用户 Nhimm 的最新3张作品\n\n"

        "📌 补充说明：\n"
        "• 每人请求有冷却限制（默认20秒）\n"
        "• 插件会自动过滤 R-18 / 敏感内容\n"
        "• 插图将在 60 秒后自动撤回（仅限群聊）\n\n"

        "—— Powered by 豆芽 doya16 ✨"
    )
    await bot.send(event=event, message=help_text)

# 配置项
REFRESH_TOKEN = "你的pixiv refresh code"   # 你的pixiv refresh code
COOLDOWN_SECONDS = 60   # 用户请求该插件的冷却时间（单位：秒）
RECALL_SECONDS = 30  # 撤回时间（单位：秒）
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache", "pixiv_download")  # 缓存文件路径，你的plugins文件夹内需要存在一个路径 /plugins/cache/pixiv_download
os.makedirs(CACHE_DIR, exist_ok=True)
NAPCAT_TEMP_DIR = r"D:\QQFiles\NapCat\temp"  # 修改为你Napcat本地的临时发送路径

# 初始化 Pixiv API
api = AppPixivAPI()
api.auth(refresh_token=REFRESH_TOKEN)

# 冷却记录
cooldowns = {}
async def check_cooldown(bot: Bot, event: MessageEvent) -> bool:
    uid = str(event.user_id)
    now = time.time()
    if uid in cooldowns and now - cooldowns[uid] < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - cooldowns[uid]))
        await bot.send(event, f"🕓 阁下的请求还在冷却中，请等待 {remaining} 秒后再试。")
        return False
    cooldowns[uid] = now
    return True


import asyncio
from nonebot import get_driver

import json

# ✅ 正确路径：指向 plugins/cache/pixiv_token.json
# 正确路径：写入 plugins/cache/pixiv_token.json
PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))  # plugins 目录路径
CACHE_DIR = os.path.join(PLUGIN_ROOT, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

TOKEN_PATH = os.path.join(CACHE_DIR, "pixiv_token.json")

if not os.path.exists(TOKEN_PATH):
    print("[Pixiv插件] token 路径检查：准备创建 plugins/cache/pixiv_token.json")


def save_access_token(token: str):
    try:
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump({"access_token": token, "timestamp": int(time.time())}, f)
        print(f"[Pixiv插件] ✅ access_token 写入成功：{TOKEN_PATH}")
    except Exception as e:
        print(f"[Pixiv插件] ❌ access_token 写入失败: {e}")



def save_access_token(token: str):
    try:
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump({"access_token": token, "timestamp": int(time.time())}, f)
    except Exception as e:
        print(f"[Pixiv插件] ❌ access_token 写入失败: {e}")


driver = get_driver()


@driver.on_startup
async def on_startup():
    try:
        api.auth(refresh_token=REFRESH_TOKEN)
        save_access_token(api.access_token)
        print("[Pixiv插件] ✅ 启动时 access_token 写入成功")
    except Exception as e:
        print(f"[Pixiv插件] ❌ 启动时刷新 token 失败: {e}")


# 自定义触发器
def pixiv_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip().lower()
    if text.startswith(".pixiv r18"):  # 显式排除 r18
        return False
    return text.startswith(".pixiv r") or text.startswith(".pixiv u")



# 注册监听器
pixiv_handler = on_message(rule=pixiv_rule, priority=1, block=True)

@pixiv_handler.handle()
async def handle_pixiv_command(bot: Bot, event: MessageEvent):
    uid = str(event.user_id)
    now = time.time()
    text = event.get_plaintext().strip()

    if uid in cooldowns and now - cooldowns[uid] < COOLDOWN_SECONDS:
        await bot.send(event=event, message=f"阁下的吟唱还在冷却中，请等待 {int(COOLDOWN_SECONDS - (now - cooldowns[uid]))} 秒后再试。")
        return

    cooldowns[uid] = now

    try:
        if text.startswith(".pixiv r"):
            await handle_pixiv_random(bot, event, text)
        elif text.startswith(".pixiv u"):
            await handle_pixiv_user(bot, event, text)
        else:
            await bot.send(event=event, message="❗ 阁下的吟唱格式错误。使用.pixiv help 查看详情")
    except FinishedException:
        raise
    except Exception as e:
        await bot.send(event=event, message=f"❌ 插件处理失败：{e}")

# 随机插图处理
async def handle_pixiv_random(bot: Bot, event: MessageEvent, text: str):
    parts = text.split()
    tag, num = None, 1
    mode = None  # 排行榜模式：day/week/month

    max_pages = 15  # 最多翻页数，建议调到 5~10 增加多样性

    # 解析参数
    for part in parts[2:]:
        if part.isdigit():
            num = min(int(part), 6)
        elif part.lower() in {"day", "week", "month"}:
            mode = part.lower()
        else:
            tag = part

    illusts = []
    try:
        if mode and not tag:  # 排行榜模式（无关键词）
            res = api.illust_ranking(mode=mode)
            pages = 0
            while res and res.illusts and pages < max_pages:
                illusts.extend([i for i in res.illusts if not is_sensitive(i)])
                pages += 1
                if res.next_url:
                    next_qs = api.parse_qs(res.next_url)
                    res = api.illust_ranking(**next_qs)
                else:
                    break

        elif tag:  # 有关键词，默认排序（支持 popular+普通图池）
            res = api.search_illust(tag)
            pages = 0
            while res and res.illusts and pages < max_pages:
                illusts.extend([i for i in res.illusts if not is_sensitive(i)])
                pages += 1
                if res.next_url:
                    next_qs = api.parse_qs(res.next_url)
                    res = api.search_illust(**next_qs)
                else:
                    break

        else:  # 默认使用周榜作为基础
            res = api.illust_ranking("week")
            pages = 0
            while res and res.illusts and pages < max_pages:
                illusts.extend([i for i in res.illusts if not is_sensitive(i)])
                pages += 1
                if res.next_url:
                    next_qs = api.parse_qs(res.next_url)
                    res = api.illust_ranking(**next_qs)
                else:
                    break

        if not illusts:
            await bot.send(event=event, message="⚠️ 未找到相关插图。")
            return

        selected = random.sample(illusts, min(num, len(illusts)))
        await send_images(bot, event, str(event.user_id), selected)

    except Exception as e:
        await bot.send(event=event, message=f"❌ 获取插图失败：{e}")

# 用户插图处理
async def handle_pixiv_user(bot: Bot, event: MessageEvent, text: str):
    parts = text.strip().split()
    if len(parts) < 3:
        await bot.send(event=event, message="❗ 阁下的吟唱格式错误。使用.pixiv help 查看详情")
        return

    username = parts[2]
    mode = "latest"  # 默认最新模式
    num = 1

    for p in parts[3:]:
        if p.isdigit():
            num = min(int(p), 6)
        elif p.lower() == "random":
            mode = "random"

    try:
        result = api.search_user(username)
        if not result.user_previews:
            await bot.send(event=event, message=f"❌ 未找到用户「{username}」。")
            return

        user = result.user_previews[0].user

        illusts = []
        max_pages = 10
        offset = 0
        seen_ids = set()

        for _ in range(max_pages):
            res = api.user_illusts(user.id, offset=offset)
            page_illusts = [i for i in res.illusts if not is_sensitive(i) and i.id not in seen_ids]
            if not page_illusts:
                break
            illusts.extend(page_illusts)
            seen_ids.update(i.id for i in page_illusts)
            if not res.next_url:
                break
            offset += len(res.illusts)

        if not illusts:
            await bot.send(event=event, message="⚠️ 该用户暂无非 R-18 / 敏感作品。")
            return

        selected = random.sample(illusts, min(num, len(illusts))) if mode == "random" else illusts[:num]
        await send_images(bot, event, str(event.user_id), selected)

    except Exception as e:
        await bot.send(event=event, message=f"❌ 获取失败：{e}")


def pixiv_hot_rule(event: MessageEvent) -> bool:
    return isinstance(event, GroupMessageEvent) and event.get_plaintext().strip().lower().startswith(".pixiv hot")


pixiv_hot = on_message(rule=pixiv_hot_rule, priority=1, block=True)

@pixiv_hot.handle()
async def handle_pixiv_hot(bot: Bot, event: MessageEvent):
    if not await check_cooldown(bot, event):
        return
    text = event.get_plaintext().strip()
    parts = text.split()
    if len(parts) < 3:
        await bot.send(event=event, message="❗ 格式错误，应为 `.pixiv hot [关键词] [数量]`")
        return

    tag = parts[2]
    try:
        num = int(parts[3]) if len(parts) > 3 else 1
        num = max(1, min(num, 10))
    except ValueError:
        await bot.send(event=event, message="❗ 数量参数无效，应为数字")
        return

    try:
        res = api.search_illust(tag, search_target="partial_match_for_tags", sort="popular_desc")
        illusts = []
        if res and getattr(res, "illusts", None):
            illusts = [i for i in res.illusts if not is_sensitive(i)]
        else:
            print(f"[Pixiv插件] ⚠️ 热门插图 API 返回为空：{res}")

        if not illusts:
            await bot.send(event=event, message="⚠️ 未找到热门插图。")
            return

        selected = random.sample(illusts, min(num, len(illusts)))
        await send_images(bot, event, str(event.user_id), selected)
    except Exception as e:
        print(f"[Pixiv插件] ❌ 热门插图获取异常：{e}")
        await bot.send(event=event, message=f"❌ 热门插图获取失败：{e}")


# 图片下载与发送
# 图片下载与发送
async def send_images(bot: Bot, event: MessageEvent, user_id: str, illusts: list):
    user_dir = os.path.join(CACHE_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)

    max_retry = 5
    retry_delay = 1
    sent_temp_paths = []  # 记录已复制到 NapCat 的路径

    for attempt in range(1, max_retry + 1):
        messages = []
        message_ids = []

        async with httpx.AsyncClient() as client:
            for illust in illusts:
                # 更健壮的图像链接获取逻辑（支持原图、多页图、降级图）
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
                    print(f"[Pixiv插件] ⚠️ 插图 {illust.id} 无可用图片链接，已跳过。")
                    continue

                try:
                    r = await client.get(url, headers={"Referer": "https://www.pixiv.net/"}, timeout=15)
                    content_type = r.headers.get("Content-Type", "")
                    if "jpeg" in content_type:
                        ext = ".jpg"
                    elif "png" in content_type:
                        ext = ".png"
                    elif "gif" in content_type:
                        ext = ".gif"
                    else:
                        print(f"[Pixiv插件] ❌ 非法格式: {content_type} 跳过")
                        continue

                    filename = f"{illust.id}{ext}"
                    path = os.path.join(user_dir, filename)
                    with open(path, "wb") as f:
                        f.write(r.content)

                    temp_filename = f"{uuid.uuid4().hex}{ext}"
                    temp_path = os.path.join(NAPCAT_TEMP_DIR, temp_filename)
                    shutil.copy(path, temp_path)
                    sent_temp_paths.append(temp_path)

                    print(f"[Pixiv插件] ✅ 下载并复制成功: {path} -> {temp_path}")
                    messages.append(MessageSegment.image(f"file://{temp_path}"))

                except Exception as e:
                    print(f"[Pixiv插件] ❌ 下载失败: {e}")
                    continue

        if messages:
            await bot.send(event=event, message=f"📷 已获取 {len(illusts)} 张插图，{RECALL_SECONDS} 秒后将自动撤回。")

            for msg in messages:
                try:
                    result = await bot.send(event=event, message=msg)
                    if isinstance(result, dict) and "message_id" in result:
                        message_ids.append(result["message_id"])
                except Exception as e:
                    print(f"[Pixiv插件] ❌ 图片发送失败：{e}")

            # 群聊消息撤回逻辑
            if isinstance(event, GroupMessageEvent):
                group_id = event.group_id

                async def recall_and_cleanup():
                    await asyncio.sleep(RECALL_SECONDS)

                    # 撤回
                    for mid in message_ids:
                        try:
                            await bot.call_api("delete_msg", message_id=mid)
                            print(f"[Pixiv插件] ✅ 已撤回消息 {mid}")
                        except Exception as e:
                            print(f"[Pixiv插件] ❌ 撤回失败：{e}")

                    # 清理 NapCat 缓存文件
                    for temp_path in sent_temp_paths:
                        try:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                                print(f"[Pixiv插件] ✅ 已删除临时文件: {temp_path}")
                        except Exception as e:
                            print(f"[Pixiv插件] ⚠️ 删除临时图片失败: {e}")

                asyncio.create_task(recall_and_cleanup())

            break  # 成功后跳出 retry
        else:
            print(f"[Pixiv插件] ⚠️ 第 {attempt}/{max_retry} 次尝试失败，准备重试...")
            await asyncio.sleep(retry_delay)
    else:
        await bot.send(event=event, message="❌ 图片全部发送失败，Pixiv 图片格式异常或网络错误")

    await asyncio.sleep(1)
    shutil.rmtree(user_dir, ignore_errors=True)


# 过滤敏感图片
def is_sensitive(illust) -> bool:
    if illust.sanity_level >= 6:
        return True

    sensitive_tags = {
        # "R-18", "r18", "r-18", "R18", "r-18g", "r18g",
        # "裸", "裸体", "露出", "性器", "色情", "sex", "中出", "精液",
        "肢体切断", "重口", "兽交", "血腥", "血", "gore",
        "流血", "血腥", "肢体切断", "猎奇", "重口", "内脏", "分尸",
        "残肢", "暴力", "病娇", "SM", "拷问", "刑具",
        "guro", "断肢",
        # "全裸", "半裸", "露出", "性器", "乳头", "下体",
        # "露奶", "露臀", "内衣", "开裆",  "手淫", "自慰",
        "兽交", "异种奸", "触手", "怪物娘", "兽人", "非人", "異種姦",
        "催眠", "洗脑", "药物", "猥亵", "非自愿", "偷拍",
        "黑丝", "脚", "恋物癖", "恋尸癖", "尸体",
        # "AI生成"
        "虫子", "昆虫娘", "寄生", "便器", "排泄", "孕"
    }

    # 防止 illust.tags 是 None
    tag_names = set()
    if illust.tags:
        try:
            tag_names = {t.name for t in illust.tags if t and hasattr(t, "name")}
        except Exception as e:
            print(f"[Pixiv插件] ⚠️ 标签解析异常: {e}")

    return not sensitive_tags.isdisjoint(tag_names)

