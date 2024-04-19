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
    QTableWidget,
    QTableWidgetItem,
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
        self.setGeometry(100, 100, 1600, 900)  # setGeometry(x, y, w, h)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_layout = QVBoxLayout()

        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)  # For smoother graphics
        self.view.setBackgroundBrush(QBrush(Qt.black))
        left_layout.addWidget(self.view)

        self.table_widget = QTableWidget()
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setFixedHeight(180)
        left_layout.addWidget(self.table_widget)

        right_layout = QVBoxLayout()

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

        self.explain_table = QTableWidget()
        self.explain_table.setEditTriggers(QTableWidget.NoEditTriggers)

        right_layout.addWidget(self.explain_table)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

    def onSubmit(self):
        self.explain_label.setStyleSheet("color: white;")
        if self.query_input.toPlainText().strip() == "":
            self.explain_label.setPlainText("Please enter a query to explain.")
            self.explain_label.setStyleSheet("color: red;")
            return
        # costs_list = []

        sql_query = self.query_input.toPlainText().strip()
        plan = explain_query(sql_query)

        self.showPlan(plan)

        # self.display_explanation(plan)

        self.update_result_table(sql_query)
        self.update_explain_table(plan)

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
            print(f"Expected Cost: {expected_cost:.4f}")
            print(f"Actual Total Cost: {node['Total Cost']}")
            print(f"Discrepancy: {node['Total Cost'] - expected_cost:.4f}\n")
            output_str += f"Node type: \t{node['Node Type']}; Expected: {expected_cost:.4f}; Actual: {node['Total Cost']}; Discrepancy: {node['Total Cost'] - expected_cost:.4f}\n"

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

        self.tree_view.resizeColumnToContents(0)

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

    def update_result_table(self, sql_query):
        sql_query_results = query_to_dataframe(sql_query)

        self.table_widget.setRowCount(sql_query_results.shape[0])
        self.table_widget.setColumnCount(sql_query_results.shape[1])
        self.table_widget.setHorizontalHeaderLabels(sql_query_results.columns)

        for i in range(sql_query_results.shape[0]):
            for j in range(sql_query_results.shape[1]):
                self.table_widget.setItem(i, j, QTableWidgetItem(str(sql_query_results.iat[i, j])))

        self.table_widget.resizeColumnsToContents()

    def update_explain_table(self, plan):
        self.explain_label.clear()

        plan = json.loads(plan)
        root_plan = plan[0]["Plan"]
        nodes = parse_plan(root_plan)

        self.explain_table.setRowCount(len(nodes))
        self.explain_table.setColumnCount(4)
        self.explain_table.setHorizontalHeaderLabels(['Node Type', 'Expected Cost', 'Actual Cost', 'Discrepancy'])

        for i, node in enumerate(nodes):
            expected_cost = compute_expected_cost(node, cost_params)

            self.explain_table.setItem(i, 0, QTableWidgetItem(node['Node Type']))
            self.explain_table.setItem(i, 1, QTableWidgetItem(f"{expected_cost:.4f}"))
            self.explain_table.setItem(i, 2, QTableWidgetItem(f"{node['Total Cost']}"))
            self.explain_table.setItem(i, 3, QTableWidgetItem(f"{node['Total Cost'] - expected_cost:.4f}"))

        self.explain_table.resizeColumnsToContents()