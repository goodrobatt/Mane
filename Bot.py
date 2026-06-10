#!/usr/bin/env python36
# -*- coding: utf-8 -*-

import requests
import time
import json
import logging
import os
from datetime import datetime, timedelta

TOKEN = "8331345131:AAG3vyde-qfrKE625I8OqFIISytFlX9ia7U"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────── ذخیره‌سازی داده ───────────────────────────
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"bot_admins": {}, "warn_counts": {}, "muted_users": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

DATA = load_data()

# ─────────────────────────── توابع API ───────────────────────────

def api(method, **kwargs):
    try:
        r = requests.post(f"{BASE_URL}/{method}", json=kwargs, timeout=15)
        return r.json()
    except Exception as e:
        log.error(f"API error {method}: {e}")
        return {"ok": False}

def send(chat_id, text, reply_to=None, parse_mode="HTML"):
    params = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_to:
        params["reply_to_message_id"] = reply_to
    return api("sendMessage", **params)

def delete_msg(chat_id, message_id):
    return api("deleteMessage", chat_id=chat_id, message_id=message_id)

def ban_user(chat_id, user_id):
    return api("banChatMember", chat_id=chat_id, user_id=user_id)

def unban_user(chat_id, user_id):
    return api("unbanChatMember", chat_id=chat_id, user_id=user_id, only_if_banned=True)

def mute_user(chat_id, user_id, until=None):
    perms = {
        "can_send_messages": False,
        "can_send_audios": False,
        "can_send_documents": False,
        "can_send_photos": False,
        "can_send_videos": False,
        "can_send_voice_notes": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
    }
    params = {"chat_id": chat_id, "user_id": user_id, "permissions": perms}
    if until:
        params["until_date"] = until
    return api("restrictChatMember", **params)

def unmute_user(chat_id, user_id):
    perms = {
        "can_send_messages": True,
        "can_send_audios": True,
        "can_send_documents": True,
        "can_send_photos": True,
        "can_send_videos": True,
        "can_send_voice_notes": True,
        "can_send_polls": True,
        "can_send_other_messages": True,
        "can_add_web_page_previews": True,
    }
    return api("restrictChatMember", chat_id=chat_id, user_id=user_id, permissions=perms)

def get_chat_member(chat_id, user_id):
    r = api("getChatMember", chat_id=chat_id, user_id=user_id)
    if r.get("ok"):
        return r["result"]
    return None

def get_me():
    r = api("getMe")
    if r.get("ok"):
        return r["result"]
    return None

def pin_message(chat_id, message_id, disable_notification=False):
    return api("pinChatMessage", chat_id=chat_id, message_id=message_id,
               disable_notification=disable_notification)

def unpin_message(chat_id, message_id):
    return api("unpinChatMessage", chat_id=chat_id, message_id=message_id)

def unpin_all(chat_id):
    return api("unpinAllChatMessages", chat_id=chat_id)

def promote_admin(chat_id, user_id):
    return api("promoteChatMember", chat_id=chat_id, user_id=user_id,
               can_manage_chat=True, can_delete_messages=True,
               can_manage_video_chats=True, can_restrict_members=True,
               can_promote_members=False, can_change_info=True,
               can_invite_users=True, can_pin_messages=True)

def demote_admin(chat_id, user_id):
    return api("promoteChatMember", chat_id=chat_id, user_id=user_id,
               can_manage_chat=False, can_delete_messages=False,
               can_manage_video_chats=False, can_restrict_members=False,
               can_promote_members=False, can_change_info=False,
               can_invite_users=False, can_pin_messages=False)

# ─────────────────────────── بررسی دسترسی ───────────────────────────

def is_bot_admin(chat_id, user_id):
    """آیا کاربر با دستور 'ترفیع ربات' ادمین ربات شده؟"""
    key = f"{chat_id}:{user_id}"
    return key in DATA.get("bot_admins", {})

def is_group_owner(chat_id, user_id):
    """آیا کاربر سازنده/مالک گروه است؟"""
    m = get_chat_member(chat_id, user_id)
    return m and m.get("status") == "creator"

def can_command(chat_id, user_id):
    """فقط کسی که با ترفیع ربات ادمین ربات شده می‌تواند دستور بدهد"""
    return is_bot_admin(chat_id, user_id)

