# This module is part of https://github.com/nabilanavab/ilovepdf
# Feel free to use and contribute to this project. Your contributions are welcome!
# copyright ©️ 2021 nabilanavab

file_name = "ILovePDF/plugins/dm/admin.py"

import datetime
import os, shutil
from plugins import *
from plugins.utils import *
from pyrogram.errors import (
    InputUserDeactivated, UserNotParticipant,
    FloodWait, UserIsBlocked, PeerIdInvalid,
)
from configs.config import dm, settings
from configs.db import dataBASE, ping_list
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

if dataBASE.MONGODB_URI:
    from database import db

BROADCAST = False

# Stop bot by using /stop [only for admins]
@ILovePDF.on_message(filters.command("stop") & filters.user(dm.ADMINS) & filters.private & filters.incoming)
async def stop(bot, message):
    try:
        global BROADCAST
        # response to admins
        if (message and message.text=="/stop" and BROADCAST):
            return await message.reply(
                "MESSAGE FOR ADMIN: Currently Broadsting Something.. 🥱", quote=True
            )
        settings.STOP_BOT = not settings.STOP_BOT
        reply = "MESSAGE FOR ADMIN: `توقف البوت` 🗽" if settings.STOP_BOT else "MESSAGE FOR ADMIN: `بدا البوت` ✨"
        await message.reply(reply)

        # when the bot get started it notifies the users asked to notify
        if not settings.STOP_BOT:
            for user in ping_list:
                try:
                    await bot.send_message(chat_id=user, text="💡")
                except FloodWait as e:
                    await asyncio.sleep(e.value)
    except Exception as error:
        logger.exception("🐞 %s: %s" % (file_name, error), exc_info=True)


@ILovePDF.on_callback_query(filters.regex("ping_me"))
async def ping_me(bot, callbackQuery):
    try:
        await callbackQuery.answer("👍")
        ping_list.append(callbackQuery.from_user.id)
    except Exception as error:
        logger.exception("🐞 %s: %s" % (file_name, error), exc_info=True)


# Broadcast Message [only for admins]
@ILovePDF.on_message(filters.command("send") & filters.user(dm.ADMINS) & filters.private & filters.incoming)
async def send(bot, message):
    try:
        await message.reply_chat_action(enums.ChatAction.TYPING)
        
        if not message.reply_to_message:
            error = await message.reply("⚙️ `المعالجة..`", quote=True)
            await asyncio.sleep(1)
            return await error.edit("__please, reply to a message__ 🥲")

        msg = await message.reply_to_message.reply("⚙️ `المعالجة..`", quote=True)
        await message.delete()
        
        return await msg.edit(
            text="⚙️ SEND MESSAGE: \n\n`Now, Select any Option Below.. `",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("📢 ↓ BROADCAST ↓ 📢", callback_data="nabilanavab")
                ],[
                    InlineKeyboardButton("🔸 COPY 🔸", callback_data="send|copy|broad"),
                    InlineKeyboardButton("🔸 FORWARD 🔸", callback_data="send|forw|broad"),
                ],[
                    InlineKeyboardButton("👤 ↓ PM ↓ 👤", callback_data="nabilanavab"),
                ],[
                    InlineKeyboardButton("🔸 COPY 🔸", callback_data="send|copy|pm"),
                    InlineKeyboardButton("🔸 FORWARD 🔸", callback_data="send|forw|pm"),
                ],[
                    InlineKeyboardButton("📢 NoN SUBSCRIBERS 📢", callback_data="nabilanavab"),
                ],[
                    InlineKeyboardButton("🔸 COPY 🔸", callback_data="send|copy|not"),
                    InlineKeyboardButton("🔸 FORWARD 🔸", callback_data="send|forw|not"),
                ],]
            ),
        )
    except Exception as error:
        logger.exception("🐞 %s: %s" % (file_name, error), exc_info=True)


async def broadcast_messages(user_id: int, message, info, force=False):
    try:
        if force:
            try:
                user_status = await bot.get_chat_member(
                    str(settings.UPDATE_CHANNEL), user_id
                )
                
                if user_status.status != "kicked":
                    pass
                else:
                    return False, "Subscribed"
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except UserNotParticipant as e:
                pass
            except Exception as e:
                pass
        
        if info == "copy":
            await message.copy(chat_id=user_id)
            return True, "Success"
        else:
            await message.forward(chat_id=user_id)
            return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message, info)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        return False, "Deleted"
    except UserIsBlocked:
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        return False, "Error"
    except Exception as e:
        logger.exception("🐞 %s: %s" % (file_name, e), exc_info=True)
        return False, "Error"


