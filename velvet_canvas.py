import sys
import json
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QPointF, QSizeF
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QPainter,
    QPen,
    QBrush,
    QPixmap,
    QImage,
    QPdfWriter,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsRectItem,
    QVBoxLayout,
    QToolBar,
    QDockWidget,
    QPushButton,
    QLabel,
    QColorDialog,
    QFileDialog,
    QFontComboBox,
    QSpinBox,
    QTextEdit,
    QMessageBox,
    QInputDialog,
    QCheckBox,
)


# ============================================================
# APPLICATION CONSTANTS
# ============================================================

APP_NAME = "VelvetCanvas"

CANVAS_WIDTH = 850
CANVAS_HEIGHT = 1100

HANDLE_SIZE = 12

MIN_WIDTH = 40
MIN_HEIGHT = 30


# ============================================================
# RESIZE HANDLE
# ============================================================

class ResizeHandle(QGraphicsRectItem):

    def __init__(self, owner, corner):

        super().__init__(owner)

        self.owner = owner
        self.corner = corner

        self.setRect(
            -HANDLE_SIZE / 2,
            -HANDLE_SIZE / 2,
            HANDLE_SIZE,
            HANDLE_SIZE,
        )

        self.setBrush(
            QBrush(QColor("white"))
        )

        self.setPen(
            QPen(
                QColor("#d63384"),
                2,
            )
        )

        self.setZValue(100000)

        self.setFlag(
            QGraphicsItem.ItemIsMovable,
            False,
        )

        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton
        )

        if corner in (
            "top_left",
            "bottom_right",
        ):
            cursor = Qt.CursorShape.SizeFDiagCursor
        else:
            cursor = Qt.CursorShape.SizeBDiagCursor

        self.setCursor(cursor)

    def mousePressEvent(self, event):

        self.owner.begin_resize(
            self.corner,
            event.scenePos(),
        )

        event.accept()

    def mouseMoveEvent(self, event):

        self.owner.perform_resize(
            self.corner,
            event.scenePos(),
        )

        event.accept()

    def mouseReleaseEvent(self, event):

        self.owner.end_resize()

        event.accept()


# ============================================================
# BASE CANVAS ITEM
# ============================================================

class CanvasItem(QGraphicsItem):

    def __init__(self):

        super().__init__()

        self.item_width = 200.0
        self.item_height = 100.0

        self.resize_start_width = 0.0
        self.resize_start_height = 0.0

        self.resize_start_position = QPointF()
        self.resize_start_scene_position = QPointF()

        self.handles = {}

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

        self.setCursor(
            Qt.CursorShape.OpenHandCursor
        )

    # --------------------------------------------------------

    def create_resize_handles(self):

        if self.handles:
            return

        for corner in (
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
        ):

            self.handles[corner] = ResizeHandle(
                self,
                corner,
            )

        self.update_handles()

    # --------------------------------------------------------

    def update_handles(self):

        if not self.handles:
            return

        rect = self.boundingRect()

        positions = {
            "top_left": rect.topLeft(),
            "top_right": rect.topRight(),
            "bottom_left": rect.bottomLeft(),
            "bottom_right": rect.bottomRight(),
        }

        for corner, handle in self.handles.items():

            handle.setPos(
                positions[corner]
            )

            handle.setVisible(
                self.isSelected()
            )

    # --------------------------------------------------------

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemSelectedHasChanged:

            for handle in self.handles.values():

                handle.setVisible(
                    bool(value)
                )

        return super().itemChange(
            change,
            value,
        )

    # --------------------------------------------------------

    def begin_resize(
        self,
        corner,
        scene_position,
    ):

        self.resize_start_width = (
            self.item_width
        )

        self.resize_start_height = (
            self.item_height
        )

        self.resize_start_position = (
            QPointF(self.pos())
        )

        self.resize_start_scene_position = (
            QPointF(scene_position)
        )

    # --------------------------------------------------------

    def set_size(
        self,
        width,
        height,
    ):

        width = max(
            MIN_WIDTH,
            float(width),
        )

        height = max(
            MIN_HEIGHT,
            float(height),
        )

        self.prepareGeometryChange()

        self.item_width = width
        self.item_height = height

        self.update_handles()
        self.update()

    # --------------------------------------------------------

    def perform_resize(
        self,
        corner,
        scene_position,
    ):
        raise NotImplementedError

    # --------------------------------------------------------

    def end_resize(self):

        self.update_handles()

    # --------------------------------------------------------

    def draw_selection(
        self,
        painter,
    ):

        if not self.isSelected():
            return

        painter.save()

        painter.setPen(
            QPen(
                QColor("#d63384"),
                2,
                Qt.PenStyle.DashLine,
            )
        )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.drawRect(
            self.boundingRect()
        )

        painter.restore()