def user_mention(user):
    uid = user.get("id")
    name = user.get("first_name", "کاربر")
    lname = user.get("last_name", "")
    if lname:
        name = f"{name} {lname}"
    return f'<a href="tg://user?id={uid}">{name}</a>'

# ─────────────────────────── متن‌های کمک ───────────────────────────

HELP_TEXT = """
🤖 <b>ربات مدیریت گروه</b>

━━━━━━━━━━━━━━━━━━━━
👑 <b>دستورات ادمین ربات</b>
━━━━━━━━━━━━━━━━━━━━

<b>📌 مدیریت ادمین‌ها:</b>
• <code>ترفیع ربات</code> — تبدیل شدن به ادمین ربات (فقط مالک گروه)
• <code>تنزل ربات</code> — حذف از ادمین ربات
• <code>لیست ادمین</code> — نمایش ادمین‌های ربات

<b>🔨 مدیریت کاربران:</b>
• ریپلی روی پیام + <code>بن</code> یا <code>ban</code> — بن کردن
• ریپلی روی پیام + <code>آنبن</code> یا <code>unban</code> — رفع بن
• ریپلی روی پیام + <code>میوت</code> یا <code>mute</code> — بی‌صدا کردن
• ریپلی روی پیام + <code>آنمیوت</code> یا <code>unmute</code> — رفع بی‌صدا
• ریپلی روی پیام + <code>اخراج</code> یا <code>kick</code> — اخراج
• ریپلی روی پیام + <code>هشدار</code> یا <code>warn</code> — اخطار (۳ اخطار = بن)
• ریپلی روی پیام + <code>هشدارها</code> یا <code>warns</code> — نمایش اخطارها
• ریپلی روی پیام + <code>پاک هشدار</code> یا <code>resetwarn</code> — پاک کردن اخطارها

<b>📌 مدیریت پیام‌ها:</b>
• ریپلی روی پیام + <code>حذف</code> یا <code>del</code> — حذف پیام
• ریپلی روی پیام + <code>پین</code> یا <code>pin</code> — پین کردن
• ریپلی روی پیام + <code>آنپین</code> یا <code>unpin</code> — رفع پین
• <code>پاک پین</code> یا <code>unpinall</code> — رفع پین همه پیام‌ها

<b>👮 مدیریت ادمین تلگرام:</b>
• ریپلی روی پیام + <code>ادمین کن</code> یا <code>promote</code> — ادمین کردن
• ریپلی روی پیام + <code>دادمین کن</code> یا <code>demote</code> — حذف ادمین

<b>ℹ️ اطلاعات:</b>
• <code>آیدی</code> یا <code>id</code> — نمایش آیدی
• <code>اطلاعات</code> یا <code>info</code> — اطلاعات کاربر
• <code>کمک</code> یا <code>help</code> — این پیام

━━━━━━━━━━━━━━━━━━━━
⚠️ <b>توجه:</b> فقط ادمین‌های ربات می‌توانند از دستورات بالا استفاده کنند.
برای ادمین شدن، مالک گروه باید پیام <code>ترفیع ربات</code> را ارسال کند.
"""

# ─────────────────────────── پردازش دستورات ───────────────────────────

