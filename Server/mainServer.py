from flask import Flask, request, jsonify
import time
import json
import os
import uuid
import requests
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryOptions
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

config_path = "server.config"

def load_config(filename):
    try:
        # Read and parse the configuration file
        config = {}
        with open(filename, 'r') as file:
            for line in file:
                if "=" in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")  # Remove possible quotes
                    config[key] = value
        
        # Validate presence of all required configurations
        influxdb_url = config['influxdb_url']
        nodeRed_url = config['nodeRed_url']
        org = config['org']
        bucket = config['bucket']
        token = config['token']
        env_data_url = config['env_data_url']

        # Return the loaded configuration
        return {
            "influxdb_url": influxdb_url,
            "nodeRed_url": nodeRed_url,
            "org": org,
            "bucket": bucket,
            "token" : token,
            "env_data_url" : env_data_url
        }
    
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except KeyError as e:
        print(f"Missing configuration for: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        
config = load_config(config_path)

if not config:
    exit()

# Initialize InfluxDB client
client = InfluxDBClient(url=config['influxdb_url'], token=config['token'], org=config['org'])
write_api = client.write_api(write_options=SYNCHRONOUS)

# Node ID management using a JSON file
db_file = 'node_ids.json'

if os.path.exists(db_file):
    with open(db_file, 'r') as file:
        node_ids = json.load(file)
else:
    node_ids = {}

def save_node_ids():
    with open(db_file, 'w') as file:
        json.dump(node_ids, file, indent=4)
        
def get_smallest_available_id():
    available_ids = sorted([int(key.split('_')[1]) for key, value in node_ids.items() if value['available']])
    if available_ids:
        return f"Node_{available_ids[0]:02d}"
    else:
        if node_ids:
            last_id = max(int(key.split('_')[1]) for key in node_ids.keys()) + 1
        else:
            last_id = 1
        return f"Node_{last_id:02d}"
        
def is_node_red_ready():
    """Check if Node-RED is up and accepting connections."""
    try:
        response = requests.get(config["nodeRed_url"])
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    return False
    
def send_configuration_requests():
    """Send configuration requests to Node-RED."""
    measure_payload = {"int": 3600}
    send_payload = {"int": 14400}
    try:
        requests.post(f'{config["nodeRed_url"]}/control_node/set_measure_int', json=measure_payload)
        requests.post(f'{config["nodeRed_url"]}/control_node/set_send_int', json=send_payload)
        print("Configuration requests sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send configuration requests: {e}")
        
def wait_for_node_red():
    """Wait for Node-RED to be ready and then send configuration requests."""
    while not is_node_red_ready():
        print("Waiting for Node-RED to be ready...")
        time.sleep(5)  # Wait for 5 seconds before trying again
    send_configuration_requests()

@app.route('/request_id', methods=['GET'])
def request_id():
    check_and_reassign_old_ids()
    node_id = get_smallest_available_id()
    unique_id = uuid.uuid4()
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M")
    node_ids[node_id] = {'available': False, 'timestamp': timestamp, 'uuid' : str(unique_id)}
    save_node_ids()
    return jsonify({"node_id":node_id, "uuid":unique_id}), 200

@app.route('/send_data', methods=['POST'])
def send_data():
    payload = request.get_json()
    try:
        nodeID = payload["Node_ID"]
        nodeUIDD = payload["Node_UUID"]    
         
        if ((nodeID in node_ids) and (nodeUIDD == node_ids[nodeID]["uuid"])):
            if (payload["Temperature"] and payload["pH"] and payload["Turbidity"] and payload["EC"] and payload["TDS"]):
                temp = float(payload["Temperature"])
                ph = float(payload["pH"])
                turbidity = float(payload["Turbidity"])
                ec = float(payload["EC"])
                tds = float(payload["TDS"])
        
                sensor_point = Point(nodeID).field("Temperature", temp).field("Turbidity", turbidity)\
                .field("pH", ph).field("TDS", tds).field("EC", ec)
            
                response = requests.get(config["env_data_url"])
                resp_data = response.json()
                env_data = resp_data['data']
            
                env_point = Point("Environmental_data")
                
                if isinstance(env_data, list) and env_data:
                    for cat_name, cat_val in env_data.items():
                        for measurement, attr in cat_val.items():
                            env_point.field(f'{cat_name}/{measurement}', float(attr['value']))
                    write_api.write(bucket=config['bucket'], org=config['org'], record=env_point)
                    
                write_api.write(bucket=config['bucket'], org=config['org'], record=sensor_point)
            
            return jsonify({"Status":"Data sent successfuly"}), 200
        else:
            return jsonify({"Status":"Node reconfig is required"}), 404
        
    except Exception as e:
        return jsonify({"Status" : "Invalid request payload" + str(e)}), 400
    
@app.route('/node_feedback', methods=['POST'])
def node_feedback():
    data = request.json
    node_id = data.get('node_id')
    if node_id in node_ids:
        node_ids[node_id]['timestamp'] = datetime.now().strftime("%d/%m/%Y-%H:%M")
        check_and_reassign_old_ids()
        save_node_ids()
        return jsonify({"status": "updated", "node_id": node_id}), 200
    else:
        return jsonify({"error": "Node ID not found"}), 404

def check_and_reassign_old_ids():
    current_time = datetime.now()
    one_day_ago = current_time - timedelta(days=1)
    for node, details in node_ids.items():
        node_time = datetime.strptime(details['timestamp'], "%d/%m/%Y-%H:%M")
        if node_time < one_day_ago:
            node_ids[node]['available'] = True
            node_ids[node]['uuid'] = "xxx"
            

@app.route('/data/<node_id>', methods=['GET'])
def get_measurement(node_id):
    # General filters for fields
    fields_filter = 'r._field == "EC" or r._field == "TDS" or r._field == "Temperature" or r._field == "Turbidity" or r._field == "pH"'
    try:
        
        if node_id == "env":
            query = f"""from(bucket: "{config['bucket']}")
                        |> range(start: -24h)
                        |> filter(fn: (r) => r._measurement == "Environmental_data")
                        |> last()
                        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")"""
                        
            result = client.query_api().query(org=config['org'], query=query)
            if result and len(result) > 0 and len(result[0].records) > 0:
                data = result[0].records[0].values
                return jsonify(data), 200
            else:
                return jsonify({"error" : "No env data available"}) , 404

            
        elif node_id == "all":
            all_data = {}
            # Assume `node_ids` is a dictionary of node IDs and availability
            for node, details in node_ids.items():
                if not details['available']:
                    # Query to get the latest data for each field from each node
                    query = f"""from(bucket: "{config['bucket']}")
                                |> range(start: -24h)
                                |> filter(fn: (r) => r._measurement == "{node}" and ({fields_filter}))
                                |> last()"""

                    # Execute the query
                    result = client.query_api().query(org=config['org'], query=query)
                    measurements = {}
                    for table in result:
                        for record in table.records:
                            measurements[record.get_field()] = record.get_value()
                
                    all_data[node] = measurements

            return jsonify(all_data), 200

        else:
            # Query to get the latest data for all fields for a specific node
            query = f"""from(bucket: "{config['bucket']}")
                        |> range(start: -24h)
                        |> filter(fn: (r) => r._measurement == "{node_id}" and ({fields_filter}))
                        |> last()"""

            result = client.query_api().query(org=config['org'], query=query)
            measurements = {}
            for table in result:
                for record in table.records:
                    measurements[record.get_field()] = record.get_value()

            if measurements:
                return jsonify(measurements), 200
            else:
                return jsonify({"error": "No data found for this node"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/control_node/one-off', methods=['POST'])
def control_node_one_off():
    payload = request.get_json()
    try:
        payload["Cmd"]
        payload["Node_ID"]
        response = requests.post(f'{config["nodeRed_url"]}/control/one-off', json=payload, headers=request.headers)
        return jsonify({"Status":"One-off measurment executed"}), 200
    except:
        return jsonify({"Status":"Inavlid request"}), 400

@app.route('/control_node/set_measure_int', methods=['POST'])
def control_node_measure_int():
    payload = request.get_json()
    try:
        payload["int"]
        response = requests.post(f'{config["nodeRed_url"]}/control/set_measure_int', json=payload, headers=request.headers)
        return jsonify({"Status":"Measure time modified"}), 200
    except:
        return jsonify({"Status":"Inavlid request"}), 400

@app.route('/control_node/set_send_int', methods=['POST'])
def control_node_send_int():
    payload = request.get_json()
    try:
        payload["int"]
        response = requests.post(f'{config["nodeRed_url"]}/control/set_send_int', json=payload, headers=request.headers)
        return jsonify({"Status":"Sending time modified"}), 200
    except:
        return jsonify({"Status":"Inavlid request"}), 400

if __name__ == '__main__':
    wait_for_node_red()
    app.run(debug=True, host='0.0.0.0')
