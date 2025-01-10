# 校验器
from functools import wraps
from app.services.user_service import UserService
from app.services.invite_code_service import InviteCodeService
from app.utils.logger import logger
from datetime import datetime, timedelta
from app.bot.core.bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.utils.message_queue import get_message_queue
from config import settings


message_queue = get_message_queue()

# 需要安装的模块：无

def user_exists(service_type, negate=False):
    """
    验证用户是否存在于本地数据库的装饰器
     Args:
        service_type: 服务名称，例如 "navidrome"
        negate: 是否取反，默认为 False
    """
    def decorator(func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            logger.info(f"message: {message}")
            telegram_id = message.from_user.id
            logger.debug(f"校验用户是否存在于本地数据库: telegram_id={telegram_id}, service_type={service_type}, negate={negate}")

            user = UserService.get_user_by_telegram_id(telegram_id=telegram_id)
            
            # if user and user.service_user_id == None and user.invite_code == None:
            #     logger.debug(f"已有积分用户")
            #     # bot.reply_to(message, f"已有积分账户，请使用 更新用户 即可！")
            #     return func(message, *args, **kwargs)
            
            # if user and user.invite_code != None:
            #     logger.debug(f"已使用过邀请码注册")
            #     # bot.reply_to(message, f"已使用过邀请码注册，请使用 更新用户 即可！")
            #     return func(message, *args, **kwargs)
            
            if (user and not negate) or (not user and negate):
                logger.debug(f"用户校验通过: telegram_id={telegram_id}, service_type={service_type}, negate={negate}, user_exists={bool(user)}")
                return func(message, *args, **kwargs)
            else:
                logger.warning(f"用户校验失败: telegram_id={telegram_id}, service_type={service_type}, negate={negate}, user_exists={bool(user)}")
                bot.reply_to(message, "未找到您的账户信息!" if not negate else "您已注册，请勿重复注册！如想重新注册，请先执行/deleteuser删除本地用户再注册!")
                return

        return wrapper
    return decorator

def user_exist_local(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        telegram_id = message.from_user.id
        logger.debug(f"校验用户是否是积分用户或者使用过邀请码用户: telegram_id={telegram_id}")

        user = UserService.get_user_by_telegram_id(telegram_id=telegram_id)
        
        if user:
            if user.service_user_id == None and user.invite_code == None:
                logger.debug(f"已有积分用户")
                bot.reply_to(message, f"已有积分账户，请使用 更新用户 即可！")
                return
            elif user.service_user_id == None and user.invite_code != None:
                logger.debug(f"已有邀请码用户")
                bot.reply_to(message, f"已有邀请码账户，请使用 更新用户 即可！")
                return 
            else:
                logger.warning(f"用户校验通过: telegram_id={telegram_id}")
                return func(message, *args, **kwargs)
        else:
            logger.info(f"用户校验通过")
            return func(message, *args, **kwargs)
    return wrapper

def admin_required(func):
    """
    验证用户是否是管理员的装饰器
    """
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        telegram_id = message.from_user.id # 修改获取 telegram_id 的方式
        logger.debug(f"校验用户是否是管理员: telegram_id={telegram_id}")
        if UserService.is_admin(telegram_id):
            logger.debug(f"用户是管理员: telegram_id={telegram_id}")
            return func(message, *args, **kwargs)
        else:
            logger.warning(f"用户不是管理员: telegram_id={telegram_id}")
            bot.reply_to(message, "你没有权限执行此操作!")
            return
    return wrapper

def invite_system_enabled(func):
    """
    邀请系统是否开启的校验装饰器
    """
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        # 检查邀请系统是否开启
        if not settings.INVITE_CODE_SYSTEM_ENABLED:
            logger.debug("邀请系统未开启，跳过邀请码验证")
            return func(message, *args, **kwargs)
        
        # 如果邀请系统开启，继续执行原逻辑
        logger.debug("邀请系统已开启，继续执行邀请码验证")
        bot.reply_to(message, "邀请系统已开启，请使用邀请码注册")
        return
    return wrapper

def invite_code_valid(func):
    """
    验证邀请码是否有效的装饰器
    """
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        
        code = message.text.strip()
        logger.debug(f"校验邀请码是否有效: code={code}")
        if not code:
            logger.warning("未提供邀请码")
            bot.reply_to(message, "请提供邀请码!")
            return

        # 验证邀请码
        invite_code = InviteCodeService.get_invite_code(code)
        expire_time = invite_code.create_time + timedelta(days=invite_code.expire_days)
        if invite_code and not invite_code.is_used and expire_time > datetime.now():
            logger.debug(f"邀请码有效: code={code}")
            # 邀请码有效，继续执行原函数
            return func(message, *args, **kwargs)
        else:
            logger.warning(f"邀请码无效: code={code}")
            bot.reply_to(message, "邀请码无效!")
            return

    return wrapper

def score_enough(service_type):
    """
    验证用户积分是否足够的装饰器

    Args:
        service_type: 服务名称
    """
    def decorator(func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            telegram_id = message.from_user.id  # 修改获取 telegram_id 的方式
            # 通过消息的文本内容获取需要的积分数量
            required_score = int(message.text.split(" ")[-1]) if len(message.text.split(" ")) > 1 else 0

            logger.debug(f"校验用户积分是否足够: telegram_id={telegram_id}, required_score={required_score}")
            user = UserService.get_user_by_telegram_id(telegram_id=telegram_id)

            if user and user.score >= required_score:
                logger.debug(f"用户积分足够: telegram_id={telegram_id}, score={user.score}, required_score={required_score}")
                return func(message, *args, **kwargs)
            else:
                logger.warning(f"用户积分不足: telegram_id={telegram_id}, score={user.score if user else 0}, required_score={required_score}")
                bot.reply_to(message, "积分不足!")
                return

        return wrapper
    return decorator
  
# 用于存储用户会话信息
user_sessions = {}

def confirmation_required(message_text):
    def decorator(func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            chat_id = message.chat.id

            # 创建内联键盘
            markup = InlineKeyboardMarkup()
            button_yes = InlineKeyboardButton("是", callback_data=f"confirm_yes_{chat_id}")
            button_no = InlineKeyboardButton("否", callback_data=f"confirm_no_{chat_id}")
            markup.add(button_yes, button_no)

            # 发送自定义的确认消息和键盘
            bot.send_message(chat_id, message_text, reply_markup=markup)
            # logger.info(f"msg: {msg.message_id}")
            # logger.info(f"yes: {message.message_id}")
            # 保存当前的命令函数和参数到会话
            user_sessions[chat_id] = {'message': message, 'func': func, 'args': args, 'kwargs': kwargs}

        return wrapper
    return decorator

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm'))
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data
    if chat_id in user_sessions:
        # 获取存储的函数信息
        command_info = user_sessions[chat_id]
        message = command_info['message']
        func = command_info['func']
        args = command_info['args']
        kwargs = command_info['kwargs']

        if data == f"confirm_yes_{chat_id}":
            # 用户选择“是”，执行原始命令
            func(message, *args, **kwargs)
            logger.debug("已确认，命令已执行")
        elif data == f"confirm_no_{chat_id}":
            # 用户选择“否”，取消操作
            logger.debug("已取消，命令已取消")
        # 清除会话信息
        if settings.ENABLE_MESSAGE_CLEANER:
            message_queue.add_message(user_sessions[chat_id]['message'])
        del user_sessions[chat_id]

    bot.answer_callback_query(call.id)
    if settings.ENABLE_MESSAGE_CLEANER:
      message_queue.add_message(call.message)

def private_chat_only(func):
    """
    限制命令只能在私聊中使用的装饰器
    """
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        telegram_id = message.from_user.id  # 获取 telegram_id
        if message.chat.type in ["group", "supergroup"]:  # 群组或超级群组
            logger.debug(f"在群组中收到命令，不响应: chat_id={message.chat.id}, telegram_id={telegram_id}")
            return # 在群组中不执行任何操作
        else:
             logger.debug(f"在私聊中收到命令，正常响应: chat_id={message.chat.id}, telegram_id={telegram_id}")
             return func(message, *args, **kwargs)
    return wrapper

def chat_type_required(not_chat_type=None):
    """
    限制命令只能在非指定 chat_type 使用的装饰器

    Args:
      not_chat_type: str | list 指定不允许的chat_type, 例如: ["private", "group", "supergroup"]
    """
    def decorator(func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            telegram_id = message.from_user.id
            if not_chat_type:
              if isinstance(not_chat_type, str):
                not_chat_type_list = [not_chat_type]
              else:
                not_chat_type_list = not_chat_type
              if message.chat.type in not_chat_type_list:  # 群组或超级群组
                  logger.debug(f"在{not_chat_type}中收到命令，不响应: chat_id={message.chat.id}, telegram_id={telegram_id}")
                  return
            
            logger.debug(f"在{message.chat.type}中收到命令，正常响应: chat_id={message.chat.id}, telegram_id={telegram_id}")
            return func(message, *args, **kwargs)
        return wrapper
    return decorator