# ============================================================
# TEXT ITEM
# ============================================================

class TextCanvasItem(CanvasItem):

    def __init__(
        self,
        text="Your beautiful message ❤️",
        width=320,
        height=120,
    ):

        super().__init__()

        # Geometry FIRST
        self.item_width = float(width)
        self.item_height = float(height)

        # Content
        self.text = text

        self.font = QFont(
            "Arial",
            28,
        )

        self.text_color = QColor(
            "#222222"
        )

        # Handles LAST
        self.create_resize_handles()

    # --------------------------------------------------------

    def boundingRect(self):

        return QRectF(
            0,
            0,
            self.item_width,
            self.item_height,
        )

    # --------------------------------------------------------

    def paint(
        self,
        painter,
        option,
        widget=None,
    ):

        painter.save()

        painter.setFont(
            self.font
        )

        painter.setPen(
            QPen(
                self.text_color
            )
        )

        text_rect = QRectF(
            8,
            8,
            max(1, self.item_width - 16),
            max(1, self.item_height - 16),
        )

        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
            | Qt.TextFlag.TextWordWrap,
            self.text,
        )

        painter.restore()

        self.draw_selection(
            painter
        )

    # --------------------------------------------------------

    def perform_resize(
        self,
        corner,
        scene_position,
    ):

        delta = (
            scene_position
            - self.resize_start_scene_position
        )

        width = self.resize_start_width
        height = self.resize_start_height

        x = self.resize_start_position.x()
        y = self.resize_start_position.y()

        if corner == "bottom_right":

            width += delta.x()
            height += delta.y()

        elif corner == "bottom_left":

            width -= delta.x()
            height += delta.y()

            x += delta.x()

        elif corner == "top_right":

            width += delta.x()
            height -= delta.y()

            y += delta.y()

        elif corner == "top_left":

            width -= delta.x()
            height -= delta.y()

            x += delta.x()
            y += delta.y()

        width = max(
            MIN_WIDTH,
            width,
        )

        height = max(
            MIN_HEIGHT,
            height,
        )

        self.prepareGeometryChange()

        self.item_width = width
        self.item_height = height

        self.setPos(
            x,
            y,
        )

        self.update_handles()
        self.update()

    # --------------------------------------------------------

    def mouseDoubleClickEvent(
        self,
        event,
    ):

        text, ok = (
            QInputDialog.getMultiLineText(
                None,
                "Edit Text",
                "Text:",
                self.text,
            )
        )

        if ok:

            self.text = text
            self.update()

        event.accept()


# ============================================================
# IMAGE ITEM
# ============================================================

