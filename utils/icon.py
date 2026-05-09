"""图标生成工具，程序化生成应用图标"""
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QRect


def create_app_icon(size=64):
    """程序化生成应用图标（蓝色圆形 + 白色i字母）

    Args:
        size: 图标尺寸（像素）

    Returns:
        QIcon 对象
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)

    margin = size * 0.05
    radius = (size - margin * 2) / 2

    gradient_center_x = size / 2
    gradient_center_y = size * 0.4
    from PyQt5.QtGui import QRadialGradient
    gradient = QRadialGradient(gradient_center_x, gradient_center_y, radius * 1.2)
    gradient.setColorAt(0, QColor("#42A5F5"))
    gradient.setColorAt(0.7, QColor("#1E88E5"))
    gradient.setColorAt(1, QColor("#1565C0"))

    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(int(margin), int(margin), int(size - margin * 2), int(size - margin * 2))

    font = QFont("Segoe UI", int(size * 0.5), QFont.Bold)
    font.setStyleStrategy(QFont.PreferAntialias)
    painter.setFont(font)

    painter.setPen(QColor("white"))

    text_rect = QRect(int(margin), int(margin), int(size - margin * 2), int(size - margin * 2))
    painter.drawText(text_rect, Qt.AlignCenter, "i")

    painter.end()

    return QIcon(pixmap)


def create_app_icon_multi():
    """生成多尺寸图标，适配不同场景

    Returns:
        QIcon 对象（包含16x16, 32x32, 48x48, 64x64, 128x128, 256x256）
    """
    icon = QIcon()
    for size in [16, 32, 48, 64, 128, 256]:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        margin = size * 0.05
        radius = (size - margin * 2) / 2

        from PyQt5.QtGui import QRadialGradient
        gradient = QRadialGradient(size / 2, size * 0.4, radius * 1.2)
        gradient.setColorAt(0, QColor("#42A5F5"))
        gradient.setColorAt(0.7, QColor("#1E88E5"))
        gradient.setColorAt(1, QColor("#1565C0"))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(margin), int(margin), int(size - margin * 2), int(size - margin * 2))

        font = QFont("Segoe UI", int(size * 0.5), QFont.Bold)
        font.setStyleStrategy(QFont.PreferAntialias)
        painter.setFont(font)

        painter.setPen(QColor("white"))
        text_rect = QRect(int(margin), int(margin), int(size - margin * 2), int(size - margin * 2))
        painter.drawText(text_rect, Qt.AlignCenter, "i")

        painter.end()

        icon.addPixmap(pixmap)

    return icon
