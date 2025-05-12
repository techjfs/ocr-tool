# OCR-Tool

## 安装依赖
```bash
pip install poetry

poetry install
```

## 打包
```bash
poetry run pyinstaller --name="OCR-Tool" --icon ocr.png --windowed --onefile --collect-all paddleocr capture_pick.py
```
or

```bash
poetry run pyinstaller OCR-Tool.spec --clean -y
```