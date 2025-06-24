import anthropic
from typing import List, Dict, Any, Optional, Generator
import logging
from config import ANTHROPIC_API_KEY, DEBUG

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

# Model definitions
MODELS = {
    "claude-opus-4-20250514": {
        "can_reasoning": True,
        "extended_thinking": True,
        "price": {
            "input": "$15 / MTok",
            "output": "$75 / MTok",
        },
        "context_window": "200K",
        "max_output": "32000 tokens",
        "description": "Our most capable model",
        "display_name": "Claude Opus 4"
    },
    "claude-sonnet-4-20250514": {
        "can_reasoning": True,
        "extended_thinking": True,
        "price": {
            "input": "$3 / MTok",
            "output": "$15 / MTok",
        },
        "context_window": "200K",
        "max_output": "64000 tokens",
        "description": "High-performance model",
        "display_name": "Claude Sonnet 4"
    },
    "claude-3-7-sonnet-20250219": {
        "can_reasoning": True,
        "extended_thinking": True,
        "price": {
            "input": "$3 / MTok",
            "output": "$15 / MTok",
        },
        "context_window": "200K",
        "max_output": "64000 tokens",
        "description": "High-performance model with early extended thinking",
        "display_name": "Claude 3.7 Sonnet"
    },
    "claude-3-5-sonnet-20241022": {
        "can_reasoning": True,
        "extended_thinking": False,
        "price": {
            "input": "$3 / MTok",
            "output": "$15 / MTok",
        },
        "context_window": "200K",
        "max_output": "8192 tokens",
        "description": "Our previous intelligent model",
        "display_name": "Claude 3.5 Sonnet"
    },
    "claude-3-5-haiku-20241022": {
        "can_reasoning": False,
        "extended_thinking": False,
        "price": {
            "input": "$0.80 / MTok",
            "output": "$4 / MTok",
        },
        "context_window": "200K",
        "max_output": "8192 tokens",
        "description": "Our fastest model",
        "display_name": "Claude 3.5 Haiku"
    },
    "claude-3-opus-20240229": {
        "can_reasoning": True,
        "extended_thinking": False,
        "price": {
            "input": "$15 / MTok",
            "output": "$75 / MTok",
        },
        "context_window": "200K",
        "max_output": "4096 tokens",
        "description": "Powerful model for complex tasks",
        "display_name": "Claude 3 Opus"
    },
    "claude-3-haiku-20240307": {
        "can_reasoning": False,
        "extended_thinking": False,
        "price": {
            "input": "$0.25 / MTok",
            "output": "$1.25 / MTok",
        },
        "context_window": "200K",
        "max_output": "4096 tokens",
        "description": "Fast and compact model for near-instant responsiveness",
        "display_name": "Claude 3 Haiku"
    }
}

