#!/usr/bin/env python3
"""
config.py 스마트 업데이트 도구
- 새로운 설정은 추가하되, 기존 사용자 설정값은 보존
- 구조 변경도 자동으로 처리
"""

import os
import re
import ast
import sys
from typing import Any, Dict, List, Tuple, Union

def parse_config_structure(content: str) -> Dict[str, Any]:
    """
    config 파일의 구조를 파싱합니다.
    주석과 함께 모든 설정을 추출합니다.
    """
    structure = {}
    lines = content.split('\n')
    current_section = None
    current_dict_name = None
    current_dict_content = []
    in_multiline_dict = False
    brace_count = 0
    
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 섹션 주석 감지
        if stripped.startswith('#') and not in_multiline_dict:
            current_section = stripped
            continue
        
        # 변수 할당 감지
        if '=' in stripped and not stripped.startswith('#') and not in_multiline_dict:
            var_match = re.match(r'^([A-Z_][A-Z0-9_]*)\s*=', stripped)
            if var_match:
                var_name = var_match.group(1)
                
                # 딕셔너리 시작 감지
                if '{' in stripped:
                    current_dict_name = var_name
                    current_dict_content = [line]
                    in_multiline_dict = True
                    brace_count = stripped.count('{') - stripped.count('}')
                    
                    if brace_count == 0:
                        # 한 줄로 완성된 딕셔너리
                        dict_content = '\n'.join(current_dict_content)
                        structure[var_name] = {
                            'section': current_section,
                            'content': dict_content,
                            'type': 'dict',
                            'line_start': line_num,
                            'line_end': line_num
                        }
                        in_multiline_dict = False
                        current_dict_content = []
                else:
                    # 단순 변수
                    structure[var_name] = {
                        'section': current_section,
                        'content': line,
                        'type': 'simple',
                        'line_start': line_num,
                        'line_end': line_num
                    }
        
        # 멀티라인 딕셔너리 처리
        elif in_multiline_dict:
            current_dict_content.append(line)
            brace_count += stripped.count('{') - stripped.count('}')
            
            if brace_count == 0:
                # 딕셔너리 완료
                dict_content = '\n'.join(current_dict_content)
                structure[current_dict_name] = {
                    'section': current_section,
                    'content': dict_content,
                    'type': 'dict',
                    'line_start': line_num - len(current_dict_content) + 1,
                    'line_end': line_num
                }
                in_multiline_dict = False
                current_dict_content = []
                current_dict_name = None
    
    return structure

def extract_dict_values(dict_str: str) -> Dict[str, Any]:
    """딕셔너리 문자열에서 값들을 추출합니다."""
    try:
        # 등호 이후 부분만 추출
        dict_part = dict_str.split('=', 1)[1].strip()
        # ast.literal_eval로 안전하게 파싱
        return ast.literal_eval(dict_part)
    except (ValueError, SyntaxError) as e:
        print(f"딕셔너리 파싱 오류: {e}")
        return {}