class ImageCanvasItem(CanvasItem):

    def __init__(
        self,
        image_path,
    ):

        super().__init__()

        self.image_path = str(
            image_path
        )

        self.pixmap = QPixmap(
            self.image_path
        )

        if self.pixmap.isNull():

            self.pixmap = QPixmap(
                400,
                300,
            )

            self.pixmap.fill(
                QColor("#cccccc")
            )

        original_width = float(
            self.pixmap.width()
        )

        original_height = float(
            self.pixmap.height()
        )

        self.aspect_ratio = (
            original_width
            / original_height
            if original_height
            else 1.0
        )

        # Reasonable initial size

        if original_width > 500:

            scale = (
                500
                / original_width
            )

            original_width *= scale
            original_height *= scale

        self.item_width = original_width
        self.item_height = original_height

        # Handles LAST
        self.create_resize_handles()

    # --------------------------------------------------------

    def boundingRect(self):

        return QRectF(
            0,
            0,
            self.item_width,
            self.item_height,
        )

    # --------------------------------------------------------

    def paint(
        self,
        painter,
        option,
        widget=None,
    ):

        painter.save()

        painter.drawPixmap(
            self.boundingRect(),
            self.pixmap,
            QRectF(
                self.pixmap.rect()
            ),
        )

        painter.restore()

        self.draw_selection(
            painter
        )

    # --------------------------------------------------------

    def perform_resize(
        self,
        corner,
        scene_position,
    ):

        delta = (
            scene_position
            - self.resize_start_scene_position
        )

        width = self.resize_start_width
        height = self.resize_start_height

        x = self.resize_start_position.x()
        y = self.resize_start_position.y()

        if corner == "bottom_right":

            width += delta.x()
            height += delta.y()

        elif corner == "bottom_left":

            width -= delta.x()
            height += delta.y()

            x += delta.x()

        elif corner == "top_right":

            width += delta.x()
            height -= delta.y()

            y += delta.y()

        elif corner == "top_left":

            width -= delta.x()
            height -= delta.y()

            x += delta.x()
            y += delta.y()

        width = max(
            MIN_WIDTH,
            width,
        )

        height = max(
            MIN_HEIGHT,
            height,
        )

        # Default behaviour:
        # preserve image aspect ratio.
        #
        # Hold Shift for free resizing.

        if not (
            QApplication.keyboardModifiers()
            & Qt.KeyboardModifier.ShiftModifier
        ):

            height = (
                width
                / self.aspect_ratio
            )

        self.prepareGeometryChange()

        self.item_width = width
        self.item_height = height

        self.setPos(
            x,
            y,
        )

        self.update_handles()
        self.update()


# ============================================================
# CANVAS SCENE
# ============================================================

class CanvasScene(QGraphicsScene):

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)

        self.grid_enabled = False
        self.grid_size = 25

        self.setSceneRect(
            0,
            0,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
        )

        self.background_color = QColor(
            "white"
        )

    # --------------------------------------------------------

    def drawBackground(
        self,
        painter,
        rect,
    ):

        painter.fillRect(
            self.sceneRect(),
            self.background_color,
        )

        if self.grid_enabled:

            painter.save()

            painter.setPen(
                QPen(
                    QColor("#eeeeee"),
                    1,
                )
            )

            scene_rect = self.sceneRect()

            x = scene_rect.left()

            while x <= scene_rect.right():

                painter.drawLine(
                    x,
                    scene_rect.top(),
                    x,
                    scene_rect.bottom(),
                )

                x += self.grid_size

            y = scene_rect.top()

            while y <= scene_rect.bottom():

                painter.drawLine(
                    scene_rect.left(),
                    y,
                    scene_rect.right(),
                    y,
                )

                y += self.grid_size

            painter.restore()

        painter.save()

        painter.setPen(
            QPen(
                QColor("#aaaaaa"),
                2,
            )
        )

        painter.drawRect(
            self.sceneRect()
        )

        painter.restore()


# ============================================================
# CANVAS VIEW
# ============================================================

class CanvasView(QGraphicsView):

    def __init__(
        self,
        scene,
    ):

        super().__init__(scene)

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.TextAntialiasing
        )

        self.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag
        )

        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )

        self.setBackgroundBrush(
            QColor("#e6e6e6")
        )

    # --------------------------------------------------------

    def wheelEvent(
        self,
        event,
    ):

        if (
            event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):

            factor = 1.15

            if event.angleDelta().y() < 0:

                factor = 1 / factor

            self.scale(
                factor,
                factor,
            )

            event.accept()

            return

        super().wheelEvent(
            event
        )


