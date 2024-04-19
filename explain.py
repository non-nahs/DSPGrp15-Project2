import pandas as pd
import psycopg2
import json

cost_params = {
    'seq_page_cost': 1.0,
    'random_page_cost': 4.0,
    'cpu_tuple_cost': 0.01,
    'cpu_operator_cost': 0.0025,
    'cpu_index_tuple_cost': 0.005,
    'cpu_hash_cost': 0.0025
}


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
        print(json.dumps(result[0][0], indent=4))
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


def query_to_dataframe(sql_query):
    db_conn = connect_db()
    cursor = db_conn.cursor()

    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]

        df = pd.DataFrame(rows, columns=col_names)
        return df

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error:", error)
        return None
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
        'Actual Total Time': plan['Actual Total Time'],
        'Actual Rows': plan['Actual Rows'],
        'Plans': []
    }

    # Recursively call extract_nodes on sub-plans, if they exist
    if 'Plans' in plan:
        for subplan in plan['Plans']:
            child_node_data = extract_nodes(subplan)
            node_data['Plans'].append(child_node_data)

    return node_data


def flatten_list(nested_list):
    """
    Flattens a nested list into a single-level list.
    """
    flattened = []
    for item in nested_list:
        if isinstance(item, list):
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened


def extract_node_types(plan):
    """ Extract the node types from the nested dictionary representation of the plan tree. """
    # This function extracts the node types from the nested dictionary
    node_types = [plan['Node Type']]

    # Recursively add the node types from sub-plans
    if 'Plans' in plan:
        for subplan in plan['Plans']:
            node_types.append(extract_node_types(subplan))
    # return node_types
    return flatten_list(node_types)


def parse_plan(plan):
    # print(plan)
    # print(type(plan))
    nodes = []

    def recurse(node):
        # Basic node details
        node_info = {
            'Node Type': node['Node Type'],
            'Startup Cost': node['Startup Cost'],
            'Total Cost': node['Total Cost'],
            'Plan Rows': node['Plan Rows'],
            'Plan Width': node['Plan Width'],
            'Actual Rows': node['Actual Rows'],
            # 'Relation Name': node['Relation Name'] if 'Relation Name' in node else '',
            # 'Alias': node['Alias'] if 'Alias' in node else '',
            # 'Parent Relationship': node['Parent Relationship'] if 'Parent Relationship' in node else None
        }
        nodes.append(node_info)
        
        # Recursive parse subplans if they exist
        if 'Plans' in node:
            for subplan in node['Plans']:
                recurse(subplan)

    recurse(plan)
    return nodes


def compute_expected_cost(node, params):
    # To update those cases with return 0
    if node['Node Type'] == 'Seq Scan':
        # Assuming each page is read sequentially
        page_cost = node['Plan Rows'] * params['seq_page_cost'] + node['Plan Rows'] * params['cpu_tuple_cost']
        return page_cost
    elif node['Node Type'] == 'Index Scan':
        # Cost per index scan typically involves random page cost due to random access nature of indexes
        index_scan_cost = node['Plan Rows'] * params['random_page_cost'] + node['Plan Rows'] * params['cpu_index_tuple_cost']
        return index_scan_cost
    elif node['Node Type'] == 'Hash Join':
        # Simplified model: cost of building the hash table plus cost of probing
        build_cost = node['Plan Rows'] * params['cpu_hash_cost']  # Cost to build hash table
        probe_cost = node['Actual Rows'] * params['cpu_operator_cost']  # Cost to probe hash table
        return build_cost + probe_cost
    elif node['Node Type'] == 'Nested Loop':
        # Outer plan and inner plan were not saved in the node relationships so no calculations possible for now
        # For Nested Loops, the cost is the outer plan cost plus the inner plan cost multiplied by the number of rows in the outer plan
        outer_plan_cost = compute_expected_cost(node['Outer Plan'], params)  # This function should be called on the outer plan node
        inner_plan_cost = compute_expected_cost(node['Inner Plan'], params)  # This function should be called on the inner plan node
        nested_loop_cost = outer_plan_cost + (inner_plan_cost * node['Outer Plan']['Plan Rows'])
        return 0
        # return nested_loop_cost
    elif node['Node Type'] == 'Hash':
        # Simplified model: cost of building the hash table plus cost of probing
        build_cost = node['Plan Rows'] * params['cpu_hash_cost']  # Cost to build hash table
        # probe_cost = node['Actual Rows'] * params['cpu_operator_cost']  # Cost to probe hash table
        return build_cost
    elif node['Node Type'] == 'Memoize':
        # Assuming memoization involves a fixed cost for cache lookup and a variable cost if a cache miss occurs
        cache_lookup_cost = params['cpu_operator_cost']  # Cost for looking up in the cache
        cache_miss_cost = node['Plan Rows'] * params['cpu_operator_cost']  # Assume each miss incurs some cost
        memoize_cost = cache_lookup_cost + cache_miss_cost
        return memoize_cost
    return 0


def analyze_qep(json_input):
    # Load JSON data
    plan_data = json.loads(json_input)
    plan = plan_data[0]['Plan']

    # Parse and compute costs
    nodes = parse_plan(plan)
    for node in nodes:
        expected_cost = compute_expected_cost(node, cost_params)
        print(f"Node: {node['Node Type']}")
        print(f"Expected: {expected_cost:.2f}")
        print(f"Actual: {node['Total Cost']}")
        print(f"Discrepancy: {node['Total Cost'] - expected_cost:.2f}\n")
