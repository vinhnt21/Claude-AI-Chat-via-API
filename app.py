import streamlit as st
import time
from typing import List, Dict
import json
from datetime import datetime

from llm_handler_anthropic import anthropic_handler, MODELS
from config import (
    PAGE_TITLE, PAGE_ICON, DEFAULT_MODEL, DEFAULT_MAX_TOKENS, 
    DEFAULT_BUDGET_TOKENS, CHAT_INPUT_PLACEHOLDER, MAX_HISTORY_LENGTH,
    DEFAULT_SYSTEM_PROMPT, DEBUG
)

# Streamlit page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Khởi tạo session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "model_settings" not in st.session_state:
        st.session_state.model_settings = {
            "model": DEFAULT_MODEL,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "thinking": False,
            "budget_tokens": DEFAULT_BUDGET_TOKENS,
            "temperature": 0.7,
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "use_streaming": True
        }
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize sync flags để tránh infinite loop
    if "sync_flags" not in st.session_state:
        st.session_state.sync_flags = {
            "last_thinking_state": False
        }



def handle_thinking_temperature_sync(thinking_enabled, current_thinking):
    """Xử lý đồng bộ temperature khi thinking mode thay đổi"""
    # Kiểm tra xem thinking state có thay đổi không
    if current_thinking != st.session_state.sync_flags["last_thinking_state"]:
        st.session_state.sync_flags["last_thinking_state"] = current_thinking
        
        if current_thinking:
            # Lưu temperature hiện tại trước khi set = 1.0
            if "saved_temperature" not in st.session_state:
                st.session_state.saved_temperature = st.session_state.model_settings["temperature"]
            st.session_state.model_settings["temperature"] = 1.0
        else:
            # Khôi phục temperature đã lưu
            if "saved_temperature" in st.session_state:
                st.session_state.model_settings["temperature"] = st.session_state.saved_temperature

