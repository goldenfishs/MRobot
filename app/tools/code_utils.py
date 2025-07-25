import re

def preserve_user_region(new_code, old_code, region_name):
    """
    替换 new_code 中 region_name 区域为 old_code 中的内容（如果有）
    region_name: 如 'USER INCLUDE'
    """
    pattern = re.compile(
        rf"/\*\s*{region_name}\s*BEGIN\s*\*/(.*?)/\*\s*{region_name}\s*END\s*\*/",
        re.DOTALL
    )
    old_match = pattern.search(old_code or "")
    if not old_match:
        return new_code  # 旧文件没有该区域，直接返回新代码

    old_content = old_match.group(1)
    def repl(m):
        return m.group(0).replace(m.group(1), old_content)
    # 替换新代码中的该区域
    return pattern.sub(repl, new_code, count=1)