# 管理员命令处理器
from datetime import timedelta
from app.bot.validators import confirmation_required
from app.services.user_service import UserService
from app.services.score_service import ScoreService
from app.services.invite_code_service import InviteCodeService
from app.utils.logger import logger
from config import settings
from app.bot.core.bot_instance import bot
from telebot import types
from app.utils.api_clients import service_api_client
from app.utils.utils import paginate_list, create_pagination
from app.utils.message_cleaner import get_message_cleaner
from app.utils.message_queue import get_message_queue

message_queue = get_message_queue()


def generate_invite_code_command(message):
    """生成邀请码 (管理员命令)"""
    telegram_id = message.from_user.id
    args = message.text.split()
    if len(args) == 0:
        count = 1  # 默认生成 1 个
    else:
        try:
            count = int(args[0])
        except ValueError:
            bot.reply_to(message, "参数错误，邀请码数量必须是整数！")
            return

    if count <= 0:
        bot.reply_to(message, "邀请码数量必须大于 0！")
        return

    try:
        invite_codes = []
        for _ in range(count):
            invite_code = InviteCodeService.generate_invite_code(telegram_id)
            if invite_code:
                invite_codes.append(f"<code>{invite_code.code}</code>")
            else:
                bot.reply_to(message, "邀请码生成失败，请重试！")
                return

        if invite_codes:
            response = f"成功生成{count}个邀请码(单击可复制):\n" + "\n".join(invite_codes)
            bot.reply_to(message, response, parse_mode='HTML')
        # bot.send_message(message.chat.id, response, parse_mode='HTML')
    except ValueError:
        bot.reply_to(message, "邀请码生成失败，请重试！")


def generate_renew_codes_command(message):
    """生成续期码 (管理员命令)
    格式: /renew [续期天数] [生成数量]
    示例: /renew 30 5
    """
    try:
        # 解析参数
        args = message.text.split()
        expire_days = int(args[0]) if len(args) > 0 else 30  # 默认续期 30 天
        count = int(args[1]) if len(args) > 1 else 1  # 默认生成 1 个续期码

        if expire_days <= 0 or count <= 0:
            bot.reply_to(message, "续期天数和生成数量必须大于 0！")
            return
        # 生成续期码
        renew_codes = []
        for _ in range(count):
            renew_code = InviteCodeService.generate_invite_code(
                create_user_id=message.from_user.id,
                expire_days=expire_days,
                code_type='renew'
            )
            if renew_code:
                renew_codes.append(f"<code>{renew_code.code}</code>")
            else:
                bot.reply_to(message, "续期码生成失败，请重试！")
                return

        # 返回结果
        response = f"成功生成{count}个续期码(单击可复制):\n" + "\n".join(renew_codes)
        bot.reply_to(message, response, parse_mode='HTML')

    except ValueError:
        bot.reply_to(message, "参数错误，续期天数和生成数量必须是整数！")
        logger.error(f"生成续期码失败: telegram_id={message.from_user.id}")


def get_all_invite_codes_command(message):
    """查看所有邀请码 (管理员命令)"""
    try:
        invite_all_codes = InviteCodeService.get_all_invite_codes()
        if invite_all_codes:
            invite_codes_list = paginate_list(data_list=invite_all_codes, page_size=20)
            page_count = 0
            for invite_codes in invite_codes_list:
                response = f"邀请码列表：当前第{page_count + 1}页\n"
                for invite_code in invite_codes:
                    expire_time = invite_code.create_time + timedelta(days=invite_code.expire_days)
                    response += f"ID: {invite_code.id}, 邀请码: {invite_code.code}, 是否已使用: {'是' if invite_code.is_used else '否'}, 创建时间: {str(invite_code.create_time)[:-7]}, 过期时间: {str(expire_time)[:-7]}, 创建者ID: {invite_code.create_user_id}\n"
                    response += f"--------\n"
                    response += f"生成总数为：{len(invite_all_codes)},当前页有{len(invite_codes)}个未使用!"
                page_count += 1
                bot.reply_to(message, response)
        else:
            bot.reply_to(message, "获取邀请码列表失败，请重试！")
    except ValueError:
        bot.reply_to(message, "获取邀请码列表失败，请重试！")
        logger.error(f"获取邀请码列表失败: telegram_id={message.from_user.id}")
    # chat_id = message.chat.id
    # message_id = message.id
    # invite_all_codes = InviteCodeService.get_all_invite_codes()
    # invite_code_list = []
    # for invite_code in invite_all_codes:
    #     invite_code_list.append(invite_code.code)
    # text, markup = create_pagination(chat_id, message_id, invite_code_list, items_per_page=50)
    # bot.send_message(chat_id, text, reply_markup=markup)


