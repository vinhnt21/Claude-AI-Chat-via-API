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