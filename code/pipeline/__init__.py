"""
堰塞湖快速評估管線，依資料流分成：

    ingest       清冊、CWA、風險模型、人工觀測
    preprocess   SAR 濾波與幾何遮罩
    detect       水體、崩塌、疑似堰塞湖分級
    assess       蓄水量、級距、淹沒、暴露
    attribution  成因敘述與溢流預報
"""

__version__ = "0.1.0"
