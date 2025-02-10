import telebot
from app.utils.logger import logger
from app.bot.handlers import admin_panel, user_handlers, user_panel
from app.bot.core.bot_instance import bot
from config import settings


# 需要安装的模块：无

class BotManager:
    def __init__(self):
        self.bot = bot

        # 定义命令列表
        commands = [
            telebot.types.BotCommand("start", "开始"),
            telebot.types.BotCommand("line", "获取线路"),
            telebot.types.BotCommand("register", "注册用户 (需要提供用户名和密码)"),
            telebot.types.BotCommand("admin", "管理"),
            # telebot.types.BotCommand("reg_score_user", "注册积分用户 (可签到、送分、购买邀请码)"),
            # telebot.types.BotCommand("use_renew_code", "使用续期码"),
            # telebot.types.BotCommand("info", "查看个人信息"),
            # telebot.types.BotCommand("deleteuser", "删除用户"),
            # telebot.types.BotCommand("score", "查看我的积分"),
            # telebot.types.BotCommand("checkin", "签到"),
            # telebot.types.BotCommand("buyinvite", "购买邀请码"),
            # telebot.types.BotCommand("reset_password", "重置密码"),
            # telebot.types.BotCommand("reset_username", "重置用户名"),
            # telebot.types.BotCommand("give", "赠送积分"),
            telebot.types.BotCommand("random_score", "发送积分红包"),
            # telebot.types.BotCommand("bind", "绑定账号"),
            # telebot.types.BotCommand("unbind", "解绑账号"),
            # telebot.types.BotCommand("generate_code", "生成邀请码码 (管理员)"),
            # telebot.types.BotCommand("generate_renew_code", "生成续期码 (管理员)"),
            # telebot.types.BotCommand("renew_code", "生成邀请码 (管理员)"),
            # telebot.types.BotCommand("invite", "查看所有邀请码 (管理员)"),
            # telebot.types.BotCommand("unused_invite_codes", "查看所有未使用邀请码 (管理员)"),
            # telebot.types.BotCommand("unused_renew_codes", "查看所有未使用续期码 (管理员)"),
            # telebot.types.BotCommand("set_score", "设置用户积分 (管理员)"),
            # telebot.types.BotCommand("get_score", "查看用户积分 (管理员)"),
            # telebot.types.BotCommand("add_score", "增加用户积分 (管理员)"),
            # telebot.types.BotCommand("reduce_score", "减少用户积分 (管理员)"),
            # telebot.types.BotCommand("set_price", "设置积分价格 (管理员)"),
            # telebot.types.BotCommand("add_random_score", "为符合条件的用户增加随机积分 (管理员)"),
            # telebot.types.BotCommand("random_score_by_checkin", "为签到用户增加随机积分 (管理员)"),
            # telebot.types.BotCommand("userinfo", "获取用户信息 (管理员)"),
            # telebot.types.BotCommand("userinfo_by_username", "通过用户名获取用户信息 (管理员)"),
            # telebot.types.BotCommand("userinfo_in_server", "通过用户名获取用户信息 (管理员)"),
            # telebot.types.BotCommand("stats", "获取注册状态 (管理员)"),
            # telebot.types.BotCommand("get_score_chart", "积分排行榜 (管理员)"),
            # telebot.types.BotCommand("toggle_invite_code_system", "开启/关闭邀请码系统 (管理员)"),
            # telebot.types.BotCommand("toggle_expired_user_clean", "切换自动清理状态 (管理员)"),
            # telebot.types.BotCommand("toggle_clean_msg_system", "切换自动清除消息 (管理员)"),
            # telebot.types.BotCommand("get_expiring_users", "获取不活跃的用户 (管理员)"),
            # telebot.types.BotCommand("get_expired_users", "获取已过期的用户 (管理员)"),
            # telebot.types.BotCommand("clean_expired_users", "清理不活跃的用户 (管理员)")

        ]
        # 设置Bot命令
        self.bot.set_my_commands(commands)

        # 注册路由
        bot.register_message_handler(user_handlers.get_line_command, commands=['line'])
        bot.register_message_handler(user_panel.start_panel_command, commands=['start'])

        bot.register_message_handler(admin_panel.admin_panel_command, commands=['admin'])
        # bot.register_message_handler(user_handlers.start_command, commands=['start'])
        # bot.register_message_handler(user_handlers.start_command, commands=['start'])
        bot.register_message_handler(user_handlers.register_user_command, commands=['register'])
        # bot.register_message_handler(user_handlers.reg_score_user_command, commands=['reg_score_user'])
        # # bot.register_message_handler(user_handlers.use_invite_code_command, commands=['use_code'])
        # bot.register_message_handler(user_handlers.info_command, commands=['info'])
        # bot.register_message_handler(user_handlers.delete_user_command, commands=['deleteuser'])
        # bot.register_message_handler(user_handlers.score_command, commands=['score'])
        # bot.register_message_handler(user_handlers.checkin_command, commands=['checkin'])
        # bot.register_message_handler(user_handlers.buy_invite_code_command, commands=['buyinvite'])
        # bot.register_message_handler(user_handlers.use_renew_code_command, commands=['use_renew_code'])
        # bot.register_message_handler(user_handlers.reset_password_command, commands=['reset_password'])
        # bot.register_message_handler(user_handlers.reset_username_command, commands=['reset_username'])
        # bot.register_message_handler(user_handlers.give_score_command, commands=['give'])
        # bot.register_message_handler(user_handlers.bind_command, commands=['bind'])
        # bot.register_message_handler(user_handlers.unbind_command, commands=['unbind'])
        bot.register_message_handler(user_handlers.random_score_command, commands=['random_score'])  # 注册随机增加积分命令

        # 注册管理员命令处理函数
        # bot.register_message_handler(admin_handlers.generate_invite_code_command, commands=['generate_code'])
        # bot.register_message_handler(admin_handlers.generate_renew_codes_command, commands=['generate_renew_code'])
        # bot.register_message_handler(admin_handlers.get_all_invite_codes_command, commands=['invite'])
        # bot.register_message_handler(admin_handlers.toggle_invite_code_system_command, commands=['toggle_invite_code_system'])
        # bot.register_message_handler(admin_handlers.set_score_command, commands=['set_score'])
        # bot.register_message_handler(admin_handlers.get_score_command, commands=['get_score', 'score'])
        # bot.register_message_handler(admin_handlers.add_score_command, commands=['add_score'])
        # bot.register_message_handler(admin_handlers.reduce_score_command, commands=['reduce_score'])
        # bot.register_message_handler(admin_handlers.set_price_command, commands=['set_price'])
        # bot.register_message_handler(admin_handlers.get_user_info_by_telegram_id_command, commands=['userinfo'])
        # bot.register_message_handler(admin_handlers.get_user_info_by_username_command, commands=['userinfo_by_username'])
        # bot.register_message_handler(admin_handlers.get_stats_command, commands=['stats'])
        # bot.register_message_handler(admin_handlers.toggle_expired_user_clean_command, commands=['toggle_expired_user_clean']) # 注册开关清理过期用户定时任务的命令
        # bot.register_message_handler(admin_handlers.get_expiring_users_command, commands=['get_expiring_users']) # 注册获取即将过期用户的命令
        # bot.register_message_handler(admin_handlers.get_expired_users_command, commands=['get_expired_users']) # 注册获取已过期用户列表的命令
        # bot.register_message_handler(admin_handlers.clean_expired_users_command, commands=['clean_expired_users']) # 注册立即清理过期用户的命令
        # bot.register_message_handler(admin_handlers.add_random_score_command, commands=['add_random_score']) # 注册随机增加积分命令
        # bot.register_message_handler(admin_handlers.random_give_score_by_checkin_time_command, commands=['random_score_by_checkin']) # 注册随机赠送积分命令
        # bot.register_message_handler(admin_handlers.get_unused_invite_codes_command, commands=['unused_invite_codes']) # 注册获取未使用的邀请码的命令
        # bot.register_message_handler(admin_handlers.get_unused_renew_codes_command, commands=['unused_renew_codes'])
        # bot.register_message_handler(admin_handlers.get_user_info_in_server_command, commands=['userinfo_in_server']) # 注册获取服务器用户信息的命令
        # bot.register_message_handler(admin_handlers.get_score_chart_command, commands=['get_score_chart']) # 注册获取积分排行榜的命令
        # bot.register_message_handler(admin_handlers.toggle_clean_msg_system_command, commands=['toggle_clean_msg_system']) # 注册获取积分排行榜的命令

    def get_bot(self):
        return self.bot


def run_bot():
    """运行 Bot"""
    bot_manager = BotManager()
    bot = bot_manager.get_bot()
    if settings.WEBHOOK_URL:
        logger.info(f"Bot 以 Webhook 模式启动")
        bot.remove_webhook()
        bot.set_webhook(settings.WEBHOOK_URL)
    else:
        logger.info(f"Bot 以 Polling 模式启动")
        bot.infinity_polling()


if __name__ == "__main__":
    run_bot()
