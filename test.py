import json

# Default PostgreSQL cost settings extracted from pgAdmin4
cost_params = {
    'seq_page_cost': 1.0,
    'random_page_cost': 4.0,
    'cpu_tuple_cost': 0.01,
    'cpu_operator_cost': 0.0025,
    'cpu_index_tuple_cost': 0.005,
    'cpu_hash_cost': 0.0025
}

def parse_plan(plan):
    nodes = []

    def recurse(node):
        # Basic node details
        node_info = {
            'Node Type': node.get('Node Type'),
            'Startup Cost': node.get('Startup Cost'),
            'Total Cost': node.get('Total Cost'),
            'Plan Rows': node.get('Plan Rows'),
            'Plan Width': node.get('Plan Width'),
            'Actual Rows': node.get('Actual Rows'),
            'Relation Name': node.get('Relation Name', ''),
            'Alias': node.get('Alias', ''),
            'Parent Relationship': node.get('Parent Relationship', None)
        }
        nodes.append(node_info)
        
        # Recursive parse subplans if they exist
        if 'Plans' in node:
            for subplan in node['Plans']:
                recurse(subplan)

    recurse(plan)
    return nodes

def compute_expected_cost(node, params):
    if node['Node Type'] == 'Seq Scan':
        # Assuming each page is read sequentially
        page_cost = node['Plan Rows'] * params['seq_page_cost'] + node['Plan Rows'] * params['cpu_tuple_cost']
        return page_cost
    elif node['Node Type'] == 'Hash Join':
        # Simplified model: cost of building the hash table plus cost of probing
        build_cost = node['Plan Rows'] * params['cpu_hash_cost']  # Cost to build hash table
        probe_cost = node['Actual Rows'] * params['cpu_operator_cost']  # Cost to probe hash table
        return build_cost + probe_cost
    elif node['Node Type'] == 'Hash':
        # Simplified model: cost of building the hash table plus cost of probing
        build_cost = node['Plan Rows'] * params['cpu_hash_cost']  # Cost to build hash table
        # probe_cost = node['Actual Rows'] * params['cpu_operator_cost']  # Cost to probe hash table
        return build_cost
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
        print(f"  Expected Cost: {expected_cost:.2f}")
        print(f"  Actual Total Cost: {node['Total Cost']}")
        print(f"  Discrepancy: {node['Total Cost'] - expected_cost:.2f}\n")

if __name__ == "__main__":
    example_json = 'test.json' # Path to json file here
    print("File executed")
    with open(example_json, 'r') as json_str:
        query = json_str.read()
        analyze_qep(query)
