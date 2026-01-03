"""
数据解析与清洗

目标：
- 从微信导出文本（raw_chat.txt）解析出每条消息的时间、发送者、内容
- 做必要的脱敏与归一化
- 输出结构化 JSON（clean_memory.json）便于检索和作为上下文输入

注意：
- 不要在仓库中提交 raw_chat.txt 或 clean_memory.json（data/ 目录应在 .gitignore 中）
"""

import re
import json
from pathlib import Path
from typing import List, Dict
import pandas as pd

CHAT_LINE_RE = re.compile(r'^\[(?P<time>.*?)\]\s*(?P<sender>.*?):\s*(?P<content>.*)$')

def parse_raw_chat(file_path: str) -> pd.DataFrame:
    """
    解析微信导出的纯文本，返回 DataFrame（columns: time, sender, content）
    解析规则需要根据你真实的导出格式做调整。
    """
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = CHAT_LINE_RE.match(line)
            if m:
                rows.append(m.groupdict())
            else:
                # 非匹配行，可能是多行消息的延续，附加到上一个内容
                if rows:
                    rows[-1]['content'] += '\n' + line
    df = pd.DataFrame(rows)
    return df

def clean_messages(df: pd.DataFrame) -> List[Dict]:
    """
    对消息进行进一步清洗（去除系统消息、表情替换、脱敏等）
    返回适合存储为 memory 的 list[dict]
    """
    memories = []
    for _, row in df.iterrows():
        content = row['content']
        # 示例脱敏：替换手机号
        content = re.sub(r'\b1\d{10}\b', '[PHONE]', content)
        # 去除多余空白
        content = re.sub(r'\s+', ' ', content).strip()
        if not content:
            continue
        memories.append({
            'time': row.get('time', ''),
            'sender': row.get('sender', ''),
            'content': content,
        })
    return memories

def save_clean_memory(memories: List[Dict], out_path: str):
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/raw_chat.txt')
    parser.add_argument('--output', default='data/clean_memory.json')
    args = parser.parse_args()

    df = parse_raw_chat(args.input)
    memories = clean_messages(df)
    save_clean_memory(memories, args.output)
    print(f"Saved {len(memories)} messages to {args.output}")