def get_unused_invite_codes_command(message):
    """获取未使用的邀请码列表 (管理员命令)"""
    telegram_id = message.from_user.id
    try:
        logger.info(f"管理员请求获取未使用的邀请码列表: telegram_id={telegram_id}")
        invite_unused_codes = InviteCodeService.get_all_invite_codes(is_used=False)
        if invite_unused_codes:
            invite_codes_list = paginate_list(data_list=invite_unused_codes, page_size=50)
            page_count = 0
            for invite_codes in invite_codes_list:
                response = f"未使用的邀请码：当前第{page_count + 1}\n"
                response += f"--------\n"
                response += f"邀请码：过期时间\n"
                response += f"--------\n"
                for invite_code in invite_codes:
                    expire_time = invite_code.create_time + timedelta(days=invite_code.expire_days)
                    response += f"<code>{invite_code.code}</code>: {str(expire_time)[:-7]}\n"
                response += f"--------\n"
                response += f"未使用总数为：{len(invite_unused_codes)}, 当前页有{len(invite_codes)}个未使用!"
                page_count += 1
                bot.send_message(message.chat.id, response, parse_mode='HTML')
                # bot.reply_to(message, response, parse_mode='HTML')  # 发送HTML格式的消息，支持点击复制
            logger.info(f"管理员获取未使用的邀请码列表成功: telegram_id={telegram_id}, count={len(invite_codes)}")
        else:
            bot.reply_to(message, "没有找到未使用的邀请码！")
            logger.warning(f"没有找到未使用的邀请码: telegram_id={telegram_id}")
    except ValueError:
        bot.reply_to(message, "获取未使用的邀请码列表失败，请重试！")
        logger.error(f"获取未使用的邀请码列表失败: telegram_id={telegram_id}")
    # chat_id = message.chat.id
    # message_id = message.id
    # logger.info(f"message_id: {message_id}")
    # invite_all_codes = InviteCodeService.get_all_invite_codes(is_used=False)
    # invite_code_list = []
    # for invite_code in invite_all_codes:
    #     invite_code_list.append(invite_code.code)
    # text, markup = create_pagination(chat_id, message_id, invite_code_list, items_per_page=50)
    # bot.send_message(chat_id, text, reply_markup=markup)


def get_unused_renew_codes_command(message):
    """获取未使用的续期码列表 (管理员命令)"""
    try:
        telegram_id = message.from_user.id
        logger.info(f"管理员请求获取未使用的续期码列表: telegram_id={telegram_id}")
        invite_unused_codes = InviteCodeService.get_all_invite_codes(code_type="renew", is_used=False)
        if invite_unused_codes:
            invite_codes_list = paginate_list(data_list=invite_unused_codes, page_size=50)
            page_count = 0
            for invite_codes in invite_codes_list:
                response = f"未使用的续期码：当前第{page_count + 1}\n"
                response += f"--------\n"
                response += f"续期码：过期时间\n"
                response += f"--------\n"
                for invite_code in invite_codes:
                    expire_time = invite_code.crate_time + timedelta(days=invite_code.expire_days)
                    response += f"<code>{invite_code.code}</code>: {str(expire_time)[:-7]}\n"
                response += f"--------\n"
                response += f"未使用总数为：{len(invite_unused_codes)}, 当前页有{len(invite_codes)}个未使用!"
                page_count += 1
                bot.reply_to(message, response, parse_mode='HTML')  # 发送HTML格式的消息，支持点击复制
            logger.info(f"管理员获取未使用的续期码列表成功: telegram_id={telegram_id}, count={len(invite_codes)}")
        else:
            bot.reply_to(message, "没有找到未使用的续期码！")
            logger.warning(f"没有找到未使用的续期码: telegram_id={telegram_id}")
    except ValueError:
        bot.reply_to(message, "获取未使用的续期码列表失败，请重试！")
        logger.error(f"获取未使用的续期码列表失败: telegram_id={telegram_id}")

    # chat_id = message.chat.id
    # message_id = message.id
    # invite_all_codes = InviteCodeService.get_all_invite_codes(code_type="renew", is_used=False)
    # invite_code_list = []
    # for invite_code in invite_all_codes:
    #     invite_code_list.append(invite_code.code)
    # text, markup = create_pagination(chat_id, message_id, invite_code_list, items_per_page=50)
    # bot.send_message(chat_id, text, reply_markup=markup)


def toggle_invite_code_system_command(message):
    """开启/关闭邀请码系统 (管理员命令)"""
    try:
        settings.INVITE_CODE_SYSTEM_ENABLED = not settings.INVITE_CODE_SYSTEM_ENABLED
        logger.info(f"邀请码系统状态已更改: {settings.INVITE_CODE_SYSTEM_ENABLED}")
        bot.reply_to(message, f"邀请码系统已{'开启' if settings.INVITE_CODE_SYSTEM_ENABLED else '关闭'}")

    except ValueError:
        bot.reply_to(message, "邀请码系统状态更改失败，请重试！")
        logger.error(f"邀请码系统状态更改失败: telegram_id={message.from_user.id}")


@confirmation_required("你确定要设置积分嘛？")
def set_score_command(message):
    """
    设置用户积分 (管理员命令)
    /set_score <telegram_id> <score>
    """
    telegram_id = message.from_user.id
    service_type = settings.SERVICE_TYPE

    logger.info(f"管理员设置用户积分: telegram_id={telegram_id}, service_type={service_type}")

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "参数错误，请提供用户 Telegram ID 和积分数，格式为：/set_score <telegram_id> <score>")
        return

    try:
        target_telegram_id, score = args
        target_telegram_id = int(target_telegram_id)
        score = int(score)
    except ValueError:
        bot.reply_to(message, "参数错误，用户 Telegram ID 和积分数必须是整数！")
        return
    try:
        # 查找本地数据库中的用户
        user = UserService.get_user_by_telegram_id(target_telegram_id, service_type)
        if user:
            # 调用服务层的设置用户积分方法
            user = ScoreService.update_user_score(user.id, score)
            if user:
                logger.info(f"用户积分设置成功: user_id={user.id}, score={user.score}")
                bot.reply_to(message, f"用户 {target_telegram_id} 的积分已设置为: {score}")
            else:
                logger.error(f"用户积分设置失败: telegram_id={target_telegram_id}")
                bot.reply_to(message, "设置积分失败，请重试！")
        else:
            logger.warning(f"用户不存在: telegram_id={target_telegram_id}, service_type={service_type}")
            bot.reply_to(message, f"未找到用户: {target_telegram_id}")
    except ValueError:
        bot.reply_to(message, "设置积分失败，请重试！")
        logger.error(f"设置积分失败: telegram_id={telegram_id}")


