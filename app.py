import streamlit as st
import pandas as pd
import zipfile
import io
import requests
from openai import OpenAI

# Cấu hình giao diện
st.set_page_config(page_title="AI Batch Image Tool", layout="wide", page_icon="🎨")

# --- PHẦN CẤU HÌNH API ---
with st.sidebar:
    st.header("Cấu hình API")
    api_key = st.text_input("Nhập OpenAI API Key:", type="password")
    model_choice = st.selectbox("Chọn Model:", ["dall-e-3", "dall-e-2"])
    size_choice = st.selectbox("Kích thước (Full HD):", ["1024x1024", "1024x1792", "1792x1024"])
    quality = st.select_slider("Chất lượng:", options=["standard", "hd"])

client = OpenAI(api_key=api_key) if api_key else None

# --- KHỞI TẠO SESSION STATE ---
if "results" not in st.session_state:
    st.session_state.results = []

# --- GIAO DIỆN CHÍNH ---
st.title("🚀 AI Batch Image Generator")
st.markdown("Công cụ tạo ảnh hàng loạt theo kịch bản, hỗ trợ quản lý lỗi và tải về file .zip")

# 1. Nhập kịch bản
prompt_input = st.text_area("Nhập kịch bản prompts (Mỗi dòng là 1 ảnh):", 
                            height=200, 
                            placeholder="Ví dụ:\nMột thành phố tương lai vào ban đêm, phong cách cyberpunk...\nMột chú mèo phi hành gia trên mặt trăng...")

# 2. Xử lý logic nút bấm
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

with col_btn1:
    if st.button("🎬 Bắt đầu tạo mới", use_container_width=True):
        if not api_key:
            st.error("Vui lòng nhập API Key!")
        else:
            prompts = [p.strip() for p in prompt_input.split('\n') if p.strip()]
            st.session_state.results = [{"prompt": p, "status": "Pending", "url": None, "error": ""} for p in prompts]

with col_btn2:
    # Nút thử lại các prompt bị lỗi
    failed_indices = [i for i, r in enumerate(st.session_state.results) if r["status"] == "Failed"]
    if st.button(f"🔄 Thử lại lỗi ({len(failed_indices)})", use_container_width=True, disabled=len(failed_indices) == 0):
        for i in failed_indices:
            st.session_state.results[i]["status"] = "Pending"

# 3. Tiến trình tạo ảnh
for idx, res in enumerate(st.session_state.results):
    if res["status"] == "Pending":
        try:
            with st.spinner(f"Đang tạo: {res['prompt'][:50]}..."):
                response = client.images.generate(
                    model=model_choice,
                    prompt=res["prompt"],
                    size=size_choice,
                    quality=quality,
                    n=1,
                )
                st.session_state.results[idx]["url"] = response.data[0].url
                st.session_state.results[idx]["status"] = "Success"
        except Exception as e:
            st.session_state.results[idx]["status"] = "Failed"
            st.session_state.results[idx]["error"] = str(e)

# 4. Hiển thị kết quả & Tải về
if st.session_state.results:
    st.divider()
    cols = st.columns(3) # Hiển thị grid 3 cột
    
    success_files = []
    
    for i, res in enumerate(st.session_state.results):
        with cols[i % 3]:
            if res["status"] == "Success":
                st.image(res["url"], caption=f"Ảnh {i+1}")
                # Chuẩn bị file để đóng gói zip
                img_content = requests.get(res["url"]).content
                success_files.append((f"image_{i+1}.png", img_content))
            else:
                st.error(f"Lỗi ảnh {i+1}: {res['error'][:100]}...")

    # Nút tải về toàn bộ
    if success_files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for name, data in success_files:
                zf.writestr(name, data)
        
        st.download_button(
            label="📂 Tải về toàn bộ ảnh thành công (.ZIP)",
            data=zip_buffer.getvalue(),
            file_name="ai_images_batch.zip",
            mime="application/zip",
            use_container_width=True
        )