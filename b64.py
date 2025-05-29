from flask import Flask, request, render_template_string
from typing import Dict, List

class Custom64:
    """
    使用中文词语作为 Base64 编码映射表的自定义编码器 / 解码器。
    - 0-63: 对应 64 个中文词条
    - 65    : 填充符号
    """

    def __init__(self, mapping: Dict[str, str], pad_symbol: str = '的') -> None:
        self.encode_map: Dict[int, str] = {int(k): v for k, v in mapping.items()}
        self.pad_index = 65
        self.decode_map: Dict[str, int] = {v: k for k, v in self.encode_map.items()}
        self.encode_map[self.pad_index] = pad_symbol
        self.decode_map[pad_symbol] = self.pad_index

    def encode(self, text: str, bit_width: int = 6) -> str:
        data = text.encode('utf-8')
        bin_str = ''.join(f"{byte:08b}" for byte in data)
        chunks = self._chunk_and_pad(bin_str, bit_width)
        result = []
        for chunk in chunks:
            idx = int(chunk, 2)
            if idx == 0 and set(chunk) == {'0'}:
                idx = self.pad_index
            result.append(self.encode_map[idx])
        return ''.join(result)

    def decode(self, encoded: str, bit_width: int = 6) -> str:
        idx_list = [self.decode_map.get(tok) for tok in self._segment(encoded)]
        if None in idx_list:
            raise ValueError("输入包含未定义的映射符号")
        bin_str = ''.join(
            '0' * bit_width if idx == self.pad_index else f"{idx:0{bit_width}b}"
            for idx in idx_list
        )
        byte_chunks = [bin_str[i:i+8] for i in range(0, len(bin_str), 8)]
        data_bytes = bytearray()
        for bstr in byte_chunks:
            if set(bstr) == {'0'}:
                continue
            data_bytes.append(int(bstr, 2))
        return data_bytes.decode('utf-8')

    def _chunk_and_pad(self, bitstr: str, width: int) -> List[str]:
        rem = len(bitstr) % width
        if rem:
            bitstr += '0' * (width - rem)
        return [bitstr[i:i+width] for i in range(0, len(bitstr), width)]

    def _segment(self, encoded: str) -> List[str]:
        tokens = sorted(self.decode_map.keys(), key=len, reverse=True)
        segments, i, n = [], 0, len(encoded)
        while i < n:
            for tok in tokens:
                if encoded.startswith(tok, i):
                    segments.append(tok)
                    i += len(tok)
                    break
            else:
                raise ValueError(f"无法识别的编码片段，从位置 {i} 开始")
        return segments

# 示例映射表, 可替换为实际中文词条映射
sample_map = {
    **{str(i): tok for i, tok in enumerate([
        "香香","软软","甜甜","糯糯","蜂蜜","奶油","腻腻","酥酥","脆脆","滑滑","嫩嫩",
        "番茄炒可乐","番茄炒科比","草莓","蓝莓","苹果","香蕉","葡萄","酸酸","辣辣",
        "爽爽","咸咸","鲜鲜","苦苦","甘甘","绵绵","弹弹","润润","油油","清清",
        "浓浓","醇醇","淡淡","幽幽","热热乎乎","冰冰凉凉","黏黏","糊糊","麻麻",
        "橙子","西瓜","樱桃","菠萝","猕猴桃","桃子","梨","杏","李子","西红柿",
        "黄瓜","胡萝卜","生菜","菠菜","花椰菜","卷心菜","洋葱","大蒜","土豆","红薯",
        "南瓜","玉米","豌豆","扁豆","红豆","绿豆","黄豆","黑豆"
    ])},
    '65': '的'
}

app = Flask(__name__)
coder = Custom64(sample_map)

HTML = '''
<!doctype html>
<html lang="zh">
<head>
    <meta charset="utf-8">
    <title>Custom64 编解码</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f4f8; color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 90%; max-width: 600px; }
        h1 { margin-bottom: 1rem; text-align: center; color: #007ACC; }
        textarea { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; }
        .btn-group { display: flex; justify-content: space-between; margin-top: 1rem; }
        button { flex: 1; margin: 0 0.5rem; padding: 0.75rem; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; transition: background 0.3s; }
        button:first-child { margin-left: 0; }
        button:last-child { margin-right: 0; }
        .encode { background: #28a745; color: #fff; }
        .encode:hover { background: #218838; }
        .decode { background: #17a2b8; color: #fff; }
        .decode:hover { background: #138496; }
        .result { margin-top: 1.5rem; word-wrap: break-word; background: #eef; padding: 1rem; border-radius: 6px; }
        .copy-btn { background: #ffc107; color: #212529; float: right; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.9rem; margin-top: -1.5rem; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>啊宝宝编码</h1>
        <form method="post">
            <textarea id="text-input" name="text" rows="4" placeholder="输入文本或编码"></textarea>
            <div class="btn-group">
                <button type="submit" name="action" value="encode" class="encode">加密</button>
                <button type="submit" name="action" value="decode" class="decode">解密</button>
            </div>
        </form>
        {% if result is not none %}
        <div class="result">
            <button class="copy-btn" onclick="copyResult()">复制</button>
            <p id="result-text">{{ result }}</p>
        </div>
        {% endif %}
    </div>
    <script>
        function copyResult() {
            const text = document.getElementById('result-text').innerText;
            navigator.clipboard.writeText(text).then(() => {
                alert('结果已复制到剪贴板');
            });
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        action = request.form.get('action')
        text = request.form.get('text', '')
        try:
            if action == 'encode':
                result = "啊啊啊啊啊啊宝宝你是一个" + coder.encode(text) + "的小蛋糕"
            elif action == 'decode':
                result = coder.decode(text)
        except Exception as e:
            result = f"错误: {e}"
    return render_template_string(HTML, result=result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
