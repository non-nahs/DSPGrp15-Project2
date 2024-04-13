import psycopg2
import json

def connect_db():
    """ Modify according to how you set up your database. """
    return psycopg2.connect(
        dbname='TPC-H', 
        user='postgres', 
        password='secret', 
        host='localhost', 
        port='5432')

def explain_query(sql_query):
    """ Executes the EXPLAIN command on the provided SQL query and returns the analysis. """
    db_conn = connect_db()
    cursor = db_conn.cursor()
    try:
        # Adjust the EXPLAIN command according to your needs
        explain_sql = f"EXPLAIN (FORMAT JSON, ANALYZE) {sql_query};"
        cursor.execute(explain_sql)
        result = cursor.fetchall()
        plan_json = json.dumps(result[0][0])
        return plan_json
        # execution_plan = json.loads(result)
        # plan_nodes = extract_nodes(execution_plan[0][0]['Plan'])
        # print(f"Query processed, plan generated")
        # return plan_nodes
        # return analyze_costs(result)
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        cursor.close()
        db_conn.close()

def format_plan(plan):
    """Convert the JSON execution plan into a human-readable string."""
    plan_json = json.loads(plan)  # Load JSON content
    formatted_plan = json.dumps(plan_json, indent=4)  # Format with indentation
    return formatted_plan

def analyze_costs(explain_result):
    """ Analyze the JSON result from the EXPLAIN command and generate a human-readable explanation. """
    # This should parse the JSON and create a meaningful explanation. Placeholder for now.
    return "Detailed cost analysis based on the QEP:\n" + str(explain_result)

def extract_nodes(plan, parent_item=None):
    """ Recursively extract the nodes and add them to the tree model starting from the given parent item. """
    # This recursive function builds a nested dictionary to represent the plan tree
    node_data = {
        'Node Type': plan['Node Type'],
        'Startup Cost': plan['Startup Cost'],
        'Total Cost': plan['Total Cost'],
        'Plan Rows': plan['Plan Rows'],
        'Plan Width': plan['Plan Width'],
        'Plans': []
    }

    # Recursively call extract_nodes on sub-plans, if they exist
    if 'Plans' in plan:
        for subplan in plan['Plans']:
            child_node_data = extract_nodes(subplan)
            node_data['Plans'].append(child_node_data)

    return node_data