@ILovePDF.on_callback_query(filters.regex("^send"))
async def _send(bot, callback_query):
    try:
        global BROADCAST
        data = callback_query.data
        _, __, ___ = callback_query.data.split("|")

        if ___ == "broad" and not dataBASE.MONGODB_URI:
            return await callback_query.answer("Can't Use this feature ={")
        
        if ___ in ["broad", "not"]:
            if ___ == "not" and not (settings.UPDATE_CHANNEL):
                return await callback_query.answer("First ADD and updates channel.. 😏")
            if BROADCAST:
                return await callback_query.answer("Broadcasting Some Other Message.. 🙄")
            await callback_query.answer("⚙️ Processing.. ")
            BROADCAST = not BROADCAST
            await stop(bot, callback_query.message)
            
            if os.path.exists(f"./work/nabilanavab"):
                for chat in os.listdir("./work/nabilanavab"):
                    if f"{chat}".startswith("-100"):
                        await bot.send_message(
                            chat_id=chat, text="Bot Stopped..\n__Some Server maintenance underway__ 😊"
                        )
                    else:
                        await bot.send_message(
                            chat_id=chat, text="Bot is paused. \n\nWill notify you when it's back up! 🔥"
                        )
                        ping_list.append(callback_query.from_user.id)
                shutil.rmtree(f"./work")
            os.makedirs("./work/nabilanavab")

            users = await db.get_all_users()
            broadcast_msg = callback_query.message.reply_to_message
            total_users = await db.total_users_count()
            await callback_query.message.edit(
                text=f"⚙️ Started Broadcasting..\nTOTAL {total_users} USERS 😍\n\n↓ MESSAGE ↓"
                     f"\n`{broadcast_msg.text if broadcast_msg.text else '📂 Media 📂'}`",
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(
                            "🔸 asForward 🔸" if __ == "forw" else "🔸 asCopy 🔸",
                            callback_data="nabilanavab",
                        )
                    ]]
                ),
            )
            
            start_time = time.time()
            done, blocked, deleted, failed, success, subscribed = 0, 0, 0, 0, 0, 0

            async for user in users:
                i_success, feed = await broadcast_messages(
                    user_id=int(user["id"]), message=broadcast_msg,
                    info=__, force=True if ___ == "not" else False
                )
                if i_success:
                    success += 1
                elif i_success == False:
                    if feed == "Blocked":
                        blocked += 1
                    elif feed == "Deleted":
                        deleted += 1
                    elif feed == "Error":
                        failed += 1
                    elif feed == "Subscribed":
                        subscribed += 1

                done += 1
                await asyncio.sleep(1)
                if done % 20 == 0:
                    try:
                        await callback_query.message.edit_reply_markup(
                            InlineKeyboardMarkup(
                                [[
                                    InlineKeyboardButton(
                                        f"🔸 asForward({done*100}/{total_users}) 🔸"
                                        if __ == "forw"
                                        else f"🔸 asCopy({done*100/total_users}) 🔸",
                                        callback_data="nabilanavab"
                                    )
                                ]]
                            )
                        )
                    except Exception:
                        logger.debug("edit error - broadcast")
            time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
            return await callback_query.message.edit(
                text=f"`Broadcast Completed:`\n"
                     f"__Completed in__ {time_taken} __seconds ⏰__\n\n"
                     f"__Total Users:__ {total_users} 😎\n"
                     f"__Completed:__   {done} / {total_users} 👑\n"
                     f"__Success:__     {success} ✅\n"
                     f"__Blocked:__     {blocked} ❌\n"
                     f"__Deleted:__     {deleted} ⚰️\n\n" + 
                     f"__Subscribed:__  {subscribed} 🎉" if ___ == "not" else "",
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(
                            "🔸 asForward 🔸" if __ == "forw" else "🔸 asCopy 🔸",
                            callback_data="nabilanavab",)
                    ]]
                ),
            )
            BROADCAST = not BROADCAST
            await stop(bot, callback_query.message)
        
        elif ___ == "pm":
            await callback_query.answer("⚙️ Processing.. ")
            user_id_msg = await bot.ask(
                text="__Now Send me the target ID/Username__ 😅\n\n"
                     "/exit for cancelling current process 🤐",
                chat_id=callback_query.from_user.id,
                reply_to_message_id=callback_query.message.id,
                reply_markup=ForceReply(True),
            )
            if not (user_id_msg.text) or (user_id_msg.text == "/exit"):
                await user_id_msg.reply_to_message.delete()
                return await user_id_msg.delete()

            chat = user_id_msg.text
            try:
                chat = int(user_id_msg.text)
            except Exception:
                pass
            
            try:
                try:
                    user_info = await bot.get_users(chat)
                except Exception:
                    user_info = await bot.get_chat(chat)
            except Exception as e:
                return await user_id_msg.reply(
                    f"__Can't Process This message__\n\n__REASON:__ `{e}`",
                    quote=True
                )
            
            forward_msg = callback_query.message.reply_to_message
            try:
                if __ == "copy":
                    await forward_msg.copy(user_info.id)
                else:
                    await forward_msg.forward(user_info.id)
            except Exception as error:
                return await user_id_msg.reply(
                    f"__Can't forward message__\n__REASON:__ `{error}`"
                )
            else:
                return await user_id_msg.reply("Successfully forwarded")
        else:
            return
    except Exception as e:
        logger.exception("🐞 %s: %s" % (file_name, e), exc_info=True)

# If you have any questions or suggestions, please feel free to reach out.
# Together, we can make this project even better, Happy coding!  XD