def get_score_command(message):
    """
    查看用户积分 (管理员命令)
    /score <telegram_id>
    """
    telegram_id = message.from_user.id
    service_type = settings.SERVICE_TYPE

    logger.info(f"管理员查看用户积分: telegram_id={telegram_id}, service_type={service_type}")

    args = message.text.split()
    if len(args) != 1:
        bot.reply_to(message, "参数错误，请提供用户 Telegram ID，格式为：/score <telegram_id>")
        return

    try:
        target_telegram_id = int(args[0])
    except ValueError:
        bot.reply_to(message, "参数错误，用户 Telegram ID 必须是整数！")
        return
    try:
        # 查找本地数据库中的用户
        user = UserService.get_user_by_telegram_id(target_telegram_id)
        if user:
            # 调用服务层的获取用户积分方法
            score = ScoreService.get_user_score(user.id)
            if score is not None:
                logger.info(f"用户积分查询成功: telegram_id={target_telegram_id}, score={score}")
                bot.reply_to(message, f"用户 {target_telegram_id} 的积分: {score}")
            else:
                logger.error(f"用户积分查询失败: telegram_id={target_telegram_id}")
                bot.reply_to(message, "查询积分失败，请重试！")
        else:
            logger.warning(f"用户不存在: telegram_id={target_telegram_id}, service_type={service_type}")
    except ValueError:
        bot.reply_to(message, "查询积分失败，请重试！")
        logger.error(f"查询积分失败: telegram_id={telegram_id}")


def add_score_command(message):
    """
    增加用户积分 (管理员命令)
    /add_score <telegram_id> <score>
    """
    telegram_id = message.from_user.id
    service_type = settings.SERVICE_TYPE

    logger.info(f"管理员增加用户积分: telegram_id={telegram_id}, service_type={service_type}")

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "参数错误，请提供用户 Telegram ID 和积分数，格式为：/add_score <telegram_id> <score>")
        return

    try:
        target_telegram_id, score = args
        target_telegram_id = int(target_telegram_id)
        score = int(score)
    except ValueError:
        bot.reply_to(message, "参数错误，用户 Telegram ID 和积分数必须是整数！")
        return
    try:
        # 查找本地数据库中的用户
        user = UserService.get_user_by_telegram_id(target_telegram_id, service_type)
        if user:
            # 调用服务层的增加用户积分方法
            user = ScoreService.add_score(user.id, score)
            if user:
                logger.info(f"用户积分增加成功: user_id={user.id}, score={user.score}")
                bot.reply_to(message, f"已为用户 {target_telegram_id} 增加积分: {score}")
            else:
                logger.error(f"用户积分增加失败: telegram_id={target_telegram_id}")
                bot.reply_to(message, "增加积分失败，请重试！")
        else:
            logger.warning(f"用户不存在: telegram_id={target_telegram_id}, service_type={service_type}")
            bot.reply_to(message, f"未找到用户: {target_telegram_id}")
    except ValueError:
        bot.reply_to(message, "增加积分失败，请重试！")
        logger.error(f"增加积分失败: telegram_id={telegram_id}")


def reduce_score_command(message):
    """
    减少用户积分 (管理员命令)
    /reduce_score <telegram_id> <score>
    """
    telegram_id = message.from_user.id
    service_type = settings.SERVICE_TYPE

    logger.info(f"管理员减少用户积分: telegram_id={telegram_id}, service_type={service_type}")
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "参数错误，请提供用户 Telegram ID 和积分数，格式为：/reduce_score <telegram_id> <score>")
        return

    try:
        target_telegram_id, score = args
        target_telegram_id = int(target_telegram_id)
        score = int(score)
    except ValueError:
        bot.reply_to(message, "参数错误，用户 Telegram ID 和积分数必须是整数！")
        return

    try:
        # 查找本地数据库中的用户
        user = UserService.get_user_by_telegram_id(target_telegram_id, service_type)
        if user:
            # 调用服务层的减少用户积分方法
            user = ScoreService.reduce_score(user.id, score)
            if user:
                logger.info(f"用户积分减少成功: user_id={user.id}, score={user.score}")
                bot.reply_to(message, f"已为用户 {target_telegram_id} 减少积分: {score}")
            else:
                logger.error(f"用户积分减少失败: telegram_id={target_telegram_id}")
                bot.reply_to(message, "减少积分失败，请重试！")
        else:
            logger.warning(f"用户不存在: telegram_id={target_telegram_id}, service_type={service_type}")
            bot.reply_to(message, f"未找到用户: {target_telegram_id}")
    except ValueError:
        bot.reply_to(message, "减少积分失败，请重试！")
        logger.error(f"减少积分失败: telegram_id={telegram_id}")


