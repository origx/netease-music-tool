import os
import ssl

APP_TITLE = "NeteaseMusicTool"
WINDOW_SIZE = (1100, 1000)
WINDOW_MIN_SIZE = (1000, 900)

# 按本机已安装字体选择中文无衬线字体，运行时由主题模块解析。
FONT_FAMILIES = (
	"Microsoft YaHei UI",
	"Microsoft YaHei",
	"SimHei",
	"PingFang SC",
	"Noto Sans CJK SC",
)
FONT_FAMILY = "TkDefaultFont"

BG_DARK = "#1F1F1F"
BG_PANEL = "#282828"
BG_INPUT = "#333333"
BG_HOVER = "#2A2D2E"
BORDER = "#3C3C3C"
PRIMARY_BLUE = "#1f7adb"
PRIMARY_HOVER = "#2462a5"
TEXT_NORMAL = "#D4D4D4"
TEXT_WHITE = "#FFFFFF"
TEXT_HINT = "#888888"
TEXT_DISABLED = "#6A6A6A"
SELECT_BG = "#2462a5"
SELECT_FG = "#FFFFFF"
STRIPE_BG = "#2D2D2D"

DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