def extract_simple_values(content: str) -> Dict[str, str]:
    """간단한 문자열 변수들을 추출합니다."""
    values = {}
    patterns = {
        'GATE_API_KEY': r'GATE_API_KEY\s*=\s*["\']([^"\']*)["\']',
        'GATE_API_SECRET': r'GATE_API_SECRET\s*=\s*["\']([^"\']*)["\']',
        'TELEGRAM_BOT_TOKEN': r'TELEGRAM_BOT_TOKEN\s*=\s*["\']([^"\']*)["\']',
        'TELEGRAM_CHAT_ID': r'TELEGRAM_CHAT_ID\s*=\s*["\']([^"\']*)["\']',
        'CHECK_INTERVAL_MINUTES': r'CHECK_INTERVAL_MINUTES\s*=\s*(\d+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match and not match.group(1).startswith('your_'):
            values[key] = int(match.group(1)) if key == "CHECK_INTERVAL_MINUTES" else match.group(1)
    
    return values

def merge_dict_values(old_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    두 딕셔너리를 병합하되, 중요한 설정값들은 old_dict에서 유지합니다.
    """
    merged = new_dict.copy()
    
    def merge_recursive(old_val: Any, new_val: Any) -> Any:
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            result = new_val.copy()
            for k, v in old_val.items():
                if k in new_val:
                    result[k] = merge_recursive(v, new_val[k])
                # 기존에만 있던 설정도 유지
                elif k not in ['enabled']:  # 'enabled' 같은 기본 설정은 새 버전 우선
                    result[k] = v
            return result
        else:
            # 값이 기본값이 아닌 경우 기존 값 유지
            if old_val != new_val and old_val is not None:
                return old_val
            return new_val
    
    for key, new_value in new_dict.items():
        if key in old_dict:
            merged[key] = merge_recursive(old_dict[key], new_value)
    
    return merged

def format_dict_content(var_name: str, dict_data: Dict[str, Any], example_content: str) -> str:
    """딕셔너리를 example 파일과 같은 형식으로 포매팅합니다."""
    
    def format_value(value: Any, indent_level: int = 1) -> str:
        indent = "    " * indent_level
        
        if isinstance(value, dict):
            if not value:
                return "{}"
            
            lines = ["{"]
            for k, v in value.items():
                formatted_v = format_value(v, indent_level + 1)
                
                # example 파일에서 해당 키의 주석 찾기
                key_pattern = rf'["\']?{re.escape(k)}["\']?\s*:\s*.*?#\s*(.+?)(?=\n|,)'
                comment_match = re.search(key_pattern, example_content, re.MULTILINE)
                comment = f"  # {comment_match.group(1).strip()}" if comment_match else ""
                
                if isinstance(v, dict):
                    lines.append(f'{indent}"{k}": {formatted_v},{comment}')
                elif isinstance(v, list):
                    lines.append(f'{indent}"{k}": {repr(v)},{comment}')
                elif isinstance(v, str):
                    lines.append(f'{indent}"{k}": "{v}",{comment}')
                else:
                    lines.append(f'{indent}"{k}": {repr(v)},{comment}')
            
            lines.append("    " * (indent_level - 1) + "}")
            return "\n".join(lines)
        
        elif isinstance(value, list):
            return repr(value)
        else:
            return repr(value)
    
    formatted = format_value(dict_data, 1)
    return f"{var_name} = {formatted}"

def update_config():
    """config.py를 config.example.py 기준으로 스마트 업데이트"""
    
    example_path = "config.example.py"
    config_path = "config.py"
    backup_path = "config.py.backup"
    
    if not os.path.exists(example_path):
        print("❌ config.example.py 파일이 없습니다.")
        return False
    
    # example 파일 읽기
    with open(example_path, 'r', encoding='utf-8') as f:
        example_content = f.read()
    
    # 기존 config 파일이 있으면 읽기
    old_dict_values = {}
    old_simple_values = {}
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            old_content = f.read()
            old_structure = parse_config_structure(old_content)
            
            # 백업 생성
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(old_content)
            print(f"✅ 기존 config.py를 {backup_path}로 백업했습니다.")
        
        # 기존 값들 추출
        for var_name, var_info in old_structure.items():
            if var_info['type'] == 'dict':
                old_dict_values[var_name] = extract_dict_values(var_info['content'])
        
        # 간단한 문자열 값들 추출
        old_simple_values = extract_simple_values(old_content)
    
    # example 구조 파싱
    new_structure = parse_config_structure(example_content)
    
    # 새 config 생성
    updated_content = example_content
    
    # 딕셔너리 변수들 처리
    for var_name in new_structure:
        if new_structure[var_name]['type'] == 'dict' and var_name in old_dict_values:
            new_dict = extract_dict_values(new_structure[var_name]['content'])
            merged_dict = merge_dict_values(old_dict_values[var_name], new_dict)
            
            # 새로운 딕셔너리 내용으로 교체
            formatted_dict = format_dict_content(var_name, merged_dict, example_content)
            
            # 정규식으로 해당 변수 부분을 교체
            var_pattern = rf'^{var_name}\s*=\s*{{.*?^}}'
            updated_content = re.sub(var_pattern, formatted_dict, updated_content, flags=re.MULTILINE | re.DOTALL)
    
    # 간단한 문자열 변수들 처리
    for key, value in old_simple_values.items():
        if isinstance(value, int):
            pattern = rf'{key}\s*=\s*\d+'
            replacement = f'{key} = {value}'
        else:
            pattern = rf'{key}\s*=\s*["\'][^"\']*["\']'
            replacement = f'{key} = "{value}"'
        
        updated_content = re.sub(pattern, replacement, updated_content)
        print(f"✅ {key} 값이 보존되었습니다.")

    # 새 파일 쓰기
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ config.py가 성공적으로 업데이트되었습니다.")
    print("🔧 새로운 설정이 추가되고 기존 사용자 설정은 보존되었습니다.")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Config 스마트 업데이트 도구")
        print("사용법: python update_config.py")
        print("")
        print("기능:")
        print("- config.example.py를 기준으로 config.py 업데이트")
        print("- 새로운 설정 자동 추가")
        print("- API 키, 토큰 등 기존 사용자 설정 보존")
        print("- 자동 백업 생성")
        sys.exit(0)
    
    update_config()
