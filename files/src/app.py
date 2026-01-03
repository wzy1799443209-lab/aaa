import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. 加载环境变量 (如果你在本地有 .env 文件)
load_dotenv()

# 2. 页面基础配置
st.set_page_config(
    page_title="AI Soul Studio",
    page_icon="💬",
    layout="centered" # 手机端体验更佳
)

# --- 侧边栏配置区 (模拟微信的设置) ---
with st.sidebar:
    st.header("⚙️ 灵魂参数设置")
    
    # API Key 输入 (优先读取环境变量，如果没有则手动输入)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("请输入 Gemini API Key", type="password")
    
    st.markdown("---")
    
    # 角色设定
    target_name = st.text_input("AI 的名字", value="她")
    user_name = st.text_input("你的名字", value="我")
    
    # 核心：这里是未来放入清洗后数据的地方
    # 目前作为 MVP，我们可以手动写一段 Prompt 来测试
    default_prompt = f"""
    你现在需要进行角色扮演。
    你的名字是{target_name}，你正在微信上和{user_name}聊天。
    
    【性格特征】：
    温柔、有时候有点小调皮，喜欢用波浪号~，不喜欢回太长的字。
    
    【说话样本】：
    {user_name}: 晚上吃了吗？
    {target_name}: 还没呢，刚下班，饿晕了都[流泪] 你呢？
    {user_name}: 我也没。
    {target_name}: 那我们要不要去吃那个火锅呀？好久没去了！
    
    请严格模仿上述语气与我对话。不要像个机器人，要生活化。
    """
    
    system_instruction = st.text_area(
        "灵魂指令 (System Prompt)", 
        value=default_prompt, 
        height=300,
        help="在这里粘贴你清洗好的聊天记录样本，AI 会模仿这种语气。"
    )
    
    temperature = st.slider("情感波动 (Temperature)", 0.0, 1.0, 0.7, help="值越高，AI 越有创造力；值越低，AI 越严谨。")
    
    if st.button("🗑️ 清空聊天记忆"):
        st.session_state.messages = []
        st.rerun()

# --- 3. 初始化聊天引擎 ---

if api_key:
    try:
        genai.configure(api_key=api_key)
        # 使用 gemini-1.5-flash，速度快且免费额度高，适合聊天
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"API Key 配置出错: {e}")
else:
    st.warning("请在侧边栏输入 Google Gemini API Key 才能开始聊天。")
    st.stop()

# --- 4. 聊天界面逻辑 ---

st.title(f"💬 与 {target_name} 的聊天")

# 初始化 Session State (用于存储网页刷新后的聊天记录)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for message in st.session_state.messages:
    # 区分 User 和 Assistant 的头像
    avatar = "🧑‍💻" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- 5. 处理用户输入 ---

if prompt := st.chat_input("发消息..."):
    # A. 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # B. AI 生成回复
    try:
        # 将 Streamlit 的历史记录转换为 Gemini 的格式
        history_for_gemini = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
            for m in st.session_state.messages[:-1] # 不包含最新的一条，因为我们下面要单独发
        ]
        
        chat = model.start_chat(history=history_for_gemini)
        
        with st.chat_message("assistant", avatar="✨"):
            # 使用流式输出 (Stream) 模拟打字效果
            response_placeholder = st.empty()
            full_response = ""
            
            # 发送消息
            response_stream = chat.send_message(prompt, stream=True, generation_config={"temperature": temperature})
            
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
        
        # C. 保存 AI 回复到历史
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"发生错误: {e}")