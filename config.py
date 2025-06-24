import os

# API Keys - để None để buộc người dùng nhập qua UI
ANTHROPIC_API_KEY = None

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

# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# API Key validation function
def validate_api_key(api_key: str) -> bool:
    """
    Kiểm tra tính hợp lệ cơ bản của API key
    
    Args:
        api_key: API key cần kiểm tra
        
    Returns:
        True nếu API key có vẻ hợp lệ, False nếu không
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Anthropic API key thường bắt đầu với "sk-ant-"
    if api_key.startswith("sk-ant-") and len(api_key) > 20:
        return True
    
    return False