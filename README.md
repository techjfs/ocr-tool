# OCR-Tool

一个OCR小工具，使用Python实现，可以和[goldendict-ng](https://github.com/xiaoyifang/goldendict-ng)搭配使用
支持的核心功能：
1. `alt+c`进行截图取词
2. `alt+鼠标左键`进行悬停取词(需要开启此功能)

注意:
1. 不支持跨平台使用，仅限于Windows系统
2. MacOS有自己的一套OCR技术，可参考[Shortcuts.app & Apple's OCR](https://xiaoyifang.github.io/goldendict-ng/howto/ocr/#shortcutsapp-apples-ocr)

核心技术:
+ [PaddleOCR, v4版本](https://paddlepaddle.github.io/PaddleOCR/latest/index.html)

## 安装依赖
```bash
pip install poetry

poetry install

pip install pyinstaller
```

## 打包
```bash
pyinstaller --name="OCR-Tool" --icon _internal/ocr.png --windowed --onefile --collect-all paddleocr main.py
```
or

```bash
pyinstaller OCR-Tool.spec --clean -y
```

项目里已生成好OCR-Tool.spec文件，推荐直接使用后者来打包

## 遇到的问题
1. PaddleOCR不能设置同时支持中英文，使用中文识别英文，会忽略空格，若使用英文，则能正常识别。(目前ocr_engine.py已处理该问题)
2. 打包时Cython依赖不全(已在OCR-Tool.spec中处理该问题)