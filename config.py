import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


# Default Configuration
DEFAULT_MAX_TOKENS = 2000
DEFAULT_BUDGET_TOKENS = 10000
DEFAULT_TEMPERATURE = 0.7

# Streamlit Configuration
PAGE_TITLE = "Claude AI Chat qua API cho rẻ hẹ hẹ hẹ"
PAGE_ICON = "🤖"

# Chat Configuration
MAX_HISTORY_LENGTH = 10  # Giới hạn số tin nhắn trong lịch sử
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."

# Model Configuration
DEFAULT_MODEL = "claude-3-haiku-20240307"

# UI Configuration
SIDEBAR_WIDTH = 300
CHAT_INPUT_PLACEHOLDER = "Nhập tin nhắn của bạn..."

# Validation
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY không được tìm thấy trong biến môi trường. Vui lòng tạo file .env và thêm ANTHROPIC_API_KEY=your_api_key")

# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() == "true"