@confirmation_required("你确定要设置邀请码价格嘛？")
def set_price_command(message):
    """
    设置邀请码价格 (管理员命令)
    /set_price <price>
    """
    telegram_id = message.from_user.id
    logger.info(f"管理员设置邀请码价格: telegram_id={telegram_id}")

    args = message.text.split()
    if len(args) != 1:
        bot.reply_to(message, "参数错误，请提供价格，格式为：/set_price <price>")
        return

    try:
        price = int(args[0])
    except ValueError:
        bot.reply_to(message, "价格必须是整数！")
        return

    try:
        config_name = "INVITE_CODE_PRICE"  # 直接指定配置项
        # 更新配置
        setattr(settings, config_name, price)  # 只更新 config 对象中的值
        logger.info(f"配置项 {config_name} 已更新为 {price}")
        bot.reply_to(message, f"邀请码积分价格已更新为 {price}")
    except Exception as e:
        logger.error(f"配置项更新失败: {e}")
        bot.reply_to(message, "设置邀请码价格失败，请重试！")


def get_user_info_by_telegram_id_command(message):
    """
    根据 Telegram ID 查询用户信息 (管理员命令)
    /userinfo <telegram_id>
    """
    telegram_id = message.text
    service_type = settings.SERVICE_TYPE
    logger.info(f"管理员根据 Telegram ID 查询用户信息: telegram_id={telegram_id}, service_type={service_type}")

    try:
        target_telegram_id = int(telegram_id)
    except ValueError:
        bot.reply_to(message, "参数错误，用户 Telegram ID 必须是整数！")
        return
    try:
        # 查找本地数据库中的用户
        user = UserService.get_user_by_telegram_id(target_telegram_id)
        if user:
            logger.info(f"用户查询成功: telegram_id={target_telegram_id}, user_id={user.id}")
            response = f"用户信息如下：\n" \
                       f"Telegram ID: {user.telegram_id}\n" \
                       f"用户名: {user.username}\n" \
                       f"积分: {user.score}\n" \
                       f"状态: {user.status}\n" \
                       f"本地数据库ID: {user.id}\n" \
                       f"服务器用户ID: {user.service_user_id}"
            bot.reply_to(message, response)
        else:
            logger.warning(f"用户不存在: telegram_id={target_telegram_id}, service_type={service_type}")
            bot.reply_to(message, f"未找到用户: {target_telegram_id}")
    except ValueError:
        bot.reply_to(message, "查询用户信息失败，请重试！")
        logger.error(f"查询用户信息失败: telegram_id={telegram_id}")


def get_user_info_by_username_command(message):
    """
    根据用户名查询用户信息 (管理员命令)
    /userinfo_by_username <username>
    """
    telegram_id = message.from_user.id
    service_type = settings.SERVICE_TYPE
    logger.info(f"管理员根据用户名查询用户信息: telegram_id={telegram_id}, service_type={service_type}")
    args = message.text.split()
    if len(args) != 1:
        bot.reply_to(message, "参数错误，请提供用户名，格式为：/userinfo_by_username <username>")
        return

    username = args[0]
    try:
        # 在本地数据库中查找用户
        user = UserService.get_user_by_username(username)
        if user:
            logger.info(f"用户查询成功: username={username}, user_id={user.id}")
            response = f"用户信息如下：\n" \
                       f"Telegram ID: {user.telegram_id}\n" \
                       f"用户名: {user.username}\n" \
                       f"积分: {user.score}\n" \
                       f"本地数据库ID: {user.id}\n" \
                       f"Navidrome用户ID: {user.service_user_id}"
            bot.reply_to(message, response)
            return

        # 如果没有找到用户，返回错误信息
        else:
            bot.reply_to(message, f"未找到用户: {username}")
            logger.warning(f"未找到用户: username={username}")

    except ValueError:
        bot.reply_to(message, "查询用户信息失败，请重试！")
        logger.error(f"查询用户信息失败: telegram_id={telegram_id}")


def get_stats_command(message):
    """
    获取统计信息 (管理员命令)
    /stats
    """
    telegram_id = message.from_user.id
    service_type = 'navidrome'
    logger.info(f"管理员查询统计信息: telegram_id={telegram_id}, service_type={service_type}")

    try:
        # 获取本地数据库用户数量
        users = UserService.get_all_users()
        local_user_count = len(users) if users else 0

        # 获取 Navidrome 用户数量
        navidrome_users = service_api_client.get_users()
        web_user_count = navidrome_users['headers']['x-total-count']
        # 获取 Navidrome 歌曲总数
        songs = service_api_client.get_songs()
        song_count = int(songs['x-total-count']) if songs and 'x-total-count' in songs else 0

        # 获取 Navidrome 专辑总数
        albums = service_api_client.get_albums()
        album_count = int(albums['x-total-count']) if albums and 'x-total-count' in albums else 0

        # 获取 Navidrome 艺术家总数
        artists = service_api_client.get_artists()
        artist_count = int(artists['x-total-count']) if artists and 'x-total-count' in artists else 0

        # 获取 Navidrome 电台总数
        radios = service_api_client.get_radios()
        radio_count = int(radios['x-total-count']) if radios and 'x-total-count' in radios else 0

        response = f"统计信息:\n" \
                   f"本地数据库注册用户数量: {local_user_count}\n" \
                   f"Navidrome Web 应用用户数量: {web_user_count}\n"
        response += f"-------\n"
        response += f"Navidrome 歌曲总数: {song_count}\n"
        response += f"Navidrome 专辑总数: {album_count}\n"
        response += f"Navidrome 艺术家总数: {artist_count}\n"
        response += f"Navidrome 电台总数: {radio_count}\n"
        response += f"-------\n"
        response += f"清理系统的状态为：{settings.ENABLE_EXPIRED_USER_CLEAN}\n"
        response += f"邀请码系统的状态为：{settings.INVITE_CODE_SYSTEM_ENABLED}\n"
        bot.reply_to(message, response)
        logger.info(
            f"管理员获取注册状态成功: telegram_id={telegram_id}, 本地注册用户数量={local_user_count},  Navidrome Web 应用用户数量={web_user_count}, 歌曲总数={song_count}, 专辑总数={album_count}, 艺术家总数={artist_count}, 电台总数={radio_count}")
    except Exception as e:
        logger.error(f"获取注册状态失败: telegram_id={telegram_id}, error={e}")
        bot.reply_to(message, "获取注册状态失败，请重试！")


