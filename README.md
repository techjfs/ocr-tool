## OCR-Tool【WIP】

一个OCR小工具，可以和[goldendict-ng](https://github.com/xiaoyifang/goldendict-ng)搭配使用

利用LLM(Claude/ChatGPT)，与AI结对编程，共同完成了此项目

支持的核心功能：
1. `alt+c`进行截图取词 
   + 1.1 截图依赖图片的清晰度，有时候会有误判的概率
2. `alt+鼠标左键`进行悬停取词(需要开启此功能)
   + 2.1 悬停识别准确率相对截图会高些，但依赖鼠标的位置，有时候位置最接近的两个词会有选择错误的情况

注意:
1. 支持跨平台使用，Windows系统和MacOS系统
2. MacOS有自己的一套OCR技术，可参考[Shortcuts.app & Apple's OCR](https://xiaoyifang.github.io/goldendict-ng/howto/ocr/#shortcutsapp-apples-ocr)

核心技术:
+ [PaddleOCR, v5版本](https://paddlepaddle.github.io/PaddleOCR/main/quick_start.html)

## TODO
- [ ] 重构热键管理，支持Mac和Windows
- [ ] 优先保证Windows下功能正常
- [ ] 验证在MacOS下软件功能是否正常
- [ ] 打包方式完善
- [ ] 兼容CPU和GPU的ocr_engine，根据用户配置决定使用哪个版本
- [ ] 将部分参数配置化
- [ ] GUI美化，保持界面风格一致
- [ ] 如果OCR取词出现同分数，考虑是否返回多个，让用户决定
- [ ] 默认使用的是CPU版本的PaddleOCR测试功能，未来有可能的话会尝试GPU版本(不紧急不重要)

## 安装依赖
```bash
pip install -r requirements.txt
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
1. 打包时Cython依赖不全(已在OCR-Tool.spec中处理该问题)
2. 程序版本升级，如何对用户的旧配置进行升级(已settings_manager中处理该问题)

配置升级过程可以安排在程序启动时，启动有个进度条，这个进度条的进度和启动过程中要做的事情有关系