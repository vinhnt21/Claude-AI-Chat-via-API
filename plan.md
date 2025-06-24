Kế hoạch chi tiết để AI Agent tạo code ứng dụng Chat đa-LLM
Giai đoạn 0: Thiết lập Dự án
Mục tiêu: Tạo cấu trúc thư mục và các file cần thiết cho dự án.

Task 0.1: Tạo cấu trúc thư mục
Tạo một thư mục gốc tên là multi_llm_chatbot. Bên trong đó, tạo các file và thư mục sau:

/multi_llm_chatbot
├── app.py
├── llm_handler.py
├── file_processor.py
├── requirements.txt
└── .streamlit/
    └── secrets.toml

Task 0.2: Điền nội dung file requirements.txt
Mở file requirements.txt và thêm các thư viện sau:

streamlit
openai
anthropic
google-generativeai
pypdf
python-dotenv

Task 0.3: Điền nội dung file secrets.toml
Mở file .streamlit/secrets.toml và thêm vào các placeholder cho API keys. Đây là nơi người dùng sẽ điền key của họ.

OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"

Giai đoạn 1: Xử lý Tệp (file_processor.py)
Mục tiêu: Xây dựng module có khả năng đọc và trích xuất văn bản từ các tệp PDF và TXT.

Task 1.1: Viết code cho file_processor.py
Mở file file_processor.py và viết một hàm tên là process_uploaded_file nhận đầu vào là một đối tượng UploadedFile của Streamlit.

Import các thư viện cần thiết: io và pypdf.

Hàm phải kiểm tra loại tệp (.type).

Nếu là application/pdf, dùng pypdf.PdfReader để đọc và trích xuất văn bản từ tất cả các trang.

Nếu là text/plain, đọc nội dung và giải mã bằng utf-8.

Hàm trả về một chuỗi văn bản đã được trích xuất hoặc None nếu không hỗ trợ loại tệp.

# Gợi ý code cho file_processor.py
import io
import pypdf

def process_uploaded_file(uploaded_file):
    """Đọc và trích xuất văn bản từ tệp được tải lên."""
    if uploaded_file is None:
        return None

    file_type = uploaded_file.type

    try:
        if file_type == "application/pdf":
            pdf_reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
            text = "".join(page.extract_text() for page in pdf_reader.pages)
            return text
        elif file_type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        else:
            return None # Không hỗ trợ loại tệp này
    except Exception as e:
        print(f"Lỗi khi xử lý tệp: {e}")
        return None

Giai đoạn 2: Trình xử lý LLM (llm_handler.py)
Mục tiêu: Xây dựng module chứa logic để gọi API của các nhà cung cấp LLM khác nhau.

Task 2.1: Viết code cho llm_handler.py
Mở file llm_handler.py và thực hiện:

Import openai, anthropic, google.generativeai as genai.

Tạo hàm get_openai_response(api_key, model, messages):

Khởi tạo client OpenAI với api_key.

Gọi client.chat.completions.create với model và messages.

Trả về response.choices[0].message.content.

Bọc trong khối try...except để xử lý lỗi.

Tạo hàm get_anthropic_response(api_key, model, messages, system_prompt):

Khởi tạo client Anthropic với api_key.

Gọi client.messages.create với model, max_tokens, system (dùng system_prompt), và messages (lọc bỏ tin nhắn system).

Trả về response.content[0].text.

Bọc trong khối try...except.

Tạo hàm get_google_response(api_key, model, messages, system_prompt):

Cấu hình genai với api_key.

Khởi tạo genai.GenerativeModel với model_name=model và system_instruction=system_prompt.

Gọi model.generate_content với messages (đã được chuyển đổi sang định dạng của Google).

Trả về response.text.

Bọc trong khối try...except.

Giai đoạn 3: Giao diện chính (app.py)
Mục tiêu: Xây dựng giao diện người dùng và tích hợp tất cả các module lại với nhau.

Task 3.1: Thiết lập ban đầu cho app.py

Import streamlit as st và các hàm từ file_processor và llm_handler.

Dùng st.set_page_config để đặt tiêu đề và layout trang (layout="wide").

Dùng st.title và st.caption để tạo tiêu đề chính.

Task 3.2: Khởi tạo Session State

Kiểm tra và khởi tạo st.session_state.messages nếu chưa có. Nó phải là một list rỗng [].

Kiểm tra và khởi tạo st.session_state.file_content nếu chưa có. Nó phải là một chuỗi rỗng "".

Task 3.3: Xây dựng Sidebar

Dùng with st.sidebar: để tạo thanh bên.

Thêm st.header("Cấu hình").

Dùng st.selectbox để tạo dropdown cho người dùng chọn provider ("OpenAI", "Anthropic", "Google").

Dựa vào provider đã chọn, dùng st.selectbox khác để hiển thị danh sách model tương ứng.

Dùng st.text_area để người dùng nhập system_prompt.

Dùng st.file_uploader để cho phép tải lên tệp. Gán kết quả cho biến uploaded_file.

Task 3.4: Xử lý tệp đã tải lên

Nếu uploaded_file không rỗng:

Gọi hàm process_uploaded_file(uploaded_file).

Lưu kết quả vào st.session_state.file_content.

Hiển thị thông báo thành công trên sidebar bằng st.sidebar.success().

Task 3.5: Hiển thị Lịch sử Chat

Lặp qua st.session_state.messages.

Với mỗi tin nhắn, dùng with st.chat_message(message["role"]): và st.markdown(message["content"]) để hiển thị.

Task 3.6: Xử lý Đầu vào của người dùng (st.chat_input)

Dùng if prompt := st.chat_input(...).

Bước 1: Hiển thị tin nhắn người dùng:

Thêm tin nhắn của người dùng ({"role": "user", "content": prompt}) vào st.session_state.messages.

Hiển thị nó ngay lập tức bằng st.chat_message.

Bước 2: Chuẩn bị dữ liệu cho API:

Tạo một prompt_with_context bằng cách kết hợp st.session_state.file_content với prompt của người dùng.

Tạo một danh sách messages_for_api từ st.session_state.messages, nhưng thay thế nội dung tin nhắn cuối cùng của người dùng bằng prompt_with_context.

Bước 3: Gọi API và hiển thị phản hồi:

Dùng with st.chat_message("assistant"): và with st.spinner(...):.

Lấy API keys từ st.secrets.

Dựa vào provider đã chọn, gọi hàm tương ứng từ llm_handler.

Hiển thị kết quả trả về bằng st.markdown().

Bước 4: Lưu phản hồi của AI:

Thêm tin nhắn của assistant ({"role": "assistant", "content": response}) vào st.session_state.messages.

Sau khi AI Agent hoàn thành tất cả các Task trên, ứng dụng sẽ có đầy đủ chức năng như kế hoạch đã đề ra.