@confirmation_required("你确定要更改清理用户系统状态嘛？")
def toggle_expired_user_clean_command(message):
    """开启/关闭过期用户清理定时任务 (管理员命令)"""
    settings.ENABLE_EXPIRED_USER_CLEAN = not settings.ENABLE_EXPIRED_USER_CLEAN
    logger.debug(f'清理系统的状态为：{settings.ENABLE_EXPIRED_USER_CLEAN}')

    UserService.start_clean_expired_users()

    logger.info(f"过期用户清理定时任务已更改: {settings.ENABLE_EXPIRED_USER_CLEAN}")
    bot.reply_to(message, f"过期用户清理定时任务已{'开启' if settings.ENABLE_EXPIRED_USER_CLEAN else '关闭'}")


def get_expired_users_command(message):
    """获取已过期的用户 (管理员命令)"""
    telegram_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.id
    logger.info(f"管理员请求获取已过期的用户列表: telegram_id={telegram_id}")

    settings.EXPIRED_DAYS = 30
    settings.WARNING_DAYS = 27
    args = message.text.split()

    if len(args) == 1:
        logger.info(f"{settings.EXPIRED_DAYS}天未使用服务的用户列表")
    elif len(args) == 2:
        try:
            day = int(args[0])
        except ValueError:
            bot.reply_to(message, "参数错误，DAY必须是整数！")
            return
        settings.EXPIRED_DAYS = day
        logger.info(f"获取距离现在已经{args[0]}天未使用服务的用户名单")
    else:
        bot.reply_to(message, "参数错误，请提供整数格式的过期时间！")
        return

    expired_users = UserService.get_expired_users()

    if expired_users and 'expired' in expired_users and expired_users['expired']:
        expired_users_list = paginate_list(data_list=expired_users['expired'], page_size=50)
        # expired_users_list = paginate_list_text(data_list=expired_users['expired'])
        for expired_users in expired_users_list:
            response = "已经过期用户列表：\n"
            response += f"-----------\n"
            for expired_user in expired_users:
                response += f"{expired_user['username']}\n"
            response += f"-----------\n"
            response += f"已经过期的用户一共有：{len(expired_users)}位！\n"
            bot.reply_to(message, response)
        # expired_username_list = []
        # for expired_user in expired_users['expired']:
        #     expired_username_list.append(expired_user['username'])

        # text, markup = create_pagination(chat_id, message_id, expired_username_list, items_per_page=50)
        # bot.send_message(chat_id, text, reply_markup=markup)
        logger.warning(f"管理员获取已经过期的用户列表成功: 共有{len(expired_users)}位！")
    else:
        bot.reply_to(message, "没有已经过期的用户!")
        logger.info(f"没有已经过期的用户: telegram_id={telegram_id}")


def get_expiring_users_command(message):
    """获取即将过期的用户 (管理员命令)"""
    telegram_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.id
    logger.info(f"管理员请求获取即将过期的用户列表: telegram_id={telegram_id}")

    settings.EXPIRED_DAYS = 30
    settings.WARNING_DAYS = 27

    args = message.text.split()

    if len(args) == 1:
        logger.info(f"获取{settings.WARNING_DAYS}天后将过期的用户名单")
    elif len(args) == 2:
        try:
            day = int(args[0])
        except ValueError:
            bot.reply_to(message, "参数错误，DAY必须是整数！")
            return
        settings.WARNING_DAYS = day
        logger.info(f"获取{args[0]}天后将过期的用户名单")
    else:
        bot.reply_to(message, "参数错误，请提供整数格式的过期时间！")
        return

    expiring_users = UserService.get_expired_users()

    if expiring_users and 'warning' in expiring_users and expiring_users['warning']:
        expiring_users_list = paginate_list(data_list=expiring_users['warning'], page_size=50)
        # expiring_users_list = paginate_list_text(data_list=expiring_users['warning'])
        for expiring_users in expiring_users_list:
            response = "即将过期用户列表：\n"
            response += f"-----------\n"
            for expiring_user in expiring_users:
                response += f"{expiring_user['username']}\n"
            response += f"-----------\n"
            response += f"即将过期的用户一共有：{len(expiring_users)}位！\n"
            bot.reply_to(message, response)
        # expiring_username_list = []
        # for expired_user in expiring_users['warning']:
        #     expiring_username_list.append(expired_user['username'])

        # text, markup = create_pagination(chat_id, message_id, expiring_username_list, items_per_page=50)
        # bot.send_message(chat_id, text, reply_markup=markup)
        logger.warning(f"管理员获取即将过期的用户列表成功: 共有{len(expiring_users)}位！")
    else:
        bot.reply_to(message, "没有即将过期的用户!")
        logger.info(f"没有即将过期的用户: telegram_id={telegram_id}")


