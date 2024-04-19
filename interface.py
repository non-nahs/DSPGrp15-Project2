from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTreeView,
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsEllipseItem,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsLineItem,
    QMessageBox,
    QLabel,
    QLineEdit
)
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QBrush,
    QColor,
    QPen,
    QWheelEvent,
    QPainter,
    QMouseEvent
)
import sys, json
from explain import *

cost_params = {
    'seq_page_cost': 1.0,
    'random_page_cost': 4.0,
    'cpu_tuple_cost': 0.01,
    'cpu_operator_cost': 0.0025,
    'cpu_index_tuple_cost': 0.005,
    'cpu_hash_cost': 0.0025
}

class GraphNode(QGraphicsItem):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label = label
        self.setFlag(QGraphicsItem.ItemIsMovable)
        
        # Add a text item as a child of this item
        self.text_item = QGraphicsTextItem(label, self)
        self.text_item.setDefaultTextColor(QColor("black"))
        self.text_item.setZValue(1)
        rect = self.text_item.boundingRect()
        
        # Optionally add an ellipse or rectangle around the text
        self.background_item = QGraphicsEllipseItem(-(rect.width()+20)/2, -(rect.height()+20)/2, rect.width()+20, rect.height()+20, self)
        self.background_item.setBrush(QBrush(QColor('white')))
        self.background_item.setPen(QPen(QColor('white')))
        self.background_item.setZValue(0.8)

        self.text_item.setPos(-rect.width() / 2, -rect.height() /2)

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
        self.setGeometry(100, 100, 1200, 800) # setGeometry(x, y, w, h)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)  # For smoother graphics
        self.view.setBackgroundBrush(QBrush(Qt.black))  
        main_layout.addWidget(self.view)

        right_layout = QVBoxLayout()
        
        db_label = QLabel("DB:")
        self.db_input = QTextEdit()
        self.db_input.setFixedSize(500,30)
         # Create horizontal layout for label and text input
        db_layout = QHBoxLayout()
        db_layout.addWidget(db_label)
        db_layout.addWidget(self.db_input)
        
        self.user_input_label = QLabel("User:")
        self.user_input = QTextEdit()
        self.user_input.setFixedSize(500,30)
         # Create horizontal layout for label and text input
        user_input_layout = QHBoxLayout()
        user_input_layout.addWidget(self.user_input_label)
        user_input_layout.addWidget(self.user_input)
        
        self.pwd_label = QLabel("Password:")
        self.pwd_input = QLineEdit(self)
        self.pwd_input.setEchoMode(QLineEdit.Password) 
        # self.pwd_input = QTextEdit()
        self.pwd_input.setFixedSize(500,30)
         # Create horizontal layout for label and text input
        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(self.pwd_label)
        pwd_layout.addWidget(self.pwd_input)
        
        self.host_label = QLabel("Host:")
        self.host_input = QTextEdit()
        self.host_input.setFixedSize(500,30)
         # Create horizontal layout for label and text input
        host_layout = QHBoxLayout()
        host_layout.addWidget(self.host_label)
        host_layout.addWidget(self.host_input)
        
        port_label = QLabel("Port:")
        self.port_input = QTextEdit()
        self.port_input.setFixedSize(500,30)
         # Create horizontal layout for label and text input
        port_layout = QHBoxLayout()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        
        right_layout.addLayout(db_layout)
        right_layout.addLayout(user_input_layout)
        right_layout.addLayout(pwd_layout)
        right_layout.addLayout(host_layout)
        right_layout.addLayout(port_layout)
        
        self.btn_login = QPushButton('Login')
        self.btn_login.clicked.connect(self.onLogin)
        right_layout.addWidget(self.btn_login)
        
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your SQL query here...")
        right_layout.addWidget(self.query_input)

        self.btn_submit = QPushButton('Explain Cost')
        self.btn_submit.clicked.connect(self.onSubmit)
        right_layout.addWidget(self.btn_submit)

        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(['Node', 'Cost', 'Planned Rows', 'Actual Rows', 'Actual Total Time'])
        self.tree_view.setModel(self.tree_model)
        right_layout.addWidget(self.tree_view)

        self.explain_label = QTextEdit("Query Execution Plan:")
        self.explain_label.setReadOnly(True)
        right_layout.addWidget(self.explain_label)
        
        main_layout.addLayout(right_layout)
        # self.result_display = QTextEdit()
        # self.result_display.setReadOnly(True)
        # layout.addWidget(self.result_display)

    def onLogin(self):
        if self.user_input.toPlainText().strip() == "" or self.host_input.toPlainText().strip() == "" or self.db_input.toPlainText().strip() == "" or self.port_input.toPlainText().strip() == "" or self.pwd_input.text().strip() == "":
            QMessageBox.warning(self, "Warning", "Please fill all the login credentials")
            return
        
        user = self.user_input.toPlainText().strip()
        db = self.db_input.toPlainText().strip()
        host = self.host_input.toPlainText().strip()
        port = self.port_input.toPlainText().strip()
        pwd = self.pwd_input.text().strip()
        print(pwd)
        login_credentials(db,user,pwd,host,port)
        QMessageBox.information(self, "Success", "Login credentials saved!")
        
    def onSubmit(self):
        if self.user_input.toPlainText().strip() == "" or self.host_input.toPlainText().strip() == "" or self.db_input.toPlainText().strip() == "" or self.port_input.toPlainText().strip() == "" or self.pwd_input.text().strip() == "":
            QMessageBox.warning(self, "Warning", "Please fill all the login credentials first")
            return
        
        if self.query_input.toPlainText().strip() == "":
            self.explain_label.setPlainText("Please enter a query to explain.")
            self.explain_label.setStyleSheet("color: red;")
            return
        # costs_list = []

        sql_query = self.query_input.toPlainText().strip()
        plan = explain_query(sql_query)

        # print(plan)
        self.showPlan(plan)

        self.display_explanation(plan)
        # types = extract_node_types(json.loads(plan)[0]['Plan'])

        # for node_type in types:
        #     costs_list.append(get_cost_estimate(node_type))
        
        # 
        # formatted_plan = format_plan(plan)
        # self.showPlan(formatted_plan)
        # explanation = explain_query(sql_query)
        # self.result_display.setPlainText(plan)

    def display_explanation(self, plan):
        self.explain_label.clear()
        output_str = ""
        
        plan = json.loads(plan)
        root_plan = plan[0]["Plan"]
        nodes = parse_plan(root_plan)
        for node in nodes:
            expected_cost = compute_expected_cost(node, cost_params)
            print(f"Node: {node['Node Type']}")
            print(f"  Expected Cost: {expected_cost:.4f}")
            print(f"  Actual Total Cost: {node['Total Cost']}")
            print(f"  Discrepancy: {node['Total Cost'] - expected_cost:.4f}\n")
            output_str += f"Node type: {node['Node Type']}; Expected Cost: {expected_cost:.4f}; Actual Total Cost: {node['Total Cost']}; Discrepancy: {node['Total Cost'] - expected_cost:.4f}\n"
        self.explain_label.setPlainText(output_str)

    def add_nodes_edges(self, node, parent_graphics_item=None, x=0, y=0, y_step=50, depth=0):
        # Define horizontal offset
        x_offset = 200 // (depth + 1)
        
        # Create the graphics item for this node
        node_graphics_item = GraphNode(node['Node Type'])
        node_graphics_item.setPos(x, y)
        node_graphics_item.setZValue(1)
        self.scene.addItem(node_graphics_item)

        # If this is not the root node, draw an edge from the parent
        if parent_graphics_item is not None:
            line = QGraphicsLineItem(parent_graphics_item.x(), parent_graphics_item.y(), x, y)
            line.setPen(QPen(QColor('white')))
            line.setZValue(0.2)
            self.scene.addItem(line)

        # Recursively add child nodes
        if 'Plans' in node:
            child_offset = -x_offset if depth % 2 == 0 else x_offset  # Alternate left and right placement
            for index, subplan in enumerate(node['Plans']):
                new_x = x + (index - 0.5) * 2 * child_offset  # Position children with offset
                self.add_nodes_edges(subplan, node_graphics_item, new_x, y + y_step, y_step, depth + 1)

    def showPlan(self, plan):
        self.scene.clear()  # Clear the scene for a new plan

        plan_dict = json.loads(plan)  # Load plan from JSON string
        root_node = plan_dict[0]['Plan']
        self.add_nodes_edges(root_node)  # Pass the root node of the plan

        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)  # Fit the scene in the view
        
        # plan_dict = json.loads(plan)
        # # Clear the current model
        self.tree_model.removeRows(0, self.tree_model.rowCount())
        
        # Recursively load the plan nodes into the table tree view
        self.load_nodes(plan_dict[0]['Plan'], self.tree_model.invisibleRootItem())

        # Expand all nodes in the view for visibility
        self.tree_view.expandAll()
        
    def load_nodes(self, node, parent_item):
        # Create an item with the node type
        node_item = QStandardItem(node['Node Type'])
        # Additional details can be added in a similar manner
        cost_item = QStandardItem(f"{node['Total Cost']}")
        planned_rows_item = QStandardItem(f"{node['Plan Rows']}")
        actual_rows_item = QStandardItem(f"{node['Actual Rows']}")
        # width_item = QStandardItem(f"{node['Plan Width']}")
        actual_time_item = QStandardItem(f"{node['Actual Total Time']}")
        
        
        parent_item.appendRow([node_item, cost_item, planned_rows_item, actual_rows_item, actual_time_item])
        # parent_item.appendRow([node_item, cost_item, planned_rows_item, width_item, actual_time_item, actual_rows_item])
        
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
