 # 项目配置
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# --- 数据库配置 ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/db.sqlite3")  # 数据库连接 URL，默认为 SQLite

# --- 服务类型配置 ---
SERVICE_TYPE = os.getenv("SERVICE_TYPE")  # 支持的服务类型列表
# --- Telegram Bot 配置 ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Telegram Bot Token
ADMIN_TELEGRAM_IDS = [int(id) for id in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if id]  # 管理员 Telegram ID 列表，用逗号分隔

# --- Navidrome 配置 ---
NAVIDROME_API_URL = os.getenv("NAVIDROME_API_URL")  # Navidrome API 地址
NAVIDROME_API_USERNAME = os.getenv("NAVIDROME_API_USERNAME")  # Navidrome API 用户名
NAVIDROME_API_PASSWORD = os.getenv("NAVIDROME_API_PASSWORD")  # Navidrome API 密码

# --- Emby 配置 ---
EMBY_API_URL = os.getenv("EMBY_API_URL")  # Emby API 地址
EMBY_API_KEY = os.getenv("EMBY_API_KEY")  # Emby API 密钥
EMBY_API_USERNAME = os.getenv("EMBY_API_USERNAME")  # Navidrome API 用户名
EMBY_API_PASSWORD = os.getenv("EMBY_API_PASSWORD")  # Navidrome API 密码
EMBY_COPY_FROM_ID = os.getenv("EMBY_COPY_FROM_ID", None) # Emby Create User Configure From User ID

# --- Audiobookshelf 配置 ---
AUDIOBOOKSHELF_API_URL = os.getenv("AUDIOBOOKSHELF_API_URL")  # Emby API 地址
AUDIOBOOKSHELF_API_KEY = os.getenv("AUDIOBOOKSHELF_API_KEY")  # Emby API 密钥
AUDIOBOOKSHELF_API_USERNAME = os.getenv("AUDIOBOOKSHELF_API_USERNAME")  # Navidrome API 用户名
AUDIOBOOKSHELF_API_PASSWORD = os.getenv("AUDIOBOOKSHELF_API_PASSWORD")  # Navidrome API 密码
AUDIOBOOKSHELF_COPY_FROM_ID = os.getenv("AUDIOBOOKSHELF_COPY_FROM_ID", None)

# --- 其他配置 ---
INVITE_CODE_LENGTH = int(os.getenv("INVITE_CODE_LENGTH", 8))  # 邀请码长度，默认为 8
INVITE_CODE_EXPIRATION_DAYS = int(os.getenv("INVITE_CODE_EXPIRATION_DAYS", 7))  # 邀请码过期时间（天），默认为 7
INVITE_CODE_SYSTEM_ENABLED=bool(os.getenv("INVITE_CODE_SYSTEM_ENABLED", False) == 'True')
INVITE_CODE_PRICE=int(os.getenv("INVITE_CODE_PRICE", 100))

# --- 清理不活跃用户 ---
EXPIRED_DAYS = int(os.getenv("EXPIRED_DAYS", 30))  # 用户过期时间（天），默认为 30
WARNING_DAYS = int(os.getenv("WARNING_DAYS", 27)) #  提前警告天数，默认为3
DELAY_INTERVAL = int(os.getenv("CLEAN_INTERVAL", 2592000))  # 清理过期用户的时间间隔（秒），默认为 30 天
ENABLE_EXPIRED_USER_CLEAN = bool(os.getenv("ENABLE_EXPIRED_USER_CLEAN", 'False') == 'True') # 是否开启定时任务，默认关闭

DELAY_INTERVAL = int(os.getenv("DELAY_INTERVAL", 5))
ENABLE_MESSAGE_CLEANER = bool(os.getenv("ENABLE_MESSAGE_CLEANER", 'False') == 'True') # 是否开启消息清理系统，默认关闭