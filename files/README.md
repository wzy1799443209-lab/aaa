# AI 聊天（ai-soul-mvp）

项目概述
- 本项目为基于 Python 的 AI 聊天应用。通过解析微信聊天记录，利用 Google Gemini 的大模型能力，通过 In-Context Learning 模式使模型模仿特定对象的语气与思路，以提供情感陪伴类对话体验。
- 当前版本：V1.0（纯文本对话）

核心功能
- 微信聊天数据清洗（从 raw_chat.txt 到结构化 clean_memory.json）
- 基于清洗后的记忆构建上下文（In-Context Learning），生成风格化对话
- 简单 Streamlit 前端用于交互与演示

技术栈
- Python 3.9+
- Streamlit（前端）
- Pandas（数据处理）
- python-dotenv（环境变量管理）
- Google Gemini 客户端（示例代码使用占位调用，需根据官方 SDK 调整）

目录结构
ai-soul-mvp/
├── data/                  # 【隐私目录】存放聊天记录（必须在 .gitignore 中忽略）
│   ├── raw_chat.txt       # 原始导出的微信记录
│   └── clean_memory.json  # 清洗后的结构化数据
├── src/
│   ├── data_loader.py     # 数据解析与清洗脚本
│   ├── bot_engine.py      # Gemini API 调用逻辑
│   └── app.py             # Streamlit 前端界面
├── .env                   # 【隐私文件】放 GEMINI_API_KEY（不要提交）
├── .gitignore
├── requirements.txt
└── README.md

安全与隐私注意
- 所有包含真实聊天记录和 API Key 的文件必须加入 .gitignore（例如 data/ 和 .env）。
- 在推送或共享仓库前，务必移除或替换任何 PII（个人身份信息）与敏感内容。
- 在发布演示或部署时，建议使用密钥管理/Secret 管理服务（例如 GitHub Secrets、Cloud Secret Manager）。

快速开始（本地）
1. 克隆仓库并创建虚拟环境：
   - python -m venv .venv
   - source .venv/bin/activate
2. 安装依赖：
   - pip install -r requirements.txt
3. 在根目录创建 `.env` 并写入真实 GEMINI_API_KEY。
4. 运行 Streamlit：
   - streamlit run src/app.py

如何贡献
- 欢迎提交 issue 或 PR。注意不要在 PR 中提交包含聊天记录或真实密钥的文件。

许可证
- (在此填写许可证，例如 MIT)