def parse_command(text):
    """استخراج دستور از متن پیام"""
    if not text:
        return None
    t = text.strip().lower()

    COMMANDS = {
        # ادمین ربات
        "ترفیع ربات": "promote_bot",
        "تنزل ربات": "demote_bot",
        "لیست ادمین": "list_admins",
        "لیست ادمین‌ها": "list_admins",
        # کمک
        "کمک": "help",
        "help": "help",
        "راهنما": "help",
        # آیدی
        "آیدی": "id",
        "id": "id",
        # اطلاعات
        "اطلاعات": "info",
        "info": "info",
        # بن
        "بن": "ban",
        "ban": "ban",
        # آنبن
        "آنبن": "unban",
        "unban": "unban",
        "رفع بن": "unban",
        # اخراج
        "اخراج": "kick",
        "kick": "kick",
        # میوت
        "میوت": "mute",
        "mute": "mute",
        "بی صدا": "mute",
        "بی‌صدا": "mute",
        # آنمیوت
        "آنمیوت": "unmute",
        "unmute": "unmute",
        "رفع میوت": "unmute",
        "رفع بی‌صدا": "unmute",
        # حذف
        "حذف": "delete",
        "del": "delete",
        "delete": "delete",
        # پین
        "پین": "pin",
        "pin": "pin",
        # آنپین
        "آنپین": "unpin",
        "unpin": "unpin",
        "رفع پین": "unpin",
        # پاک پین همه
        "پاک پین": "unpinall",
        "unpinall": "unpinall",
        # هشدار
        "هشدار": "warn",
        "warn": "warn",
        "اخطار": "warn",
        # هشدارها
        "هشدارها": "warns",
        "warns": "warns",
        "اخطارها": "warns",
        # پاک هشدار
        "پاک هشدار": "resetwarn",
        "resetwarn": "resetwarn",
        "پاک اخطار": "resetwarn",
        # ادمین تلگرام
        "ادمین کن": "promote",
        "promote": "promote",
        # دادمین
        "دادمین کن": "demote",
        "demote": "demote",
    }

    return COMMANDS.get(t)


