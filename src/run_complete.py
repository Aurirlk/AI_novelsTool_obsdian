"""
AI写作助手 - 完整版启动器
包含所有功能模块
"""

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


class _LogWriter:
    """将 print 输出重定向到日志文件（替代 sys.stdout/sys.stderr）"""

    def __init__(self, logger: logging.Logger, level: int = logging.INFO):
        self.logger = logger
        self.level = level
        self._buf = ""

    def write(self, text: str):
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.strip()
            if line:
                self.logger.log(self.level, line)

    def flush(self):
        if self._buf.strip():
            self.logger.log(self.level, self._buf.strip())
            self._buf = ""

    def fileno(self):
        return -1


def _setup_logging() -> logging.Logger:
    """配置日志：文件输出，不在控制台打印"""
    os.makedirs(_LOG_DIR, exist_ok=True)
    log_file = os.path.join(_LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 文件 handler（utf-8）
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root_logger.addHandler(fh)

    # 第三方库降级
    for name in ("httpx", "httpcore", "openai", "chromadb", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logger = logging.getLogger("app")

    # 重定向 stdout/stderr → 日志文件（捕获所有 print）
    sys.stdout = _LogWriter(logger, logging.INFO)
    sys.stderr = _LogWriter(logger, logging.ERROR)

    return logger


def main():
    logger = _setup_logging()
    logger.info("=" * 40)
    logger.info("AI写作助手 v2.0.0 启动")
    logger.info("日志文件: %s", os.path.join(_LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log"))
    logger.info("=" * 40)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))

    from src.gui.professional_main_window import ProfessionalMainWindow

    window = ProfessionalMainWindow()
    window.show()

    # 首次启动向导：未配置 API 密钥时引导配置
    try:
        from src.gui.onboarding_wizard import show_onboarding_if_needed
        show_onboarding_if_needed(window)
    except Exception as e:
        logger.warning("启动向导异常: %s", e)

    logger.info("应用启动成功")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
