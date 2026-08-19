"""
ChatGPT风格主题
简洁、大方、中性灰配色
"""


class ProfessionalTheme:
    """ChatGPT风格主题"""

    DARK = {
        "bg_primary": "#212121",
        "bg_secondary": "#171717",
        "bg_tertiary": "#2f2f2f",
        "bg_card": "#2a2a2a",
        "bg_hover": "#2f2f2f",
        "bg_active": "#3d3d3d",
        "bg_input": "#2f2f2f",

        "text_primary": "#ececec",
        "text_secondary": "#b4b4b4",
        "text_muted": "#8e8e8e",
        "text_inverse": "#ffffff",

        "accent": "#10a37f",
        "accent_hover": "#1ab58a",
        "accent_active": "#0d8a6c",
        "accent_light": "#1a3c34",

        "success": "#10a37f",
        "warning": "#f7b500",
        "danger": "#ef4146",
        "info": "#3e9fe0",

        "border": "#3a3a3a",
        "border_light": "#4a4a4a",
        "border_focus": "#10a37f",

        "shadow": "0 2px 8px rgba(0, 0, 0, 0.25)",
        "shadow_lg": "0 4px 16px rgba(0, 0, 0, 0.35)",

        "radius_sm": "6px",
        "radius_md": "10px",
        "radius_lg": "14px",

        "spacing_xs": "4px",
        "spacing_sm": "8px",
        "spacing_md": "16px",
        "spacing_lg": "24px",
        "spacing_xl": "32px",

        "font_family": "'Segoe UI', 'Microsoft YaHei', sans-serif",
        "font_size_xs": "11px",
        "font_size_sm": "12px",
        "font_size_md": "14px",
        "font_size_lg": "16px",
        "font_size_xl": "18px",
        "font_size_xxl": "24px",

        "font_weight_normal": "400",
        "font_weight_medium": "500",
        "font_weight_bold": "600",

        "transition": "all 0.2s ease",
    }

    LIGHT = {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f9f9f9",
        "bg_tertiary": "#f0f0f0",
        "bg_card": "#ffffff",
        "bg_hover": "#f0f0f0",
        "bg_active": "#e5e5e5",
        "bg_input": "#f4f4f4",

        "text_primary": "#0d0d0d",
        "text_secondary": "#5d5d5d",
        "text_muted": "#a0a0a0",
        "text_inverse": "#ffffff",

        "accent": "#10a37f",
        "accent_hover": "#0d8a6c",
        "accent_active": "#0b7559",
        "accent_light": "#d9f0e9",

        "success": "#10a37f",
        "warning": "#f7b500",
        "danger": "#ef4146",
        "info": "#3e9fe0",

        "border": "#e5e5e5",
        "border_light": "#eeeeee",
        "border_focus": "#10a37f",

        "shadow": "0 1px 3px rgba(0, 0, 0, 0.08)",
        "shadow_lg": "0 4px 12px rgba(0, 0, 0, 0.12)",

        "radius_sm": "6px",
        "radius_md": "10px",
        "radius_lg": "14px",

        "spacing_xs": "4px",
        "spacing_sm": "8px",
        "spacing_md": "16px",
        "spacing_lg": "24px",
        "spacing_xl": "32px",

        "font_family": "'Segoe UI', 'Microsoft YaHei', sans-serif",
        "font_size_xs": "11px",
        "font_size_sm": "12px",
        "font_size_md": "14px",
        "font_size_lg": "16px",
        "font_size_xl": "18px",
        "font_size_xxl": "24px",

        "font_weight_normal": "400",
        "font_weight_medium": "500",
        "font_weight_bold": "600",

        "transition": "all 0.2s ease",
    }

    @classmethod
    def get_theme(cls, theme_name: str = "dark") -> dict:
        if theme_name == "light":
            return cls.LIGHT
        return cls.DARK

    @classmethod
    def get_stylesheet(cls, theme_name: str = "dark") -> str:
        t = cls.get_theme(theme_name)

        return f"""
        QMainWindow, QWidget {{
            background-color: {t['bg_primary']};
            color: {t['text_primary']};
            font-family: {t['font_family']};
            font-size: {t['font_size_md']};
        }}

        /* 全局 QPushButton 基础样式：覆盖 Windows 原生渲染 */
        QPushButton {{
            background-color: transparent;
            color: {t['text_primary']};
            border: none;
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_md']};
            font-family: {t['font_family']};
            font-size: {t['font_size_md']};
        }}
        QPushButton:hover {{
            background-color: {t['bg_hover']};
        }}
        QPushButton:pressed {{
            background-color: {t['bg_active']};
        }}

        #sidebar {{
            background-color: {t['bg_secondary']};
            border-right: 1px solid {t['border']};
        }}

        #logo {{
            font-size: {t['font_size_xl']};
            font-weight: {t['font_weight_bold']};
            color: {t['text_primary']};
            padding: {t['spacing_md']};
        }}

        #nav_item {{
            background-color: transparent;
            border: none;
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_md']};
            text-align: left;
            color: {t['text_secondary']};
            font-size: {t['font_size_md']};
            font-weight: {t['font_weight_normal']};
        }}
        #nav_item:hover {{
            background-color: {t['bg_hover']};
            color: {t['text_primary']};
        }}

        #nav_item_active {{
            background-color: {t['bg_tertiary']};
            border: none;
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_md']};
            text-align: left;
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
            font-weight: {t['font_weight_bold']};
        }}

        #version {{
            color: {t['text_muted']};
            font-size: {t['font_size_sm']};
            padding: {t['spacing_md']};
        }}

        /* 分组标题（可折叠） */
        #nav_group_header {{
            background-color: transparent;
            border: none;
            text-align: left;
            color: {t['text_muted']};
            font-size: {t['font_size_sm']};
            font-weight: {t['font_weight_bold']};
            padding: {t['spacing_xs']} {t['spacing_sm']};
            margin-top: {t['spacing_sm']};
        }}
        #nav_group_header:hover {{
            color: {t['text_primary']};
        }}

        #page_title {{
            font-size: {t['font_size_xxl']};
            font-weight: {t['font_weight_bold']};
            color: {t['text_primary']};
            margin-bottom: {t['spacing_md']};
        }}

        #page_subtitle {{
            font-size: {t['font_size_lg']};
            color: {t['text_secondary']};
            margin-bottom: {t['spacing_lg']};
        }}

        #section_title {{
            font-size: {t['font_size_lg']};
            font-weight: {t['font_weight_bold']};
            color: {t['text_primary']};
            margin-bottom: {t['spacing_sm']};
        }}

        #card {{
            background-color: {t['bg_card']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_lg']};
            padding: {t['spacing_lg']};
            margin-bottom: {t['spacing_md']};
        }}
        #card:hover {{
            border-color: {t['border_light']};
        }}

        /* AI助手历史面板 */
        #history_panel {{
            background-color: {t['bg_card']};
            border-right: 1px solid {t['border']};
        }}
        #panel_title {{
            font-size: {t['font_size_md']};
            font-weight: {t['font_weight_bold']};
            color: {t['text_primary']};
        }}
        #history_list {{
            background-color: transparent;
            border: none;
            outline: none;
            font-size: {t['font_size_sm']};
        }}
        #history_list::item {{
            padding: 6px 8px;
            border-radius: {t['radius_md']};
            margin-bottom: 2px;
            color: {t['text_primary']};
        }}
        #history_list::item:hover {{
            background-color: {t['bg_hover']};
        }}
        #history_list::item:selected {{
            background-color: {t['bg_active']};
        }}

        /* 创作助手卡片（无CSS padding，由内部布局控制） */
        #assist_card {{
            background-color: {t['bg_card']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
        }}
        #assist_card:hover {{
            border-color: {t['accent']};
        }}

        /* 书籍卡片右上角设置键 */
        #card_gear {{
            background-color: transparent;
            border: none;
            border-radius: {t['radius_sm']};
        }}
        #card_gear:hover {{
            background-color: {t['bg_hover']};
        }}

        /* 编辑器工具栏图标按钮 */
        #tool_btn {{
            background-color: transparent;
            border: none;
            border-radius: {t['radius_sm']};
            padding: 4px;
        }}
        #tool_btn:hover {{
            background-color: {t['bg_hover']};
        }}
        #tool_btn:pressed {{
            background-color: {t['bg_active']};
        }}

        #btn_primary {{
            background-color: {t['accent']};
            color: {t['text_inverse']};
            border: none;
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_lg']};
            font-weight: {t['font_weight_medium']};
            font-size: {t['font_size_md']};
        }}
        #btn_primary:hover {{
            background-color: {t['accent_hover']};
        }}
        #btn_primary:pressed {{
            background-color: {t['accent_active']};
        }}
        #btn_primary:disabled {{
            background-color: {t['border']};
            color: {t['text_muted']};
        }}

        #btn_secondary {{
            background-color: transparent;
            color: {t['text_primary']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_lg']};
            font-weight: {t['font_weight_medium']};
            font-size: {t['font_size_md']};
        }}
        #btn_secondary:hover {{
            background-color: {t['bg_hover']};
        }}

        #btn_danger {{
            background-color: transparent;
            color: {t['danger']};
            border: 1px solid {t['danger']};
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_lg']};
            font-weight: {t['font_weight_medium']};
            font-size: {t['font_size_md']};
        }}
        #btn_danger:hover {{
            background-color: {t['danger']};
            color: {t['text_inverse']};
        }}

        #input {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_md']};
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
        }}
        #input:focus {{
            border-color: {t['border_focus']};
        }}

        #text_edit {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            padding: {t['spacing_md']};
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
        }}
        #text_edit:focus {{
            border-color: {t['border_focus']};
        }}

        /* 聊天气泡 */
        #bubble_user {{
            background-color: {t['accent']};
            color: {t['text_inverse']};
            border-radius: 18px;
            padding: 10px 16px;
            font-size: {t['font_size_md']};
        }}
        #bubble_ai {{
            background-color: {t['bg_tertiary']};
            color: {t['text_primary']};
            border-radius: 18px;
            padding: 12px 16px;
            font-size: {t['font_size_md']};
        }}
        #bubble_system {{
            background-color: transparent;
            color: {t['text_muted']};
            font-size: {t['font_size_sm']};
        }}
        #chat_input_area {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border']};
            border-radius: 24px;
        }}
        #chat_input_area:focus-within {{
            border-color: {t['border_focus']};
        }}
        #chat_input {{
            background-color: transparent;
            border: none;
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
            padding: 10px 14px;
        }}
        #btn_send {{
            background-color: {t['accent']};
            color: {t['text_inverse']};
            border: none;
            border-radius: 16px;
            font-size: {t['font_size_md']};
            font-weight: {t['font_weight_bold']};
        }}
        #btn_send:hover {{
            background-color: {t['accent_hover']};
        }}
        #btn_send:disabled {{
            background-color: {t['border']};
            color: {t['text_muted']};
        }}
        #chat_empty {{
            color: {t['text_muted']};
            font-size: {t['font_size_xl']};
        }}
        #chat_hint {{
            color: {t['text_muted']};
            font-size: {t['font_size_sm']};
        }}

        QComboBox {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_md']};
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
        }}
        QComboBox:focus {{
            border-color: {t['border_focus']};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: {t['spacing_md']};
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {t['text_secondary']};
        }}

        QSpinBox, QDoubleSpinBox {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_md']};
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {t['border_focus']};
        }}

        QGroupBox {{
            border: 1px solid {t['border']};
            border-radius: {t['radius_lg']};
            margin-top: {t['spacing_lg']};
            padding-top: {t['spacing_lg']};
            font-weight: {t['font_weight_bold']};
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {t['spacing_md']};
            padding: 0 {t['spacing_sm']};
        }}

        QTabWidget::pane {{
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            background-color: {t['bg_primary']};
            margin-top: -1px;
        }}
        QTabBar::tab {{
            background-color: transparent;
            border: none;
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']} {t['spacing_lg']};
            margin-right: 4px;
            color: {t['text_secondary']};
            font-size: {t['font_size_md']};
        }}
        QTabBar::tab:selected {{
            background-color: {t['bg_tertiary']};
            color: {t['text_primary']};
            font-weight: {t['font_weight_bold']};
        }}
        QTabBar::tab:hover {{
            color: {t['text_primary']};
        }}

        QSlider::groove:horizontal {{
            border: none;
            height: 4px;
            background-color: {t['border']};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background-color: {t['accent']};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {t['accent_hover']};
        }}

        QCheckBox {{
            spacing: {t['spacing_sm']};
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {t['border']};
            border-radius: {t['radius_sm']};
            background-color: {t['bg_input']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {t['accent']};
            border-color: {t['accent']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {t['accent']};
        }}

        QListWidget {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            padding: {t['spacing_sm']};
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
        }}
        QListWidget::item {{
            padding: {t['spacing_sm']} {t['spacing_md']};
            border-radius: {t['radius_sm']};
            margin-bottom: 2px;
        }}
        QListWidget::item:selected {{
            background-color: {t['bg_tertiary']};
            color: {t['text_primary']};
        }}
        QListWidget::item:hover {{
            background-color: {t['bg_hover']};
        }}

        QScrollBar:vertical {{
            background-color: transparent;
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {t['border']};
            min-height: 30px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {t['text_muted']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}

        QProgressBar {{
            background-color: {t['bg_input']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            text-align: center;
            color: {t['text_primary']};
            font-size: {t['font_size_sm']};
        }}
        QProgressBar::chunk {{
            background-color: {t['accent']};
            border-radius: {t['radius_md']};
        }}

        QLabel {{
            color: {t['text_primary']};
            font-size: {t['font_size_md']};
        }}

        QFrame[frameShape="4"] {{
            background-color: {t['border']};
            max-height: 1px;
        }}

        QToolTip {{
            background-color: {t['bg_tertiary']};
            color: {t['text_primary']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_sm']};
            padding: {t['spacing_sm']};
            font-size: {t['font_size_sm']};
        }}

        QMenuBar {{
            background-color: {t['bg_primary']};
            color: {t['text_primary']};
            border-bottom: 1px solid {t['border']};
        }}
        QMenuBar::item:selected {{
            background-color: {t['bg_hover']};
            border-radius: {t['radius_sm']};
        }}
        QMenu {{
            background-color: {t['bg_tertiary']};
            color: {t['text_primary']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_md']};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 24px;
            border-radius: {t['radius_sm']};
        }}
        QMenu::item:selected {{
            background-color: {t['bg_hover']};
        }}

        QStatusBar {{
            background-color: {t['bg_secondary']};
            color: {t['text_muted']};
            border-top: 1px solid {t['border']};
        }}

        /* 通用分割线 */
        #divider {{
            background-color: {t['border']};
            max-height: 1px;
        }}

        /* Badge 徽章 */
        #badge_success {{
            background-color: {t['accent_light']};
            color: {t['accent']};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: {t['font_size_xs']};
            font-weight: {t['font_weight_bold']};
        }}
        #badge_warning {{
            background-color: #3d2e00;
            color: {t['warning']};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: {t['font_size_xs']};
            font-weight: {t['font_weight_bold']};
        }}
        #badge_danger {{
            background-color: #3d0a0a;
            color: {t['danger']};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: {t['font_size_xs']};
            font-weight: {t['font_weight_bold']};
        }}
        #badge_info {{
            background-color: #0a2a3d;
            color: {t['info']};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: {t['font_size_xs']};
            font-weight: {t['font_weight_bold']};
        }}
        #badge_default {{
            background-color: {t['bg_tertiary']};
            color: {t['text_secondary']};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: {t['font_size_xs']};
            font-weight: {t['font_weight_bold']};
        }}

        /* Toast 提示框 */
        #toast_success {{
            background-color: {t['accent_light']};
            color: {t['accent']};
            padding: 8px 16px;
            border-radius: {t['radius_md']};
            font-size: {t['font_size_sm']};
            font-weight: {t['font_weight_bold']};
        }}
        #toast_warning {{
            background-color: #3d2e00;
            color: {t['warning']};
            padding: 8px 16px;
            border-radius: {t['radius_md']};
            font-size: {t['font_size_sm']};
            font-weight: {t['font_weight_bold']};
        }}
        #toast_error {{
            background-color: #3d0a0a;
            color: {t['danger']};
            padding: 8px 16px;
            border-radius: {t['radius_md']};
            font-size: {t['font_size_sm']};
            font-weight: {t['font_weight_bold']};
        }}
        #toast_info {{
            background-color: #0a2a3d;
            color: {t['info']};
            padding: 8px 16px;
            border-radius: {t['radius_md']};
            font-size: {t['font_size_sm']};
            font-weight: {t['font_weight_bold']};
        }}

        /* 首页功能卡片 */
        #feature_card {{
            background-color: {t['bg_card']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_lg']};
            padding: {t['spacing_lg']};
        }}
        #feature_card:hover {{
            border-color: {t['accent']};
        }}

        /* 快速开始引导区 */
        #quick_start {{
            background-color: {t['bg_secondary']};
            border: 1px solid {t['border']};
            border-radius: {t['radius_lg']};
            padding: {t['spacing_lg']};
        }}
        """
