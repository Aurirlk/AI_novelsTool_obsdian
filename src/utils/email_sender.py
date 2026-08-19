"""
邮箱投递模块
一键把小说章节通过 SMTP 发送到编辑邮箱（内置实现，零第三方依赖）
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header
from typing import List, Optional


# 常用邮箱 SMTP 预设（国内网文作者常用）
SMTP_PRESETS = {
    "QQ邮箱": {"host": "smtp.qq.com", "port": 465, "ssl": True, "tls": False},
    "163邮箱": {"host": "smtp.163.com", "port": 465, "ssl": True, "tls": False},
    "126邮箱": {"host": "smtp.126.com", "port": 465, "ssl": True, "tls": False},
    "腾讯企业邮箱": {"host": "smtp.exmail.qq.com", "port": 465, "ssl": True, "tls": False},
    "阿里云邮箱": {"host": "smtp.mxhichina.com", "port": 465, "ssl": True, "tls": False},
    "Gmail": {"host": "smtp.gmail.com", "port": 587, "ssl": False, "tls": True},
    "Outlook": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False, "tls": True},
}


def get_email_config() -> dict:
    """从设置读取邮箱配置"""
    from src.data.settings_manager import get_settings_manager
    sm = get_settings_manager()
    cfg = {
        "preset": sm.get_setting("email", "preset", "QQ邮箱"),
        "smtp_host": sm.get_setting("email", "smtp_host", ""),
        "smtp_port": int(sm.get_setting("email", "smtp_port", "465") or 465),
        "use_ssl": sm.get_setting("email", "use_ssl", "true"),
        "sender_email": sm.get_setting("email", "sender_email", ""),
        "auth_code": sm.get_setting("email", "auth_code", ""),
        "editor_email": sm.get_setting("email", "editor_email", ""),
        "sender_name": sm.get_setting("email", "sender_name", "AI写作助手"),
    }
    return cfg


def save_email_config(preset: str, smtp_host: str, smtp_port: int, use_ssl: bool,
                      sender_email: str, auth_code: str,
                      editor_email: str, sender_name: str = "AI写作助手"):
    """保存邮箱配置到设置"""
    from src.data.settings_manager import get_settings_manager
    sm = get_settings_manager()
    sm.set_setting("email", "preset", preset)
    sm.set_setting("email", "smtp_host", smtp_host)
    sm.set_setting("email", "smtp_port", str(smtp_port))
    sm.set_setting("email", "use_ssl", "true" if use_ssl else "false")
    sm.set_setting("email", "sender_email", sender_email)
    sm.set_setting("email", "auth_code", auth_code)
    sm.set_setting("email", "editor_email", editor_email)
    sm.set_setting("email", "sender_name", sender_name)


def resolve_smtp(preset: str, custom_host: str = "", custom_port: int = 465,
                 custom_ssl: bool = True) -> dict:
    """解析 SMTP 配置：预设优先，有自定义则用自定义"""
    base = SMTP_PRESETS.get(preset, SMTP_PRESETS["QQ邮箱"])
    if custom_host:
        return {"host": custom_host, "port": custom_port, "ssl": custom_ssl}
    return dict(base)


def build_message(sender_email: str, sender_name: str, to_emails: List[str],
                  subject: str, body: str,
                  attachments: Optional[List[str]] = None) -> MIMEMultipart:
    """
    构建 MIME 邮件消息

    Args:
        sender_email: 发件邮箱
        sender_name: 发件人名称
        to_emails: 收件人列表（支持多收件人）
        subject: 邮件主题
        body: 邮件正文（纯文本）
        attachments: 附件文件路径列表

    Returns:
        MIMEMultipart 消息对象
    """
    msg = MIMEMultipart()
    msg["From"] = f"{Header(sender_name, 'utf-8')} <{sender_email}>"
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = Header(subject, "utf-8")

    msg.attach(MIMEText(body, "plain", "utf-8"))

    for path in (attachments or []):
        if not path or not os.path.isfile(path):
            continue
        fname = os.path.basename(path)
        with open(path, "rb") as f:
            part = MIMEApplication(f.read())
        part.add_header("Content-Disposition", "attachment",
                        filename=("utf-8", "", fname))
        msg.attach(part)

    return msg


def send_email(sender_email: str, auth_code: str, smtp_host: str, smtp_port: int,
               use_ssl: bool, to_emails: List[str], subject: str, body: str,
               attachments: Optional[List[str]] = None,
               sender_name: str = "AI写作助手") -> tuple[bool, str]:
    """
    通过 SMTP 发送邮件

    Returns:
        (是否成功, 说明)
    """
    msg = build_message(sender_email, sender_name, to_emails, subject, body, attachments)

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            try:
                server.starttls()
            except Exception:
                pass
        server.login(sender_email, auth_code)
        server.sendmail(sender_email, to_emails, msg.as_string())
        server.quit()
        return True, f"已发送到 {', '.join(to_emails)}"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP 认证失败：请确认使用授权码（不是登录密码），且已开启 SMTP 服务"
    except smtplib.SMTPRecipientsRefused:
        return False, "收件人地址被拒绝：请检查编辑邮箱地址是否正确"
    except Exception as e:
        return False, f"发送失败：{e}"


def test_connection(sender_email: str, auth_code: str, smtp_host: str,
                    smtp_port: int, use_ssl: bool) -> tuple[bool, str]:
    """测试 SMTP 连接（不发送邮件）"""
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        server.login(sender_email, auth_code)
        server.quit()
        return True, "连接成功，SMTP 配置有效"
    except smtplib.SMTPAuthenticationError:
        return False, "认证失败：请确认使用授权码（不是登录密码）"
    except Exception as e:
        return False, f"连接失败：{e}"


def send_chapter_to_editor(book_title: str, chapter_title: str, content: str,
                           editor_email: Optional[str] = None,
                           attachments: Optional[List[str]] = None) -> tuple[bool, str]:
    """
    一键把章节投递到编辑邮箱（读取设置中的邮箱配置）

    Args:
        book_title: 书名
        chapter_title: 章节标题
        content: 章节正文
        editor_email: 收件编辑邮箱（默认用设置里的编辑邮箱）
        attachments: 附件文件路径列表

    Returns:
        (是否成功, 说明)
    """
    cfg = get_email_config()
    if not cfg["sender_email"] or not cfg["auth_code"]:
        return False, "请先在 系统设置 → 邮箱投递 中配置发件邮箱和授权码"
    if not cfg["editor_email"] and not editor_email:
        return False, "请先在 系统设置 → 邮箱投递 中配置编辑邮箱，或指定收件人"

    to = [editor_email] if editor_email else [cfg["editor_email"]]
    smtp = resolve_smtp(cfg["preset"], cfg["smtp_host"], cfg["smtp_port"],
                        str(cfg.get("use_ssl", "true")).lower() in ("true", "1", "yes"))

    subject = f"【投稿】{book_title} - {chapter_title}"
    body = (
        f"您好：\n\n"
        f"我是网文作者，投稿以下章节，请查收附件。\n\n"
        f"书名：{book_title}\n"
        f"章节：{chapter_title}\n\n"
        f"正文预览：\n{content[:500]}\n\n"
        f"—— {cfg['sender_name']}"
    )

    return send_email(
        cfg["sender_email"], cfg["auth_code"],
        smtp["host"], smtp["port"], smtp["ssl"],
        to, subject, body, attachments, cfg["sender_name"],
    )