@confirmation_required("你确定要清理用户嘛？")
def clean_expired_users_command(message):
    """立即清理过期用户 (管理员命令)"""
    telegram_id = message.from_user.id
    logger.info(f"管理员请求清理过期用户: telegram_id={telegram_id}")

    settings.EXPIRED_DAYS = 30
    settings.WARNING_DAYS = 3

    args = message.text.split()

    if len(args) == 1:
        logger.info(f"清理30天未使用的用户")
    elif len(args) == 2:
        try:
            day = int(args[0])
        except ValueError:
            bot.reply_to(message, "参数错误，DAY必须是整数！")
            return
        settings.EXPIRED_DAYS = day
        logger.info(f"清理{day}天未使用的用户")
    else:
        bot.reply_to(message, "参数错误，请提供整数格式的过期时间！")
        return

    user_list = UserService.clean_expired_users()
    if user_list:
        bot.reply_to(message, f"已执行过期用户清理,一共清理用户{len(user_list)}位！")
        logger.info(f"管理员清理过期用户成功: telegram_id={telegram_id}")
    else:
        bot.reply_to(message, "未发现过期用户！")
        logger.info(f"没有用户过期！")


def random_give_score_by_checkin_time_command(message):
    """
    根据签到时间给用户随机增加积分 (管理员命令)
    /random_give_score_by_checkin_time <today|yesterday|2025-01-01>[可选] <max_score>[可选]
    """
    telegram_id = message.from_user.id
    logger.info(f"管理员请求根据签到时间随机增加用户积分: telegram_id={telegram_id}")

    args = message.text.split()
    logger.debug(f"参数为{args}")
    max_score = 10
    user_range = "today"

    if len(args) == 0:
        logger.info("为今天所有签到的用户增加随机积分，最大积分为10分！")
        users = UserService.get_sign_in_users(user_range)
    elif len(args) == 1:
        logger.info(f"为今天签到所有签到的用户增加随机积分，最大积分为{max_score}分！")
        max_score = args[0]
        users = UserService.get_sign_in_users(user_range)
    elif len(args) == 2:
        logger.info(f"为{user_range}内所有签到的用户增加随机积分，最大积分为{max_score}分！")
        user_range, max_score = args
        users = UserService.get_sign_in_users(user_range)
    else:
        bot.reply_to(message,
                     "参数错误，请提供签到时间范围和最大积分数，格式为：/random_give_score_by_checkin_time <all|today|yesterday|weekly|month> "
                     "<max_score>")
        return

    try:
        max_score = int(max_score)
    except ValueError:
        bot.reply_to(message, "参数错误，最大积分数必须是整数！")
        return

    if users:
        for user in users:
            score = ScoreService._generate_random_score(max_score=max_score)
            ScoreService.add_score(user_id=user.id, score=score)
            logger.info(f"为用户增加随机积分: telegram_id={telegram_id}, score={score}, range={user_range}")
        bot.reply_to(message, f"已为{len(users)}个用户随机增加积分，范围: {user_range}，最大积分: {max_score}!")
    else:
        bot.reply_to(message, "没有用户符合条件，无法增加积分")
        logger.info(f"没有用户符合条件，无法增加积分, range={user_range}")


@confirmation_required(message_text="你确定要普天同庆吗？该过程较慢，Bot响应会比较慢。")
def add_random_score_command(message):
    """
    根据注册时间范围给用户随机增加积分 (管理员命令)
     /add_random_score <start_time> <end_time> <max_score>
     start_time和end_time格式必须是 YYYY-MM-DD
    """
    telegram_id = message.from_user.id
    logger.info(f"管理员请求根据注册时间范围随机增加用户积分: telegram_id={telegram_id}")
    args = message.text.split()
    max_score = 10
    if len(args) == 0:
        logger.info(f"为注册的所有用户增加随机积分！最大积分为10分")
        users = UserService.get_users_by_register_time()
    elif len(args) == 1:
        max_score = args[0]
        logger.info(f"为注册的所有用户增加随机积分！最大积分为{max_score}")
        users = UserService.get_users_by_register_time()
    elif len(args) == 2:
        start_time, end_time = args
        logger.info(f"为{start_time}-{end_time}期间注册所有用户增加随机积分！最大积分为10分")
        start_time, end_time = args
        users = UserService.get_users_by_register_time(start_time, end_time)
    elif len(args) == 3:
        start_time, end_time, max_score = args
        logger.info(f"为{start_time}-{end_time}期间注册所有用户增加随机积分！最大积分为{max_score}分")
        users = UserService.get_users_by_register_time(start_time, end_time)
    else:
        logger.warning(f"提供的参数错误！")
        bot.reply_to(message,
                     "参数错误，请提供注册时间范围的开始时间、结束时间和最大积分数，格式为：/random_give_score_by_range_time <start_time>[可选] <end_time>[可选] <max_score>[可选]")

    try:
        max_score = int(max_score)
    except ValueError:
        bot.reply_to(message, "参数错误，最大积分数必须是整数！")
        return

    users = UserService.get_users_by_register_time(start_time, end_time)
    if users:
        for user in users:
            score = ScoreService._generate_random_score(max_score=max_score)
            ScoreService.add_score(user_id=user.id, score=score)
            logger.info(f"为用户增加随机积分: telegram_id={telegram_id}, score={score}")
        bot.reply_to(message, f"已为{len(users)}个用户随机增加积分, 最大积分: {max_score}!")
    else:
        bot.reply_to(message, "没有用户符合条件，无法增加积分")
        logger.info(f"没有用户符合条件，无法增加积分，start_time={start_time}, end_time={end_time}")