def render_sidebar():
    """Render sidebar với các tùy chọn cấu hình"""
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        
        # Model Selection
        st.subheader("🤖 Chọn Model")
        
        model_options = list(MODELS.keys())
        model_labels = [anthropic_handler.format_model_display(model) for model in model_options]
        
        selected_model_index = model_options.index(st.session_state.model_settings["model"]) if st.session_state.model_settings["model"] in model_options else 0
        
        selected_model = st.selectbox(
            "Model:",
            options=model_options,
            index=selected_model_index,
            format_func=lambda x: anthropic_handler.format_model_display(x),
            key="model_selector"
        )
        
        st.session_state.model_settings["model"] = selected_model
        
        # Model Information
        model_info = anthropic_handler.get_model_info(selected_model)
        if model_info:
            with st.expander("ℹ️ Thông tin Model", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Input:** {model_info['price']['input']}")
                    st.write(f"**Context:** {model_info['context_window']}")
                with col2:
                    st.write(f"**Output:** {model_info['price']['output']}")
                    st.write(f"**Max Output:** {model_info['max_output']}")
        
        st.divider()
        
        # Parameters
        st.subheader("🎛️ Tham số")
        
        # Max Tokens
        max_tokens = st.number_input(
            "Max Tokens:",
            min_value=100,
            max_value=50000,
            value=st.session_state.model_settings["max_tokens"],
            step=100,
            help="Số token tối đa cho response"
        )
        st.session_state.model_settings["max_tokens"] = max_tokens
        
        # Temperature với đồng bộ thinking mode
        thinking_enabled = model_info.get("extended_thinking", False) if model_info else False
        
        # Extended Thinking checkbox (đặt trước temperature để xử lý đồng bộ)
        if thinking_enabled:
            enable_thinking = st.checkbox(
                "🧠 Bật Extended Thinking",
                value=st.session_state.model_settings["thinking"],
                key="thinking_checkbox",
                help="Cho phép model suy nghĩ trước khi trả lời"
            )
            st.session_state.model_settings["thinking"] = enable_thinking
        else:
            st.session_state.model_settings["thinking"] = False
            
        current_thinking = st.session_state.model_settings["thinking"] and thinking_enabled
        
        # Xử lý đồng bộ thinking và temperature
        handle_thinking_temperature_sync(thinking_enabled, current_thinking)
        
        if current_thinking:
            # Khi thinking enabled, temperature cố định = 1.0
            st.markdown("**Temperature:** *1.0 (cố định khi thinking enabled)*")
            st.info("⚠️ Temperature được cố định ở 1.0 khi Extended Thinking được bật")
            # Hiển thị temperature đã lưu
            if "saved_temperature" in st.session_state:
                st.caption(f"💾 Temperature đã lưu: {st.session_state.saved_temperature}")
        else:
            # Cho phép điều chỉnh temperature
            temperature = st.number_input(
                "Temperature:",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.model_settings["temperature"],
                step=0.1,
                format="%.1f",
                help="Mức độ sáng tạo (0 = conservative, 1 = creative)"
            )
            st.session_state.model_settings["temperature"] = temperature
        
        # Extended Thinking Budget Tokens
        if thinking_enabled and st.session_state.model_settings["thinking"]:
            budget_tokens = st.number_input(
                "Budget Tokens cho Thinking:",
                min_value=1024,  # Minimum theo API
                max_value=100000,
                value=max(st.session_state.model_settings["budget_tokens"], 1024),
                step=1000,
                help="Số tokens cho quá trình thinking"
            )
            st.session_state.model_settings["budget_tokens"] = budget_tokens
            
            # Validation: budget_tokens phải < max_tokens
            current_budget = st.session_state.model_settings["budget_tokens"]
            current_max = st.session_state.model_settings["max_tokens"]
            
            if current_budget >= current_max:
                st.error(f"⚠️ Budget tokens ({current_budget}) phải nhỏ hơn Max tokens ({current_max})")
                # Tự động điều chỉnh
                adjusted_budget = max(1024, current_max - 1000)
                st.session_state.model_settings["budget_tokens"] = adjusted_budget
                st.info(f"✅ Đã tự động điều chỉnh Budget tokens thành {adjusted_budget}")
                st.rerun()  # Refresh để cập nhật UI
            
            # Warning nếu quá gần
            elif current_budget >= current_max * 0.8:
                st.warning("⚠️ Budget tokens quá gần Max tokens, có thể ảnh hưởng đến chất lượng response")
        
        if not thinking_enabled:
            st.info("⚠️ Model này không hỗ trợ Extended Thinking")
        
        st.divider()
        
        # System Prompt
        st.subheader("📝 System Prompt")
        system_prompt = st.text_area(
            "System Prompt:",
            value=st.session_state.model_settings["system_prompt"],
            height=100,
            placeholder="Nhập system prompt để định hướng AI...",
            help="Hướng dẫn cho AI về cách phản hồi"
        )
        st.session_state.model_settings["system_prompt"] = system_prompt
        
        st.divider()
        
        # Streaming
        st.subheader("🚀 Tùy chọn khác")
        use_streaming = st.checkbox(
            "Bật Streaming",
            value=st.session_state.model_settings["use_streaming"],
            help="Hiển thị response theo thời gian thực"
        )
        st.session_state.model_settings["use_streaming"] = use_streaming
        
        # Debug mode
        if DEBUG:
            st.subheader("🐛 Debug")
            if st.button("Hiển thị Session State"):
                st.json(dict(st.session_state))
        
        st.divider()
        
        # API Rules Information
        st.subheader("📋 Quy tắc API")
        with st.expander("ℹ️ Thông tin quan trọng", expanded=False):
            st.markdown("""
            **Extended Thinking Rules:**
            - Temperature phải = 1.0 khi thinking enabled
            - Budget tokens ≥ 1024 (minimum)
            - Max tokens > Budget tokens
            - Chỉ model có hỗ trợ mới có thể dùng thinking
            
            **Token Guidelines:**
            - Sử dụng input number để nhập giá trị chính xác
            - Hệ thống sẽ tự động điều chỉnh nếu không hợp lệ
            - Giao diện tối ưu để giảm reload trang
            """)
        
        st.divider()
        
        # Chat Management
        st.subheader("💬 Quản lý Chat")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Xóa Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("💾 Lưu Chat", use_container_width=True):
                save_chat_history()
        
        # Chat Statistics
        if st.session_state.messages:
            st.subheader("📊 Thống kê")
            total_messages = len(st.session_state.messages)
            user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
            assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tổng tin nhắn", total_messages)
            with col2:
                st.metric("Của bạn", user_messages)

def save_chat_history():
    """Lưu lịch sử chat"""
    if st.session_state.messages:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.json"
        
        chat_data = {
            "timestamp": timestamp,
            "model_settings": st.session_state.model_settings,
            "messages": st.session_state.messages
        }
        
        # Trong môi trường thực tế, bạn có thể lưu vào file hoặc database
        st.session_state.chat_history.append(chat_data)
        st.success(f"✅ Đã lưu chat history: {filename}")

def render_chat_interface():
    """Render giao diện chat chính"""
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    
    # Hiển thị thông tin model hiện tại
    current_model = st.session_state.model_settings["model"]
    model_display = anthropic_handler.format_model_display(current_model)
    
    st.info(f"🤖 Đang sử dụng: **{model_display}** | "
           f"Streaming: {'✅' if st.session_state.model_settings['use_streaming'] else '❌'} | "
           f"Thinking: {'🧠' if st.session_state.model_settings['thinking'] else '❌'}")
    
    # Hiển thị lịch sử chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input từ user
    if prompt := st.chat_input(CHAT_INPUT_PLACEHOLDER):
        # Giới hạn độ dài lịch sử
        if len(st.session_state.messages) >= MAX_HISTORY_LENGTH:
            st.session_state.messages = st.session_state.messages[-(MAX_HISTORY_LENGTH-2):]
        
        # Thêm message của user
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Tạo response từ assistant
        with st.chat_message("assistant"):
            generate_response()

def sync_validated_parameters(validated_params):
    """Đồng bộ parameters đã được validate trở lại session state"""
    st.session_state.model_settings["max_tokens"] = validated_params["max_tokens"]
    st.session_state.model_settings["budget_tokens"] = validated_params["budget_tokens"] 
    st.session_state.model_settings["temperature"] = validated_params["temperature"]

def generate_response():
    """Tạo response từ AI"""
    settings = st.session_state.model_settings
    
    try:
        # Validate parameters trước khi gọi API
        validated = anthropic_handler.validate_and_fix_parameters(
            settings["model"],
            settings["max_tokens"],
            settings["budget_tokens"],
            settings["temperature"],
            settings["thinking"]
        )
        
        # Đồng bộ parameters đã được validate
        sync_validated_parameters(validated)
        
        # Hiển thị warnings nếu có
        if validated["warnings"]:
            warning_container = st.container()
            with warning_container:
                for warning in validated["warnings"]:
                    st.warning(f"⚠️ {warning}")
            time.sleep(1)  # Cho user đọc warnings
        
        if settings["use_streaming"]:
            # Streaming response
            response_placeholder = st.empty()
            full_response = ""
            
            with st.spinner("🤔 Đang suy nghĩ..."):
                for chunk in anthropic_handler.stream_response(
                    model=settings["model"],
                    messages=st.session_state.messages,
                    system_prompt=settings["system_prompt"] if settings["system_prompt"].strip() else None,
                    max_tokens=validated["max_tokens"],
                    thinking=settings["thinking"],
                    budget_tokens=validated["budget_tokens"],
                    temperature=validated["temperature"]
                ):
                    full_response += chunk
                    # Thêm cursor effect
                    response_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)
            
            # Hiển thị response cuối cùng
            response_placeholder.markdown(full_response)
            
        else:
            # Non-streaming response
            with st.spinner("🤔 Đang tạo phản hồi..."):
                full_response = anthropic_handler.get_response(
                    model=settings["model"],
                    messages=st.session_state.messages,
                    system_prompt=settings["system_prompt"] if settings["system_prompt"].strip() else None,
                    max_tokens=validated["max_tokens"],
                    thinking=settings["thinking"],
                    budget_tokens=validated["budget_tokens"],
                    temperature=validated["temperature"]
                )
            st.markdown(full_response)
        
        # Thêm response vào session state
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
    except Exception as e:
        st.error(f"❌ Lỗi khi tạo response: {str(e)}")

