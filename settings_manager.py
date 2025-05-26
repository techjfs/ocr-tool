import sys
import json
from pathlib import Path
from PySide6.QtCore import QSettings

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
        "external_tool_exec_cmd": "",
        "capture_shortcuts": "alt+c",
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
