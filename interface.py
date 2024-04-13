from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QTreeView,
    QGraphicsItem, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsView, QGraphicsScene,
    QGraphicsLineItem)
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QBrush, QColor, QPen, QWheelEvent, QPainter, QMouseEvent)
import sys, json
from explain import explain_query, extract_nodes

class GraphNode(QGraphicsItem):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label = label
        self.setFlag(QGraphicsItem.ItemIsMovable)
        
        # Add a text item as a child of this item
        self.text_item = QGraphicsTextItem(label, self)
        rect = self.text_item.boundingRect()
        
        # Optionally add an ellipse or rectangle around the text
        self.background_item = QGraphicsEllipseItem(-rect.width()/2, -rect.height()/2, rect.width(), rect.height(), self)
        self.background_item.setBrush(QBrush(QColor(255, 255, 255)))
        self.background_item.setPen(QPen(QColor(255, 255, 255)))

    def boundingRect(self):
        return self.background_item.boundingRect()

    def paint(self, painter, option, widget=None):
        # The painting is handled by the child items
        pass

class GraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        # self.setBackgroundBrush(QBrush(Qt.black))

    def wheelEvent(self, event: QWheelEvent):
        factor = 1.1  # This is the zoom factor
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)
        super().mouseReleaseEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("QEP Cost Estimator")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)  # For smoother graphics
        # self.view.setBackgroundBrush(QBrush(Qt.black))  
        layout.addWidget(self.view)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your SQL query here...")
        layout.addWidget(self.query_input)

        self.btn_submit = QPushButton('Explain Cost')
        self.btn_submit.clicked.connect(self.onSubmit)
        layout.addWidget(self.btn_submit)

        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(['Node', 'Cost', 'Rows', 'Width'])
        self.tree_view.setModel(self.tree_model)
        layout.addWidget(self.tree_view)
        
        # self.result_display = QTextEdit()
        # self.result_display.setReadOnly(True)
        # layout.addWidget(self.result_display)

    def onSubmit(self):
        sql_query = self.query_input.toPlainText().strip()
        plan = explain_query(sql_query)
        self.showPlan(plan)
        # formatted_plan = format_plan(plan)
        # self.showPlan(formatted_plan)
        # explanation = explain_query(sql_query)
        # self.result_display.setPlainText(plan)

    def add_nodes_edges(self, node, parent_graphics_item=None, x=0, y=0, y_step=50, depth=0):
        # Define horizontal offset
        x_offset = 200 // (depth + 1)
        
        # Create the graphics item for this node
        node_graphics_item = GraphNode(node['Node Type'])
        node_graphics_item.setPos(x, y)
        self.scene.addItem(node_graphics_item)

        # If this is not the root node, draw an edge from the parent
        if parent_graphics_item is not None:
            line = QGraphicsLineItem(parent_graphics_item.x(), parent_graphics_item.y(), x, y)
            line.setPen(QPen(QColor(255, 255, 255)))
            self.scene.addItem(line)

        # Recursively add child nodes
        if 'Plans' in node:
            child_offset = -x_offset if depth % 2 == 0 else x_offset  # Alternate left and right placement
            for index, subplan in enumerate(node['Plans']):
                new_x = x + (index - 0.5) * 2 * child_offset  # Position children with offset
                self.add_nodes_edges(subplan, node_graphics_item, new_x, y + y_step, y_step, depth + 1)
        
        # # Create the graphics item for this node
        # node_graphics_item = GraphNode(node['Node Type'])
        # node_graphics_item.setPos(x, y)
        # self.scene.addItem(node_graphics_item)

        # # If this is not the root node, draw an edge from the parent
        # if parent_graphics_item is not None:
        #     line = QGraphicsLineItem(parent_graphics_item.x(), parent_graphics_item.y(), x, y)
        #     self.scene.addItem(line)

        # # Recursively add child nodes
        # if 'Plans' in node:
        #     for subplan in node['Plans']:
        #         self.add_nodes_edges(subplan, node_graphics_item, x + 100, y + y_step, y_step)

    def showPlan(self, plan):
        self.scene.clear()  # Clear the scene for a new plan

        plan_dict = json.loads(plan)  # Load plan from JSON string
        root_node = plan_dict[0]['Plan']
        self.add_nodes_edges(root_node)  # Pass the root node of the plan

        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)  # Fit the scene in the view
        
        # plan_dict = json.loads(plan)
        # # Clear the current model
        self.tree_model.removeRows(0, self.tree_model.rowCount())
        
        # Recursively load the plan nodes into the tree view
        self.load_nodes(plan_dict[0]['Plan'], self.tree_model.invisibleRootItem())

        # Expand all nodes in the view for visibility
        self.tree_view.expandAll()
        
    def load_nodes(self, node, parent_item):
        # Create an item with the node type
        node_item = QStandardItem(node['Node Type'])
        # Additional details can be added in a similar manner
        cost_item = QStandardItem(f"{node['Total Cost']}")
        rows_item = QStandardItem(f"{node['Plan Rows']}")
        width_item = QStandardItem(f"{node['Plan Width']}")
        
        parent_item.appendRow([node_item, cost_item, rows_item, width_item])
        
        # If this node has children (sub-plans), recursively add them
        if 'Plans' in node:
            for subplan in node['Plans']:
                self.load_nodes(subplan, node_item)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