class AnthropicHandler:
    """Handler cho Anthropic API với streaming support"""
    
    def __init__(self, api_key: str = None):
        """
        Khởi tạo Anthropic client
        
        Args:
            api_key: Anthropic API key (optional)
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.client = None
        if self.api_key:
            self._initialize_client()
    
    def _initialize_client(self):
        """Khởi tạo Anthropic client với API key"""
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Anthropic client đã được khởi tạo")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Anthropic client: {str(e)}")
            self.client = None
    
    def set_api_key(self, api_key: str) -> bool:
        """
        Thiết lập API key mới
        
        Args:
            api_key: API key mới
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        if not api_key:
            return False
        
        self.api_key = api_key
        self._initialize_client()
        return self.client is not None
    
    def is_ready(self) -> bool:
        """
        Kiểm tra xem handler đã sẵn sàng sử dụng chưa
        
        Returns:
            True nếu client đã được khởi tạo, False nếu chưa
        """
        return self.client is not None and self.api_key is not None
    
    def test_api_key(self) -> Dict[str, Any]:
        """
        Test API key bằng cách gọi một request đơn giản
        
        Returns:
            Dictionary chứa kết quả test
        """
        if not self.is_ready():
            return {
                "success": False,
                "error": "Client chưa được khởi tạo hoặc API key chưa được set"
            }
        
        try:
            # Test với một request đơn giản
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return {
                "success": True,
                "message": "API key hợp lệ"
            }
        except anthropic.AuthenticationError:
            return {
                "success": False,
                "error": "API key không hợp lệ"
            }
        except anthropic.APIError as e:
            return {
                "success": False,
                "error": f"Lỗi API: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi không mong muốn: {str(e)}"
            }
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Lấy danh sách các model khả dụng
        
        Returns:
            Dictionary chứa thông tin các model
        """
        return MODELS
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin của một model cụ thể
        
        Args:
            model_id: ID của model
            
        Returns:
            Dictionary chứa thông tin model
        """
        return MODELS.get(model_id, {})
    
    def validate_model_features(self, model_id: str, thinking: bool = False) -> bool:
        """
        Kiểm tra xem model có hỗ trợ các tính năng được yêu cầu không
        
        Args:
            model_id: ID của model
            thinking: Có cần extended thinking không
            
        Returns:
            True nếu model hỗ trợ, False nếu không
        """
        model_info = self.get_model_info(model_id)
        if not model_info:
            return False
        
        if thinking and not model_info.get("extended_thinking", False):
            return False
            
        return True
    
    def validate_and_fix_parameters(
        self,
        model: str,
        max_tokens: int,
        budget_tokens: int,
        temperature: float,
        thinking: bool
    ) -> Dict[str, Any]:
        """
        Validate và tự động sửa các parameters để tránh lỗi API
        
        Args:
            model: Model ID
            max_tokens: Số token tối đa
            budget_tokens: Budget tokens cho thinking
            temperature: Temperature
            thinking: Có bật thinking không
            
        Returns:
            Dictionary chứa parameters đã được validate và sửa
        """
        warnings = []
        
        # Kiểm tra và sửa budget_tokens minimum
        if thinking and budget_tokens < 1024:
            budget_tokens = 1024
            warnings.append("Budget tokens đã được tăng lên 1024 (minimum required)")
        
        # Kiểm tra và sửa max_tokens vs budget_tokens
        if thinking and max_tokens <= budget_tokens:
            max_tokens = budget_tokens + 1000  # Đảm bảo có khoảng cách an toàn
            warnings.append(f"Max tokens đã được tăng lên {max_tokens} để lớn hơn budget_tokens")
        
        # Kiểm tra và sửa temperature khi thinking enabled
        if thinking:
            # Theo documentation, temperature phải = 1 khi thinking enabled
            if temperature != 1.0:
                temperature = 1.0
                warnings.append("Temperature đã được set = 1.0 (required when thinking enabled)")
        
        return {
            "max_tokens": max_tokens,
            "budget_tokens": budget_tokens,
            "temperature": temperature,
            "warnings": warnings
        }
    
    def _build_request_params(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        thinking: bool = False,
        budget_tokens: int = 10000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Xây dựng parameters cho API request
        
        Args:
            model: Model ID
            messages: Danh sách tin nhắn
            system_prompt: System prompt (tùy chọn)
            max_tokens: Số token tối đa
            thinking: Bật extended thinking
            budget_tokens: Budget tokens cho thinking
            temperature: Temperature cho response
            
        Returns:
            Dictionary chứa parameters
        """
        # Validate và sửa parameters
        validated = self.validate_and_fix_parameters(
            model, max_tokens, budget_tokens, temperature, thinking
        )
        
        # Log warnings nếu có
        for warning in validated["warnings"]:
            logger.warning(warning)
        
        params = {
            "model": model,
            "max_tokens": validated["max_tokens"],
            "messages": messages,
            "temperature": validated["temperature"]
        }
        
        if system_prompt and system_prompt.strip():
            params["system"] = system_prompt
            
        if thinking and self.validate_model_features(model, thinking=True):
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": validated["budget_tokens"]
            }
            logger.debug(f"Extended thinking enabled với {validated['budget_tokens']} budget tokens")
            
        return params
    
    def get_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        thinking: bool = False,
        budget_tokens: int = 10000,
        temperature: float = 0.7
    ) -> str:
        """
        Lấy response từ Anthropic API (không streaming)
        
        Args:
            model: Model ID
            messages: Danh sách tin nhắn
            system_prompt: System prompt (tùy chọn)
            max_tokens: Số token tối đa
            thinking: Bật extended thinking
            budget_tokens: Budget tokens cho thinking
            temperature: Temperature
            
        Returns:
            Response text
        """
        if not self.is_ready():
            return "❌ Lỗi: API key chưa được cung cấp hoặc không hợp lệ. Vui lòng nhập API key trong sidebar."
        
        try:
            params = self._build_request_params(
                model, messages, system_prompt, max_tokens, 
                thinking, budget_tokens, temperature
            )
            
            logger.debug(f"Gọi API với model: {model}, thinking: {thinking}")
            response = self.client.messages.create(**params)
            
            # Xử lý response có thinking
            if thinking and hasattr(response, 'content'):
                full_response = ""
                for block in response.content:
                    if block.type == "thinking":
                        full_response += f"\n**🤔 Thinking:** {block.thinking}\n\n"
                    elif block.type == "text":
                        full_response += block.text
                return full_response
            else:
                return response.content[0].text
                
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return f"❌ Lỗi API: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return f"❌ Lỗi không mong muốn: {str(e)}"
    
    def stream_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        thinking: bool = False,
        budget_tokens: int = 10000,
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        Stream response từ Anthropic API
        
        Args:
            model: Model ID
            messages: Danh sách tin nhắn
            system_prompt: System prompt (tùy chọn)
            max_tokens: Số token tối đa
            thinking: Bật extended thinking
            budget_tokens: Budget tokens cho thinking
            temperature: Temperature
            
        Yields:
            Từng chunk của response
        """
        if not self.is_ready():
            yield "❌ Lỗi: API key chưa được cung cấp hoặc không hợp lệ. Vui lòng nhập API key trong sidebar."
            return
        
        try:
            params = self._build_request_params(
                model, messages, system_prompt, max_tokens, 
                thinking, budget_tokens, temperature
            )
            
            logger.debug(f"Streaming với model: {model}, thinking: {thinking}")
            
            with self.client.messages.stream(**params) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield event.delta.text
                    elif event.type == "thinking_block_delta":
                        if hasattr(event.delta, 'thinking'):
                            yield f"\n**🤔 [Thinking]** {event.delta.thinking}"
                    elif event.type == "content_block_start":
                        if hasattr(event.content_block, 'type') and event.content_block.type == "thinking":
                            yield "\n\n**🤔 Thinking process:**\n"
                            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API streaming error: {str(e)}")
            yield f"❌ Lỗi API streaming: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected streaming error: {str(e)}")
            yield f"❌ Lỗi streaming không mong muốn: {str(e)}"
    
    def estimate_tokens(self, text: str) -> int:
        """
        Ước tính số tokens trong text (xấp xỉ)
        
        Args:
            text: Text cần ước tính
            
        Returns:
            Số tokens ước tính
        """
        # Ước tính đơn giản: 1 token ≈ 4 characters
        return len(text) // 4
    
    def format_model_display(self, model_id: str) -> str:
        """
        Format tên model để hiển thị trong UI
        
        Args:
            model_id: ID của model
            
        Returns:
            Tên hiển thị của model
        """
        model_info = self.get_model_info(model_id)
        if not model_info:
            return model_id
        
        display_name = model_info.get("display_name", model_id)
        description = model_info.get("description", "")
        
        return f"{display_name} - {description}"

# Instance mặc định để sử dụng - không khởi tạo với API key
anthropic_handler = AnthropicHandler()