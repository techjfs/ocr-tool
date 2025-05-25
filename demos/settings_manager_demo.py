import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                               QHBoxLayout, QWidget, QPushButton, QLabel,
                               QSpinBox, QCheckBox, QComboBox, QLineEdit,
                               QDialog, QDialogButtonBox, QFormLayout,
                               QColorDialog, QFontDialog, QMessageBox)
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont, QColor


class SettingsManager:
    # 配置版本和迁移规则
    CURRENT_CONFIG_VERSION = "1.0.0"

    # 配置迁移映射表
    MIGRATION_RULES = {
        "1.0.0": {
            "version": "1.0.1",
            "mappings": {
                # "old_key": "new_key",
            }, # 字段重命名
            "transforms": {
                # "transform_key": lambda x: x,
            }, # 类型转换
            "removed_fields": [
                # "delete_old_key",
            ],  # 已移除的字段
            "new_defaults": {
                # "new_key": "new_value",
            } # 新增字段
        },
    }

    # 默认配置
    DEFAULT_CONFIG = {
        "config_version": CURRENT_CONFIG_VERSION,
        "external_tool_exec_cmd": ""
    }

    def __init__(self, config_file=None, use_file_storage=True):
        self.use_file_storage = use_file_storage

        if use_file_storage:
            # 使用文件存储模式
            if config_file is None:
                # 获取程序运行目录
                if getattr(sys, 'frozen', False):
                    # 如果是打包后的exe文件
                    app_dir = Path(sys.executable).parent
                else:
                    # 如果是直接运行Python脚本
                    app_dir = Path(__file__).parent

                config_file = app_dir / "config.json"

            self.config_file = Path(config_file)
            self.settings_data = self._load_and_migrate_config()
        else:
            # 使用系统默认存储（注册表/系统配置）
            self.settings = QSettings("MyCompany", "MyApp")
            self.settings_data = {}

    def _load_and_migrate_config(self):
        """加载配置并进行版本迁移"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # 检查配置版本
                current_version = config_data.get("config_version", "1.0.0")

                if current_version != self.CURRENT_CONFIG_VERSION:
                    print(f"检测到配置版本 {current_version}，开始迁移到 {self.CURRENT_CONFIG_VERSION}")

                    # 备份旧配置
                    self._backup_old_config(config_data, current_version)

                    # 执行迁移
                    migrated_config = self._migrate_config(config_data, current_version)

                    # 保存迁移后的配置
                    self._save_migrated_config(migrated_config)

                    return migrated_config
                else:
                    # 版本一致，直接返回
                    return self._ensure_all_defaults(config_data)

        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置文件失败: {e}")

        # 如果加载失败或文件不存在，返回默认配置
        return self.DEFAULT_CONFIG.copy()

    def _backup_old_config(self, old_config, version):
        """备份旧配置文件"""
        try:
            backup_file = self.config_file.with_suffix(f'.backup_v{version}.json')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(old_config, f, ensure_ascii=False, indent=2)
            print(f"旧配置已备份到: {backup_file}")
        except Exception as e:
            print(f"备份旧配置失败: {e}")

    def _migrate_config(self, old_config, from_version):
        """执行配置迁移"""
        current_config = old_config.copy()
        current_version = from_version

        # 逐步迁移到最新版本
        while current_version != self.CURRENT_CONFIG_VERSION:
            if current_version not in self.MIGRATION_RULES:
                print(f"警告: 找不到版本 {current_version} 的迁移规则")
                break

            rule = self.MIGRATION_RULES[current_version]
            next_version = rule["version"]

            print(f"正在从 {current_version} 迁移到 {next_version}")

            # 应用字段映射
            if "mappings" in rule:
                for old_key, new_key in rule["mappings"].items():
                    if old_key in current_config:
                        current_config[new_key] = current_config.pop(old_key)

            # 应用数据转换
            if "transforms" in rule:
                for key, transform_func in rule["transforms"].items():
                    if key in current_config:
                        try:
                            current_config[key] = transform_func(current_config[key])
                        except Exception as e:
                            print(f"转换字段 {key} 失败: {e}")

            # 移除废弃字段
            if "removed_fields" in rule:
                for field in rule["removed_fields"]:
                    current_config.pop(field, None)

            # 添加新字段的默认值
            if "new_defaults" in rule:
                for key, default_value in rule["new_defaults"].items():
                    if key not in current_config:
                        current_config[key] = default_value

            # 更新版本号
            current_config["config_version"] = next_version
            current_version = next_version

        # 确保所有默认字段都存在
        return self._ensure_all_defaults(current_config)

    def _ensure_all_defaults(self, config):
        """确保配置包含所有默认字段"""
        for key, default_value in self.DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = default_value
        return config

    def _save_migrated_config(self, config):
        """保存迁移后的配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print("配置迁移完成并已保存")
        except Exception as e:
            print(f"保存迁移后的配置失败: {e}")

    def _load_from_file(self):
        """从JSON文件加载配置（已被_load_and_migrate_config替代）"""
        # 这个方法现在由_load_and_migrate_config处理
        pass

    def _save_to_file(self):
        """保存配置到JSON文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings_data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get_value(self, key, default_value=None, type=None):
        """获取设置值"""
        if self.use_file_storage:
            value = self.settings_data.get(key, default_value)

            # 类型转换
            if type is not None and value is not None:
                if type == bool:
                    if isinstance(value, str):
                        return value.lower() in ('true', '1', 'yes', 'on')
                    return bool(value)
                elif type == int:
                    return int(value)
                elif type == float:
                    return float(value)

            return value
        else:
            return self.settings.value(key, default_value, type=type)

    def set_value(self, key, value):
        """设置值"""
        if self.use_file_storage:
            self.settings_data[key] = value
        else:
            self.settings.setValue(key, value)

    def sync(self):
        """强制同步到磁盘"""
        if self.use_file_storage:
            return self._save_to_file()
        else:
            self.settings.sync()
            return True

    def get_all_keys(self):
        """获取所有键"""
        if self.use_file_storage:
            return list(self.settings_data.keys())
        else:
            return self.settings.allKeys()

    def get_config_info(self):
        """获取配置信息"""
        if self.use_file_storage:
            version = self.settings_data.get("config_version", "未知")
            return {
                "path": str(self.config_file.absolute()),
                "version": version,
                "exists": self.config_file.exists(),
                "size": self.config_file.stat().st_size if self.config_file.exists() else 0
            }
        else:
            return {"path": "系统配置存储", "version": "N/A"}

    def check_config_health(self):
        """检查配置文件健康状态"""
        issues = []

        if self.use_file_storage:
            # 检查文件是否存在
            if not self.config_file.exists():
                issues.append("配置文件不存在")
            else:
                try:
                    # 检查JSON格式是否正确
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 检查版本号
                    version = data.get("config_version")
                    if not version:
                        issues.append("缺少版本号")
                    elif version != self.CURRENT_CONFIG_VERSION:
                        issues.append(f"版本过旧: {version}")

                    # 检查必需字段
                    for key in self.DEFAULT_CONFIG:
                        if key not in data:
                            issues.append(f"缺少字段: {key}")

                except json.JSONDecodeError:
                    issues.append("JSON格式错误")
                except Exception as e:
                    issues.append(f"读取错误: {e}")

        return issues

    def reset_to_defaults(self):
        """重置为默认配置"""
        if self.use_file_storage:
            self.settings_data = self.DEFAULT_CONFIG.copy()
            return self._save_to_file()
        else:
            for key in self.settings.allKeys():
                self.settings.remove(key)
            for key, value in self.DEFAULT_CONFIG.items():
                self.settings.setValue(key, value)
            self.settings.sync()
            return True

    def backup_settings(self, backup_file=None):
        """备份设置"""
        if backup_file is None:
            backup_file = self.config_file.with_suffix('.backup.json')

        try:
            if self.use_file_storage:
                import shutil
                shutil.copy2(self.config_file, backup_file)
            else:
                # 对于QSettings，导出为JSON格式
                data = {}
                for key in self.settings.allKeys():
                    data[key] = self.settings.value(key)

                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False

    def restore_settings(self, backup_file):
        """从备份恢复设置"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            if self.use_file_storage:
                self.settings_data = backup_data
                self._save_to_file()
            else:
                for key, value in backup_data.items():
                    self.settings.setValue(key, value)
                self.settings.sync()

            return True
        except Exception as e:
            print(f"恢复失败: {e}")
            return False


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("应用设置")
        self.setModal(True)
        self.resize(400, 300)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 创建表单布局
        form_layout = QFormLayout()

        # 用户名设置
        self.username_edit = QLineEdit()
        form_layout.addRow("用户名:", self.username_edit)

        # 自动保存间隔
        self.autosave_spinbox = QSpinBox()
        self.autosave_spinbox.setRange(1, 60)
        self.autosave_spinbox.setSuffix(" 分钟")
        form_layout.addRow("自动保存间隔:", self.autosave_spinbox)

        # 启用通知
        self.notification_checkbox = QCheckBox()
        form_layout.addRow("启用通知:", self.notification_checkbox)

        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "系统默认"])
        form_layout.addRow("主题:", self.theme_combo)

        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English", "日本語"])
        form_layout.addRow("语言:", self.language_combo)

        layout.addLayout(form_layout)

        # 字体和颜色设置
        font_color_layout = QHBoxLayout()

        self.font_button = QPushButton("选择字体")
        self.font_button.clicked.connect(self.choose_font)
        font_color_layout.addWidget(self.font_button)

        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self.choose_color)
        font_color_layout.addWidget(self.color_button)

        layout.addLayout(font_color_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)

        layout.addWidget(button_box)

        self.setLayout(layout)

        # 用于存储选择的字体和颜色
        self.selected_font = None
        self.selected_color = None

    def load_settings(self):
        """从设置中加载当前值"""
        self.username_edit.setText(self.settings_manager.get_value("username", ""))
        self.autosave_spinbox.setValue(int(self.settings_manager.get_value("autosave_interval", 5)))
        self.notification_checkbox.setChecked(
            self.settings_manager.get_value("enable_notifications", True, type=bool)
        )
        self.theme_combo.setCurrentText(self.settings_manager.get_value("theme", "浅色"))
        self.language_combo.setCurrentText(self.settings_manager.get_value("language", "中文"))

        # 加载字体设置
        font_family = self.settings_manager.get_value("font_family", "Arial")
        font_size = int(self.settings_manager.get_value("font_size", 12))
        self.selected_font = QFont(font_family, font_size)

        # 加载颜色设置
        color_name = self.settings_manager.get_value("color", "#000000")
        self.selected_color = QColor(color_name)

    def choose_font(self):
        """选择字体"""
        ok, font = QFontDialog.getFont(self.selected_font or QFont(), self)
        if ok:
            self.selected_font = font
            self.font_button.setText(f"字体: {font.family()}, {font.pointSize()}pt")

    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.selected_color or QColor(), self)
        if color.isValid():
            self.selected_color = color
            # 更新按钮背景色以显示选择的颜色
            self.color_button.setStyleSheet(f"background-color: {color.name()}")

    def restore_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认", "确定要恢复默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.username_edit.setText("")
            self.autosave_spinbox.setValue(5)
            self.notification_checkbox.setChecked(True)
            self.theme_combo.setCurrentText("浅色")
            self.language_combo.setCurrentText("中文")
            self.selected_font = QFont("Arial", 12)
            self.selected_color = QColor("#000000")
            self.font_button.setText("选择字体")
            self.color_button.setStyleSheet("")

    def accept(self):
        """保存设置"""
        self.save_settings()
        super().accept()

    def save_settings(self):
        """保存所有设置"""
        self.settings_manager.set_value("username", self.username_edit.text())
        self.settings_manager.set_value("autosave_interval", self.autosave_spinbox.value())
        self.settings_manager.set_value("enable_notifications", self.notification_checkbox.isChecked())
        self.settings_manager.set_value("theme", self.theme_combo.currentText())
        self.settings_manager.set_value("language", self.language_combo.currentText())

        if self.selected_font:
            self.settings_manager.set_value("font_family", self.selected_font.family())
            self.settings_manager.set_value("font_size", self.selected_font.pointSize())

        if self.selected_color:
            self.settings_manager.set_value("color", self.selected_color.name())

        # 强制同步到磁盘
        self.settings_manager.sync()


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        # 创建设置管理器，使用文件存储模式
        self.settings_manager = SettingsManager(use_file_storage=True)
        self.setWindowTitle("PySide6 设置示例 - 文件存储模式")
        self.resize(700, 500)

        self.setup_ui()
        self.apply_settings()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # 显示配置文件信息
        config_info = self.settings_manager.get_config_info()
        config_info_text = f"配置文件: {config_info['path']}\n版本: {config_info['version']}"
        if config_info.get('size'):
            config_info_text += f" | 大小: {config_info['size']} bytes"

        config_path_label = QLabel(config_info_text)
        config_path_label.setWordWrap(True)
        config_path_label.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 10px;")
        layout.addWidget(config_path_label)

        # 显示当前设置的标签
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # 按钮
        button_layout = QHBoxLayout()

        settings_button = QPushButton("打开设置")
        settings_button.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_button)

        refresh_button = QPushButton("刷新显示")
        refresh_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(refresh_button)

        backup_button = QPushButton("备份设置")
        backup_button.clicked.connect(self.backup_settings)
        button_layout.addWidget(backup_button)

        open_folder_button = QPushButton("打开配置文件夹")
        open_folder_button.clicked.connect(self.open_config_folder)
        button_layout.addWidget(open_folder_button)

        # 新增按钮
        check_button = QPushButton("检查配置")
        check_button.clicked.connect(self.check_config_health)
        button_layout.addWidget(check_button)

        reset_button = QPushButton("重置配置")
        reset_button.clicked.connect(self.reset_config)
        button_layout.addWidget(reset_button)

        layout.addLayout(button_layout)
        central_widget.setLayout(layout)

    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_settings()
            QMessageBox.information(self, "成功", "设置已保存并应用！")

    def backup_settings(self):
        """备份设置"""
        if self.settings_manager.backup_settings():
            QMessageBox.information(self, "成功", "设置已备份！")
        else:
            QMessageBox.warning(self, "失败", "备份设置失败！")

    def check_config_health(self):
        """检查配置文件健康状态"""
        issues = self.settings_manager.check_config_health()

        if not issues:
            QMessageBox.information(self, "配置检查", "配置文件状态正常！")
        else:
            issue_text = "发现以下问题:\n" + "\n".join(f"• {issue}" for issue in issues)
            QMessageBox.warning(self, "配置检查", issue_text)

    def reset_config(self):
        """重置配置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有配置到默认值吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.settings_manager.reset_to_defaults():
                self.apply_settings()
                QMessageBox.information(self, "成功", "配置已重置为默认值！")
            else:
                QMessageBox.warning(self, "失败", "重置配置失败！")

    def open_config_folder(self):
        """打开配置文件所在文件夹"""
        config_info = self.settings_manager.get_config_info()
        config_path = Path(config_info['path'])
        folder_path = config_path.parent

        # 跨平台打开文件夹
        import subprocess
        import platform

        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(folder_path)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(folder_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(folder_path)])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件夹: {e}")

    def apply_settings(self):
        """应用当前设置"""
        # 获取设置值
        username = self.settings_manager.get_value("username", "未设置")
        autosave = self.settings_manager.get_value("autosave_interval", 5)
        notifications = self.settings_manager.get_value("enable_notifications", True, type=bool)
        theme = self.settings_manager.get_value("theme", "浅色")
        language = self.settings_manager.get_value("language", "中文")

        # 字体设置
        font_family = self.settings_manager.get_value("font_family", "Arial")
        font_size = int(self.settings_manager.get_value("font_size", 12))
        font = QFont(font_family, font_size)

        # 颜色设置
        color_name = self.settings_manager.get_value("color", "#000000")
        color = QColor(color_name)

        # 更新显示
        info_text = f"""
当前设置:
用户名: {username}
自动保存间隔: {autosave} 分钟
启用通知: {'是' if notifications else '否'}
主题: {theme}
语言: {language}
字体: {font_family}, {font_size}pt
颜色: {color_name}
        """

        # 应用字体和颜色
        self.info_label.setText(info_text.strip())
        self.info_label.setFont(font)

        # 使用样式表设置颜色，更简单且兼容性更好
        self.info_label.setStyleSheet(f"color: {color_name};")

        # 应用主题（简单示例）
        if theme == "深色":
            self.setStyleSheet("""
                QMainWindow { background-color: #2b2b2b; color: white; }
                QLabel { color: white; }
                QPushButton { background-color: #404040; color: white; border: 1px solid #666; }
            """)
        else:
            self.setStyleSheet("")


def main():
    app = QApplication(sys.argv)

    # 设置应用程序信息，这会影响QSettings的存储位置
    app.setOrganizationName("MyCompany")
    app.setApplicationName("SettingsDemo")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()