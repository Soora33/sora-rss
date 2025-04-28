def format_number(num) -> str:
    """格式化数字为易读形式"""
    if isinstance(num, str):
        if '万' in num:
            return num
        try:
            num = int(num)
        except:
            return num

    if isinstance(num, int):
        if num >= 10000:
            return f"{num/10000:.1f}万"
        return str(num)
    return num

def format_duration(seconds: int) -> str:
    """将秒数格式化为时分秒"""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