def get_user_info_in_server_command(message):
    """
    获取服务器上的用户信息 (管理员命令)
    /user_info_in_server <username>
    """
    telegram_id = message.from_user.id
    service_type = settings.SERVICE_TYPE
    logger.info(f"管理员获取服务器上的用户信息: telegram_id={telegram_id}, service_type={service_type}")

    args = message.text.split()
    if len(args) != 1:
        bot.reply_to(message, "参数错误，请提供用户名，格式为：/user_info_in_server <username>")
        return

    username = args[0]
    # 调用服务层的获取服务器上用户信息方法
    user_info = UserService.get_info_in_server(username)
    if user_info:
        logger.info(f"获取服务器上用户信息成功: username={username}")
        response = f"用户信息如下：\n" \
                   f"用户名: {user_info['userName']}\n" \
                   f"注册时间: {user_info['createdAt']}\n" \
                   f"最后登录时间: {user_info['lastLoginAt']}\n" \
                   f"最后使用时间: {user_info['lastAccessAt']}\n" \
                   f"Service User ID: {user_info['id']}\n"
        bot.reply_to(message, response)
    else:
        logger.warning(f"获取服务器上用户信息失败: username={username}")
        bot.reply_to(message, f"未找到用户: {username}")


def get_score_chart_command(message):
    """
    获取积分排行榜 (管理员命令)
    /get_score_chart <num>
    """
    telegram_id = message.from_user.id
    logger.info(f"管理员请求获取积分排行榜: telegram_id={telegram_id}")

    args = message.text.split()
    limit = 10  # 默认10
    if len(args) > 0:
        try:
            limit = int(args[0])
        except ValueError:
            bot.reply_to(message, "参数错误，排行榜用户数量必须是整数！")
            return

    score_chart = UserService.get_score_chart(limit=limit)
    if score_chart:
        response = "🏆 *积分排行榜*\n"
        response += f"排名 | 用户名 | 积分\n"
        response += "--------------------\n"
        for user_info in score_chart:
            response += f"第 {user_info['rank']} 名  *{user_info['username']}*  {user_info['score']}分\n"
        bot.reply_to(message, response, parse_mode="Markdown")
        logger.info(f"管理员获取积分排行榜成功: telegram_id={telegram_id}, 用户数量={limit}")
    else:
        bot.reply_to(message, "获取排行榜失败，没有用户或发生错误！")
        logger.warning(f"获取积分排行榜失败: telegram_id={telegram_id}")


def toggle_clean_msg_system_command(message):
    """开启/关闭清理消息系统 (管理员命令)"""
    settings.ENABLE_MESSAGE_CLEANER = not settings.ENABLE_MESSAGE_CLEANER
    logger.info(f"消息清理系统已更改: {settings.ENABLE_MESSAGE_CLEANER}")
    message_cleaner = get_message_cleaner()
    if settings.ENABLE_MESSAGE_CLEANER:
        message_cleaner.start()  # 启动消息清理器
        logger.info(f"消息管理器已启动！")
    else:
        message_cleaner.stop()
        logger.info(f"消息管理器已关闭！")
    bot.reply_to(message, f"消息清理系统已{'开启' if settings.ENABLE_MESSAGE_CLEANER else '关闭'}")