def handle_message(msg):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    user = msg.get("from", {})
    user_id = user.get("id")
    text = msg.get("text", "").strip() if msg.get("text") else ""
    reply = msg.get("reply_to_message")
    msg_id = msg.get("message_id")

    if not chat_id or not user_id:
        return

    cmd = parse_command(text)
    if not cmd:
        return

    log.info(f"CMD: {cmd} | user: {user_id} | chat: {chat_id}")

    # ─── دستورات عمومی (بدون نیاز به ادمین بودن) ───
    if cmd == "help":
        send(chat_id, HELP_TEXT, reply_to=msg_id)
        return

    if cmd == "id":
        if reply:
            target = reply.get("from", {})
            tid = target.get("id")
            send(chat_id, f"🆔 آیدی کاربر: <code>{tid}</code>", reply_to=msg_id)
        else:
            send(chat_id, f"🆔 آیدی شما: <code>{user_id}</code>\n🏠 آیدی گروه: <code>{chat_id}</code>", reply_to=msg_id)
        return

    # ─── ترفیع ربات (فقط مالک گروه) ───
    if cmd == "promote_bot":
        if chat_type == "private":
            send(chat_id, "⚠️ این دستور فقط در گروه کار می‌کند.")
            return
        if not is_group_owner(chat_id, user_id):
            send(chat_id, "❌ فقط مالک گروه می‌تواند ادمین ربات تعیین کند.", reply_to=msg_id)
            return
        target_user = user
        target_id = user_id
        if reply:
            target_user = reply.get("from", {})
            target_id = target_user.get("id")
        key = f"{chat_id}:{target_id}"
        DATA.setdefault("bot_admins", {})[key] = {
            "user_id": target_id,
            "name": target_user.get("first_name", ""),
            "added_at": str(datetime.now())
        }
        save_data(DATA)
        send(chat_id, f"✅ {user_mention(target_user)} به عنوان ادمین ربات تعیین شد.", reply_to=msg_id)
        return

    # ─── تنزل ربات (فقط ادمین ربات یا مالک) ───
    if cmd == "demote_bot":
        if not (is_bot_admin(chat_id, user_id) or is_group_owner(chat_id, user_id)):
            send(chat_id, "❌ شما دسترسی ندارید.", reply_to=msg_id)
            return
        target_user = user
        target_id = user_id
        if reply:
            target_user = reply.get("from", {})
            target_id = target_user.get("id")
        key = f"{chat_id}:{target_id}"
        if key in DATA.get("bot_admins", {}):
            del DATA["bot_admins"][key]
            save_data(DATA)
            send(chat_id, f"✅ {user_mention(target_user)} از ادمین ربات حذف شد.", reply_to=msg_id)
        else:
            send(chat_id, "⚠️ این کاربر ادمین ربات نیست.", reply_to=msg_id)
        return

    # ─── لیست ادمین‌های ربات ───
    if cmd == "list_admins":
        admins = DATA.get("bot_admins", {})
        group_admins = {k: v for k, v in admins.items() if k.startswith(f"{chat_id}:")}
        if not group_admins:
            send(chat_id, "📋 هیچ ادمین ربات‌ای در این گروه وجود ندارد.", reply_to=msg_id)
        else:
            lines = ["👑 <b>ادمین‌های ربات:</b>\n"]
            for k, v in group_admins.items():
                lines.append(f"• {v.get('name', 'نامشخص')} — <code>{v.get('user_id')}</code>")
            send(chat_id, "\n".join(lines), reply_to=msg_id)
        return

    # ─── بقیه دستورات: فقط ادمین ربات ───
    if not can_command(chat_id, user_id):
        send(chat_id, "🚫 شما ادمین ربات نیستید.\nبرای کسب دسترسی، از مالک گروه بخواهید پیام <b>ترفیع ربات</b> را ارسال کند.", reply_to=msg_id)
        return

    # ─── اطلاعات کاربر ───
    if cmd == "info":
        target_user = reply.get("from", {}) if reply else user
        target_id = target_user.get("id")
        m = get_chat_member(chat_id, target_id)
        status_map = {
            "creator": "👑 مالک",
            "administrator": "🛡 ادمین",
            "member": "👤 عضو",
            "restricted": "🔇 محدود",
            "left": "🚪 خارج شده",
            "kicked": "🔨 بن شده"
        }
        status = status_map.get(m.get("status", ""), "نامشخص") if m else "نامشخص"
        warn_key = f"{chat_id}:{target_id}"
        warns = DATA.get("warn_counts", {}).get(warn_key, 0)
        text_out = (
            f"ℹ️ <b>اطلاعات کاربر</b>\n\n"
            f"👤 نام: {user_mention(target_user)}\n"
            f"🆔 آیدی: <code>{target_id}</code>\n"
            f"📌 وضعیت: {status}\n"
            f"⚠️ اخطارها: {warns}/3"
        )
        send(chat_id, text_out, reply_to=msg_id)
        return

    # ─── حذف پیام ───
    if cmd == "delete":
        if not reply:
            send(chat_id, "⚠️ روی پیامی که می‌خواهید حذف کنید ریپلی بزنید.", reply_to=msg_id)
            return
        delete_msg(chat_id, reply["message_id"])
        delete_msg(chat_id, msg_id)
        return

    # ─── بن ───
    if cmd == "ban":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        r = ban_user(chat_id, target_id)
        if r.get("ok"):
            send(chat_id, f"🔨 {user_mention(target_user)} بن شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا در بن کردن: {r.get('description', '')}", reply_to=msg_id)
        return

    # ─── آنبن ───
    if cmd == "unban":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        r = unban_user(chat_id, target_id)
        if r.get("ok"):
            send(chat_id, f"✅ بن {user_mention(target_user)} برداشته شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا: {r.get('description', '')}", reply_to=msg_id)
        return

    # ─── اخراج ───
    if cmd == "kick":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        ban_user(chat_id, target_id)
        unban_user(chat_id, target_id)
        send(chat_id, f"👢 {user_mention(target_user)} اخراج شد.", reply_to=msg_id)
        return

    # ─── میوت ───
    if cmd == "mute":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        r = mute_user(chat_id, target_id)
        if r.get("ok"):
            key = f"{chat_id}:{target_id}"
            DATA.setdefault("muted_users", {})[key] = True
            save_data(DATA)
            send(chat_id, f"🔇 {user_mention(target_user)} بی‌صدا شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا: {r.get('description', '')}", reply_to=msg_id)
        return

    # ─── آنمیوت ───
    if cmd == "unmute":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        r = unmute_user(chat_id, target_id)
        if r.get("ok"):
            key = f"{chat_id}:{target_id}"
            DATA.get("muted_users", {}).pop(key, None)
            save_data(DATA)
            send(chat_id, f"🔊 بی‌صدایی {user_mention(target_user)} برداشته شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا: {r.get('description', '')}", reply_to=msg_id)
        return

    # ─── هشدار ───
    if cmd == "warn":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        key = f"{chat_id}:{target_id}"
        warns = DATA.setdefault("warn_counts", {}).get(key, 0) + 1
        DATA["warn_counts"][key] = warns
        save_data(DATA)
        if warns >= 3:
            ban_user(chat_id, target_id)
            DATA["warn_counts"][key] = 0
            save_data(DATA)
            send(chat_id, f"🚫 {user_mention(target_user)} پس از ۳ اخطار بن شد.", reply_to=msg_id)
        else:
            send(chat_id, f"⚠️ {user_mention(target_user)} اخطار {warns}/3 گرفت.", reply_to=msg_id)
        return

    # ─── نمایش هشدارها ───
    if cmd == "warns":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        key = f"{chat_id}:{target_id}"
        warns = DATA.get("warn_counts", {}).get(key, 0)
        send(chat_id, f"📊 {user_mention(target_user)} — اخطارها: {warns}/3", reply_to=msg_id)
        return

    # ─── پاک کردن هشدارها ───
    if cmd == "resetwarn":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        key = f"{chat_id}:{target_id}"
        DATA.setdefault("warn_counts", {})[key] = 0
        save_data(DATA)
        send(chat_id, f"✅ اخطارهای {user_mention(target_user)} پاک شد.", reply_to=msg_id)
        return

    # ─── پین ───
    if cmd == "pin":
        if not reply:
            send(chat_id, "⚠️ روی پیامی که می‌خواهید پین کنید ریپلی بزنید.", reply_to=msg_id)
            return
        r = pin_message(chat_id, reply["message_id"])
        if r.get("ok"):
            send(chat_id, "📌 پیام پین شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا: {r.get('description', '')}", reply_to=msg_id)
        return

    # ─── آنپین ───
    if cmd == "unpin":
        if not reply:
            send(chat_id, "⚠️ روی پیام پین‌شده ریپلی بزنید.", reply_to=msg_id)
            return
        r = unpin_message(chat_id, reply["message_id"])
        if r.get("ok"):
            send(chat_id, "✅ پین پیام برداشته شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا: {r.get('description', '')}", reply_to=msg_id)
        return

    # ─── پاک پین همه ───
    if cmd == "unpinall":
        r = unpin_all(chat_id)
        if r.get("ok"):
            send(chat_id, "✅ پین همه پیام‌ها برداشته شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا: {r.get('description', '')}", reply_to=msg_id)
        return

    # ─── ادمین کردن در تلگرام ───
    if cmd == "promote":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        r = promote_admin(chat_id, target_id)
        if r.get("ok"):
            send(chat_id, f"👑 {user_mention(target_user)} ادمین شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا: {r.get('description', '')}", reply_to=msg_id)
        return

    # ─── حذف ادمین از تلگرام ───
    if cmd == "demote":
        if not reply:
            send(chat_id, "⚠️ روی پیام کاربر مورد نظر ریپلی بزنید.", reply_to=msg_id)
            return
        target_user = reply.get("from", {})
        target_id = target_user.get("id")
        r = demote_admin(chat_id, target_id)
        if r.get("ok"):
            send(chat_id, f"✅ ادمینی {user_mention(target_user)} برداشته شد.", reply_to=msg_id)
        else:
            send(chat_id, f"❌ خطا: {r.get('description', '')}", reply_to=msg_id)
        return


# ─────────────────────────── حلقه اصلی ───────────────────────────

def main():
    me = get_me()
    if me:
        log.info(f"✅ ربات راه‌اندازی شد: @{me.get('username')} — {me.get('first_name')}")
    else:
        log.error("❌ ربات راه‌اندازی نشد. توکن را بررسی کنید.")
        return

    # پاک کردن آپدیت‌های قدیمی
    r = api("getUpdates", offset=-1, timeout=1)
    last_update_id = 0
    if r.get("ok") and r["result"]:
        last_update_id = r["result"][-1]["update_id"]

    log.info("🔄 در حال دریافت پیام‌ها...")

    while True:
        try:
            r = api("getUpdates", offset=last_update_id + 1, timeout=30)
            if not r.get("ok"):
                time.sleep(3)
                continue

            for update in r.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message") or update.get("edited_message")
                if msg:
                    try:
                        handle_message(msg)
                    except Exception as e:
                        log.error(f"Error handling message: {e}")

        except KeyboardInterrupt:
            log.info("⏹ ربات متوقف شد.")
            break
        except Exception as e:
            log.error(f"Main loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