def render_welcome_message():
    """Hiển thị thông báo chào mừng khi chưa có tin nhắn"""
    if not st.session_state.messages:
        st.markdown("""
        ### 👋 Chào mừng bạn đến với Claude AI Chat!
        
        **Hướng dẫn sử dụng:**
        - 🤖 Chọn model phù hợp trong sidebar
        - 🎛️ Điều chỉnh các tham số theo nhu cầu (slider hoặc nhập trực tiếp)
        - 🧠 Bật Extended Thinking để xem quá trình suy nghĩ của AI
        - 📝 Sử dụng System Prompt để định hướng AI
        - 🚀 Bật Streaming để xem response theo thời gian thực
        
        **Tính năng được cải thiện:**
        - ✅ **Smart Validation**: Tự động kiểm tra và điều chỉnh parameters
        - 🎚️ **Smart Temperature**: Tự động cố định/khôi phục khi bật/tắt thinking
        - 🧠 **Thinking Mode**: Lưu và khôi phục temperature khi chuyển đổi
        - ⚡ **Streamlined UI**: Chỉ sử dụng input để tránh reload nhiều lần
        - 📊 **Visual Warnings**: Hiển thị cảnh báo validation trực quan
        
        **Cách sử dụng:**
        - 🔢 **Input Fields**: Nhập giá trị trực tiếp cho các tham số
        - 💾 **Auto Save**: Temperature được lưu khi bật thinking và khôi phục khi tắt
        - ⚠️ **Smart Validation**: Hệ thống tự động kiểm tra và điều chỉnh nếu cần
        
        **Bắt đầu trò chuyện bằng cách nhập tin nhắn ở bên dưới!** 👇
        
        *Lưu ý: Hệ thống sẽ tự động điều chỉnh các tham số để tuân thủ quy tắc API của Anthropic. Giao diện đã được tối ưu để giảm reload trang.*
        """)

def main():
    """Hàm chính"""
    # Khởi tạo session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render chat interface
    render_chat_interface()
    
    # Hiển thị welcome message nếu chưa có tin nhắn
    render_welcome_message()

if __name__ == "__main__":
    main()