def block_user_command(message):
    """封禁用户 (管理员命令)"""
    telegram_id = message.from_user.id
    logger.info(f"管理员请求封禁用户: telegram_id={telegram_id}")

    args = message.text.split()
    if len(args) != 1:
        bot.reply_to(message, "参数错误，请提供用户 Telegram ID，格式为：/block_user <telegram_id>/username")
        return

    target_input = args[0]

    try:
        # 尝试将输入转换为整数（Telegram ID）
        target_telegram_id = int(target_input)
        user = UserService.get_user_by_telegram_id(target_telegram_id)
    except ValueError:
        # 如果输入不是整数，则尝试按用户名查找
        user = UserService.get_user_by_username(target_input)

    try:
        # 查找本地数据库中的用户
        if user:
            # 调用服务层的封禁用户方法
            user = UserService.block_user(user.id)
            if user:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text="封禁", callback_data=f"block_server_user_{user.id}"))
                logger.info(f"用户封禁成功: user_id={user.id}")
                bot.reply_to(message, f"用户 {target_telegram_id} 已封禁, 同时封禁使用服务器账号？", reply_markup=markup)
            else:
                logger.error(f"用户封禁失败: telegram_id={target_telegram_id}")
                bot.reply_to(message, "封禁用户失败，请重试！")
        else:
            logger.warning(f"用户不存在: telegram_id={target_telegram_id}")
            bot.reply_to(message, f"未找到用户: {target_telegram_id}")
    except ValueError:
        bot.reply_to(message, "封禁用户失败，请重试！")
        logger.error(f"封禁用户失败: telegram_id={telegram_id}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('block_server_user_'))
def block_server_user_callback(call):
    """封禁服务器用户"""
    telegram_id = call.from_user.id
    logger.info(f"管理员请求封禁服务器用户: telegram_id={telegram_id}")

    user_id = call.data.split('_')[-1]
    user = UserService.get_user_by_id(user_id)
    if user:
        # 调用服务层的封禁服务器用户方法
        user = UserService.block_server_user(user.id)
        if user:
            logger.info(f"服务器用户封禁成功: user_id={user.id}")
            bot.reply_to(call.message, f"服务器用户 {user.username} 已封禁")
        else:
            logger.error(f"服务器用户封禁失败: user_id={user.id}")
            bot.reply_to(call.message, "封禁服务器用户失败，请重试！")
    else:
        logger.warning(f"用户不存在: user_id={user_id}")
        bot.reply_to(call.message, f"未找到用户: {user_id}")


def unblock_user_command(message):
    """解封用户 (管理员命令)"""
    telegram_id = message.from_user.id
    logger.info(f"管理员请求解封用户: telegram_id={telegram_id}")

    args = message.text.split()
    if len(args) != 1:
        bot.reply_to(message, "参数错误，请提供用户 Telegram ID，格式为：/unblock_user <telegram_id>/username")
        return

    target_input = args[0]

    try:
        # 尝试将输入转换为整数（Telegram ID）
        target_telegram_id = int(target_input)
        user = UserService.get_user_by_telegram_id(target_telegram_id)
    except ValueError:
        # 如果输入不是整数，则尝试按用户名查找
        user = UserService.get_user_by_username(target_input)

    try:
        # 查找本地数据库中的用户
        if user:
            # 调用服务层的解封用户方法
            user = UserService.unblock_user(user.id)
            if user:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text="解封", callback_data=f"unblock_server_user_{user.id}"))
                logger.info(f"用户解封成功: user_id={user.id}")
                bot.reply_to(message, f"用户 {target_telegram_id} 已解封, 同时解封使用服务器账号？", reply_markup=markup)
            else:
                logger.error(f"用户解封失败: telegram_id={target_telegram_id}")
                bot.reply_to(message, "解封用户失败，请重试！")
        else:
            logger.warning(f"用户不存在: telegram_id={target_telegram_id}")
            bot.reply_to(message, f"未找到用户: {target_telegram_id}")
    except ValueError:
        bot.reply_to(message, "解封用户失败，请重试！")
        logger.error(f"解封用户失败: telegram_id={telegram_id}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('unblock_server_user_'))
def unblock_server_user_callback(call):
    """解封服务器用户"""
    telegram_id = call.from_user.id
    logger.info(f"管理员请求解封服务器用户: telegram_id={telegram_id}")

    user_id = call.data.split('_')[-1]
    user = UserService.get_user_by_id(user_id)
    if user:
        # 调用服务层的解封服务器用户方法
        user = UserService.unblock_server_user(user.id)
        if user:
            logger.info(f"服务器用户解封成功: user_id={user.id}")
            bot.reply_to(call.message, f"服务器用户 {user.username} 已解封")
        else:
            logger.error(f"服务器用户解封失败: user_id={user.id}")
            bot.reply_to(call.message, "解封服务器用户失败，请重试！")
    else:
        logger.warning(f"用户不存在: user_id={user_id}")
        bot.reply_to(call.message, f"未找到用户: {user_id}")


def get_block_users(message):
    """获取被封禁的用户 (管理员命令)"""
    telegram_id = message.from_user.id
    logger.info(f"管理员请求获取被封禁的用户: telegram_id={telegram_id}")

    try:
        # 调用服务层的获取被封禁用户方法
        block_users = UserService.get_block_users()
        if block_users:
            response = "被封禁的用户列表：\n"
            response += f"-----------\n"
            for block_user in block_users:
                response += f"{block_user['username']} - {block_user['telegram_id']}\n"
            response += f"-----------\n"
            response += f"被封禁的用户一共有：{len(block_users)}位！\n"
            bot.reply_to(message, response)
            logger.warning(f"管理员获取被封禁的用户列表成功: 共有{len(block_users)}位！")
        else:
            bot.reply_to(message, "没有被封禁的用户!")
            logger.info(f"没有被封禁的用户: telegram_id={telegram_id}")
    except ValueError:
        bot.reply_to(message, "获取被封禁用户失败，请重试！")
        logger.error(f"获取被封禁用户失败: telegram_id={telegram_id}")


def set_whitelist_user(message):
    """设置用户白名单状态"""
    telegram_id = message.from_user.id
    logger.info(f"管理员请求设置用户白名单：telegram_id={telegram_id}")

    args = message.text.split()
    if len(args) != 1:
        bot.reply_to(message, "参数错误，请提供用户 Telegram ID，格式为：<telegram_id>/username")
        return

    target_input = args[0]

    try:
        # 尝试将输入转换为整数（Telegram ID）
        target_telegram_id = int(target_input)
        user = UserService.get_user_by_telegram_id(target_telegram_id)
    except ValueError:
        # 如果输入不是整数，则尝试按用户名查找
        user = UserService.get_user_by_username(target_input)

    try:
        if user:
            white_user = UserService.set_user_status(user.id, "whitelist")
            bot.reply_to(message, f"用户{white_user.username}已被设置为白名单用户！")
            logger.info(f"已设置用户白名单！")
        else:
            bot.reply_to(message, f"未找到用户！")
    except ValueError:
        bot.reply_to(message, "设置用户白名单失败，请重试！")
        logger.error(f"设置用户白名单失败：telegram_id={telegram_id}")


def get_user_status(message):
    """获取用户状态"""
    telegram_id = message.from_user.id
    logger.info(f"管理员请求过去用户状态：telegram_id={telegram_id}")

    args = message.text.split()
    if len(args) != 1:
        bot.reply_to(message, "参数错误，请提供用户 Telegram ID，格式为：<telegram_id>/username")
        return

    target_input = args[0]

    try:
        # 尝试将输入转换为整数（Telegram ID）
        target_telegram_id = int(target_input)
        user = UserService.get_user_by_telegram_id(target_telegram_id)
    except ValueError:
        # 如果输入不是整数，则尝试按用户名查找
        user = UserService.get_user_by_username(target_input)

    bot.reply_to(message, f"用户状态：{user.status}\n\n 用户Telegram_ID：{user.telegram_id}")