# ============================================================
# MAIN APPLICATION
# ============================================================

class VelvetCanvas(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            f"❤️ {APP_NAME}"
        )

        self.resize(
            1500,
            950,
        )

        self.scene = CanvasScene()

        self.view = CanvasView(
            self.scene
        )

        self.setCentralWidget(
            self.view
        )

        self.create_toolbar()
        self.create_properties_panel()
        self.create_menus()

        self.scene.selectionChanged.connect(
            self.selection_changed
        )

        self.fit_canvas()

        self.statusBar().showMessage(
            "Ready"
        )

    # ========================================================
    # TOOLBAR
    # ========================================================

    def create_toolbar(self):

        toolbar = QToolBar(
            "Tools"
        )

        toolbar.setMovable(
            False
        )

        self.addToolBar(
            toolbar
        )

        toolbar.addAction(
            "✏ Add Text",
            self.add_text,
        )

        toolbar.addAction(
            "🖼 Add Image",
            self.add_image,
        )

        toolbar.addAction(
            "❤️ Heart",
            lambda: self.add_text_item(
                "❤️",
                64,
            ),
        )

        toolbar.addAction(
            "💕 Love",
            lambda: self.add_text_item(
                "I Love You ❤️",
                32,
            ),
        )

        toolbar.addSeparator()

        toolbar.addAction(
            "Duplicate",
            self.duplicate_selected,
        )

        toolbar.addAction(
            "Delete",
            self.delete_selected,
        )

        toolbar.addSeparator()

        toolbar.addAction(
            "↑ Forward",
            self.bring_forward,
        )

        toolbar.addAction(
            "↓ Back",
            self.send_backward,
        )

        toolbar.addSeparator()

        toolbar.addAction(
            "↺ Fit",
            self.fit_canvas,
        )

        toolbar.addSeparator()

        toolbar.addAction(
            "Save",
            self.save_project,
        )

        toolbar.addAction(
            "Open",
            self.open_project,
        )

        toolbar.addAction(
            "PNG",
            self.export_png,
        )

        toolbar.addAction(
            "PDF",
            self.export_pdf,
        )

    # ========================================================
    # PROPERTIES PANEL
    # ========================================================

    def create_properties_panel(self):

        dock = QDockWidget(
            "Properties",
            self,
        )

        dock.setMinimumWidth(
            280
        )

        panel = QWidget()

        layout = QVBoxLayout(
            panel
        )

        layout.addWidget(
            QLabel(
                "<b>Text Content</b>"
            )
        )

        self.text_editor = QTextEdit()

        self.text_editor.setFixedHeight(
            120
        )

        self.text_editor.textChanged.connect(
            self.update_selected_text
        )

        layout.addWidget(
            self.text_editor
        )

        layout.addWidget(
            QLabel(
                "Font"
            )
        )

        self.font_combo = QFontComboBox()

        self.font_combo.currentFontChanged.connect(
            self.change_font
        )

        layout.addWidget(
            self.font_combo
        )

        layout.addWidget(
            QLabel(
                "Font Size"
            )
        )

        self.font_size = QSpinBox()

        self.font_size.setRange(
            6,
            300,
        )

        self.font_size.setValue(
            28
        )

        self.font_size.valueChanged.connect(
            self.change_font_size
        )

        layout.addWidget(
            self.font_size
        )

        self.bold_button = QCheckBox(
            "Bold"
        )

        self.bold_button.toggled.connect(
            self.change_bold
        )

        layout.addWidget(
            self.bold_button
        )

        self.italic_button = QCheckBox(
            "Italic"
        )

        self.italic_button.toggled.connect(
            self.change_italic
        )

        layout.addWidget(
            self.italic_button
        )

        color_button = QPushButton(
            "🎨 Text Colour"
        )

        color_button.clicked.connect(
            self.change_text_color
        )

        layout.addWidget(
            color_button
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            QLabel(
                "<b>Rotation</b>"
            )
        )

        self.rotation_spin = QSpinBox()

        self.rotation_spin.setRange(
            -360,
            360,
        )

        self.rotation_spin.valueChanged.connect(
            self.change_rotation
        )

        layout.addWidget(
            self.rotation_spin
        )

        layout.addSpacing(
            15
        )

        background_button = QPushButton(
            "🖼 Canvas Background"
        )

        background_button.clicked.connect(
            self.change_background
        )

        layout.addWidget(
            background_button
        )

        self.grid_check = QCheckBox(
            "Show Grid"
        )

        self.grid_check.toggled.connect(
            self.toggle_grid
        )

        layout.addWidget(
            self.grid_check
        )

        layout.addStretch()

        dock.setWidget(
            panel
        )

        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            dock,
        )

    # ========================================================
    # MENU
    # ========================================================

    def create_menus(self):

        file_menu = self.menuBar().addMenu(
            "&File"
        )

        file_menu.addAction(
            "New",
            self.new_project,
        )

        file_menu.addSeparator()

        file_menu.addAction(
            "Open Project",
            self.open_project,
        )

        file_menu.addAction(
            "Save Project",
            self.save_project,
        )

        file_menu.addSeparator()

        file_menu.addAction(
            "Export PNG",
            self.export_png,
        )

        file_menu.addAction(
            "Export PDF",
            self.export_pdf,
        )

        file_menu.addSeparator()

        file_menu.addAction(
            "Exit",
            self.close,
        )

    # ========================================================
    # ADD ITEMS
    # ========================================================

    def add_text(self):

        self.add_text_item(
            "Your beautiful message ❤️",
            28,
        )

    # --------------------------------------------------------

    def add_text_item(
        self,
        text,
        size=28,
    ):

        item = TextCanvasItem(
            text=text
        )

        item.font.setPointSize(
            size
        )

        item.setPos(
            150,
            150,
        )

        self.scene.addItem(
            item
        )

        self.select_item(
            item
        )

    # --------------------------------------------------------

    def add_image(self):

        filename, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Select Image",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
            )
        )

        if not filename:
            return

        item = ImageCanvasItem(
            filename
        )

        item.setPos(
            150,
            150,
        )

        self.scene.addItem(
            item
        )

        self.select_item(
            item
        )

    # ========================================================
    # SELECTION
    # ========================================================

    def select_item(
        self,
        item,
    ):

        self.scene.clearSelection()

        item.setSelected(
            True
        )

    # --------------------------------------------------------

    def selected_item(self):

        items = (
            self.scene.selectedItems()
        )

        if not items:
            return None

        for item in items:

            if isinstance(
                item,
                CanvasItem,
            ):
                return item

        return None

    # --------------------------------------------------------

    def selected_text_item(self):

        item = self.selected_item()

        if isinstance(
            item,
            TextCanvasItem,
        ):
            return item

        return None

    # --------------------------------------------------------

    def selection_changed(self):

        item = self.selected_item()

        self.text_editor.blockSignals(
            True
        )

        self.font_combo.blockSignals(
            True
        )

        self.font_size.blockSignals(
            True
        )

        self.bold_button.blockSignals(
            True
        )

        self.italic_button.blockSignals(
            True
        )

        self.rotation_spin.blockSignals(
            True
        )

        if isinstance(
            item,
            TextCanvasItem,
        ):

            self.text_editor.setPlainText(
                item.text
            )

            self.font_combo.setCurrentFont(
                item.font
            )

            self.font_size.setValue(
                item.font.pointSize()
            )

            self.bold_button.setChecked(
                item.font.bold()
            )

            self.italic_button.setChecked(
                item.font.italic()
            )

        else:

            self.text_editor.clear()

        if item:

            self.rotation_spin.setValue(
                int(item.rotation())
            )

        else:

            self.rotation_spin.setValue(
                0
            )

        self.text_editor.blockSignals(
            False
        )

        self.font_combo.blockSignals(
            False
        )

        self.font_size.blockSignals(
            False
        )

        self.bold_button.blockSignals(
            False
        )

        self.italic_button.blockSignals(
            False
        )

        self.rotation_spin.blockSignals(
            False
        )

    # ========================================================
    # TEXT PROPERTIES
    # ========================================================

    def update_selected_text(self):

        item = self.selected_text_item()

        if not item:
            return

        item.text = (
            self.text_editor.toPlainText()
        )

        item.update()

    # --------------------------------------------------------

    def change_font(
        self,
        font,
    ):

        item = self.selected_text_item()

        if not item:
            return

        size = item.font.pointSize()

        item.font = QFont(
            font
        )

        item.font.setPointSize(
            size
        )

        item.update()

    # --------------------------------------------------------

    def change_font_size(
        self,
        size,
    ):

        item = self.selected_text_item()

        if not item:
            return

        item.font.setPointSize(
            size
        )

        item.update()

    # --------------------------------------------------------

    def change_bold(
        self,
        enabled,
    ):

        item = self.selected_text_item()

        if not item:
            return

        item.font.setBold(
            enabled
        )

        item.update()

    # --------------------------------------------------------

    def change_italic(
        self,
        enabled,
    ):

        item = self.selected_text_item()

        if not item:
            return

        item.font.setItalic(
            enabled
        )

        item.update()

    # --------------------------------------------------------

    def change_text_color(self):

        item = self.selected_text_item()

        if not item:

            QMessageBox.information(
                self,
                "Select Text",
                "Select a text item first.",
            )

            return

        color = QColorDialog.getColor(
            item.text_color,
            self,
            "Text Colour",
        )

        if color.isValid():

            item.text_color = color

            item.update()

    # ========================================================
    # ROTATION
    # ========================================================

    def change_rotation(
        self,
        value,
    ):

        item = self.selected_item()

        if not item:
            return

        item.setTransformOriginPoint(
            item.boundingRect().center()
        )

        item.setRotation(
            value
        )

    # ========================================================
    # CANVAS
    # ========================================================

    def change_background(self):

        color = QColorDialog.getColor(
            self.scene.background_color,
            self,
            "Canvas Background",
        )

        if color.isValid():

            self.scene.background_color = (
                color
            )

            self.scene.update()

    # --------------------------------------------------------

    def toggle_grid(
        self,
        enabled,
    ):

        self.scene.grid_enabled = enabled

        self.scene.update()

    # --------------------------------------------------------

    def fit_canvas(self):

        self.view.resetTransform()

        self.view.fitInView(
            self.scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    # ========================================================
    # ITEM ACTIONS
    # ========================================================

    def delete_selected(self):

        for item in list(
            self.scene.selectedItems()
        ):

            if isinstance(
                item,
                CanvasItem,
            ):

                self.scene.removeItem(
                    item
                )

    # --------------------------------------------------------

    def duplicate_selected(self):

        item = self.selected_item()

        if not item:
            return

        if isinstance(
            item,
            TextCanvasItem,
        ):

            duplicate = TextCanvasItem(
                text=item.text,
                width=item.item_width,
                height=item.item_height,
            )

            duplicate.font = QFont(
                item.font
            )

            duplicate.text_color = QColor(
                item.text_color
            )

        elif isinstance(
            item,
            ImageCanvasItem,
        ):

            duplicate = ImageCanvasItem(
                item.image_path
            )

            duplicate.item_width = (
                item.item_width
            )

            duplicate.item_height = (
                item.item_height
            )

        else:
            return

        duplicate.setPos(
            item.pos()
            + QPointF(
                25,
                25,
            )
        )

        duplicate.setRotation(
            item.rotation()
        )

        duplicate.setZValue(
            item.zValue() + 1
        )

        self.scene.addItem(
            duplicate
        )

        self.select_item(
            duplicate
        )

    # --------------------------------------------------------

    def bring_forward(self):

        item = self.selected_item()

        if item:

            item.setZValue(
                item.zValue() + 1
            )

    # --------------------------------------------------------

    def send_backward(self):

        item = self.selected_item()

        if item:

            item.setZValue(
                item.zValue() - 1
            )

    # ========================================================
    # NEW PROJECT
    # ========================================================

    def clear_canvas(self):

        for item in list(
            self.scene.items()
        ):

            if isinstance(
                item,
                CanvasItem,
            ):

                self.scene.removeItem(
                    item
                )

    # --------------------------------------------------------

    def new_project(self):

        answer = QMessageBox.question(
            self,
            "New Project",
            "Clear the current canvas?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if (
            answer
            == QMessageBox.StandardButton.Yes
        ):

            self.clear_canvas()

            self.scene.background_color = QColor(
                "white"
            )

            self.scene.update()

    # ========================================================
    # SAVE PROJECT
    # ========================================================

    def save_project(self):

        filename, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Save Project",
                "velvet_project.json",
                "VelvetCanvas Project (*.json)",
            )
        )

        if not filename:
            return

        items = []

        for item in self.scene.items():

            if isinstance(
                item,
                TextCanvasItem,
            ):

                items.append(
                    {
                        "type": "text",
                        "text": item.text,
                        "x": item.pos().x(),
                        "y": item.pos().y(),
                        "width": item.item_width,
                        "height": item.item_height,
                        "font": item.font.family(),
                        "size": item.font.pointSize(),
                        "bold": item.font.bold(),
                        "italic": item.font.italic(),
                        "color": item.text_color.name(),
                        "rotation": item.rotation(),
                        "z": item.zValue(),
                    }
                )

            elif isinstance(
                item,
                ImageCanvasItem,
            ):

                items.append(
                    {
                        "type": "image",
                        "path": item.image_path,
                        "x": item.pos().x(),
                        "y": item.pos().y(),
                        "width": item.item_width,
                        "height": item.item_height,
                        "rotation": item.rotation(),
                        "z": item.zValue(),
                    }
                )

        data = {
            "version": 1,
            "canvas": {
                "width": CANVAS_WIDTH,
                "height": CANVAS_HEIGHT,
                "background": (
                    self.scene.background_color.name()
                ),
            },
            "items": items,
        }

        try:

            Path(filename).write_text(
                json.dumps(
                    data,
                    indent=4,
                ),
                encoding="utf-8",
            )

            self.statusBar().showMessage(
                "Project saved"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Save Error",
                str(error),
            )

    # ========================================================
    # OPEN PROJECT
    # ========================================================

    def open_project(self):

        filename, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Open Project",
                "",
                "VelvetCanvas Project (*.json)",
            )
        )

        if not filename:
            return

        try:

            data = json.loads(
                Path(filename).read_text(
                    encoding="utf-8"
                )
            )

            self.clear_canvas()

            canvas_data = data.get(
                "canvas",
                {}
            )

            self.scene.background_color = QColor(
                canvas_data.get(
                    "background",
                    "#ffffff",
                )
            )

            for data_item in data.get(
                "items",
                [],
            ):

                item_type = data_item.get(
                    "type"
                )

                if item_type == "text":

                    item = TextCanvasItem(
                        text=data_item.get(
                            "text",
                            "",
                        ),
                        width=data_item.get(
                            "width",
                            320,
                        ),
                        height=data_item.get(
                            "height",
                            120,
                        ),
                    )

                    item.font = QFont(
                        data_item.get(
                            "font",
                            "Arial",
                        ),
                        data_item.get(
                            "size",
                            28,
                        ),
                    )

                    item.font.setBold(
                        data_item.get(
                            "bold",
                            False,
                        )
                    )

                    item.font.setItalic(
                        data_item.get(
                            "italic",
                            False,
                        )
                    )

                    item.text_color = QColor(
                        data_item.get(
                            "color",
                            "#222222",
                        )
                    )

                elif item_type == "image":

                    path = data_item.get(
                        "path"
                    )

                    if not path:
                        continue

                    if not Path(
                        path
                    ).exists():

                        continue

                    item = ImageCanvasItem(
                        path
                    )

                    item.item_width = (
                        data_item.get(
                            "width",
                            item.item_width,
                        )
                    )

                    item.item_height = (
                        data_item.get(
                            "height",
                            item.item_height,
                        )
                    )

                    item.update_handles()

                else:

                    continue

                item.setPos(
                    data_item.get(
                        "x",
                        100,
                    ),
                    data_item.get(
                        "y",
                        100,
                    ),
                )

                item.setRotation(
                    data_item.get(
                        "rotation",
                        0,
                    )
                )

                item.setTransformOriginPoint(
                    item.boundingRect().center()
                )

                item.setZValue(
                    data_item.get(
                        "z",
                        0,
                    )
                )

                self.scene.addItem(
                    item
                )

                item.update_handles()

            self.scene.update()

            self.statusBar().showMessage(
                "Project loaded"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Open Error",
                str(error),
            )

    # ========================================================
    # EXPORT PNG
    # ========================================================

    def render_scene_to_image(self):

        rect = self.scene.sceneRect()

        image = QImage(
            int(rect.width()),
            int(rect.height()),
            QImage.Format.Format_ARGB32,
        )

        image.fill(
            self.scene.background_color
        )

        # Hide selection handles temporarily.

        handles = []

        for item in self.scene.items():

            if isinstance(
                item,
                CanvasItem,
            ):

                for handle in (
                    item.handles.values()
                ):

                    if handle.isVisible():

                        handles.append(
                            handle
                        )

                        handle.setVisible(
                            False
                        )

        painter = QPainter(
            image
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        self.scene.render(
            painter,
            QRectF(
                image.rect()
            ),
            rect,
        )

        painter.end()

        for handle in handles:

            handle.setVisible(
                True
            )

        return image

    # --------------------------------------------------------

    def export_png(self):

        filename, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Export PNG",
                "velvet_canvas.png",
                "PNG Image (*.png)",
            )
        )

        if not filename:
            return

        image = (
            self.render_scene_to_image()
        )

        if image.save(
            filename
        ):

            self.statusBar().showMessage(
                "PNG exported successfully"
            )

        else:

            QMessageBox.warning(
                self,
                "Export Error",
                "Could not save PNG.",
            )

    # ========================================================
    # EXPORT PDF
    # ========================================================

    def export_pdf(self):

        filename, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Export PDF",
                "velvet_canvas.pdf",
                "PDF File (*.pdf)",
            )
        )

        if not filename:
            return

        try:

            image = (
                self.render_scene_to_image()
            )

            writer = QPdfWriter(
                filename
            )

            writer.setResolution(
                150
            )

            painter = QPainter(
                writer
            )

            page_rect = (
                writer.pageLayout()
                .paintRectPixels(
                    writer.resolution()
                )
            )

            scaled = image.scaled(
                page_rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            x = (
                page_rect.width()
                - scaled.width()
            ) // 2

            y = (
                page_rect.height()
                - scaled.height()
            ) // 2

            painter.drawImage(
                x,
                y,
                scaled,
            )

            painter.end()

            self.statusBar().showMessage(
                "PDF exported successfully"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "PDF Error",
                str(error),
            )

    # ========================================================
    # KEYBOARD
    # ========================================================

    def keyPressEvent(
        self,
        event,
    ):

        if event.key() == Qt.Key.Key_Delete:

            self.delete_selected()

            event.accept()

            return

        if (
            event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):

            if event.key() == Qt.Key.Key_D:

                self.duplicate_selected()

                event.accept()

                return

        super().keyPressEvent(
            event
        )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        APP_NAME
    )

    window = VelvetCanvas()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()