# WWTP/init_data.sh
#!/bin/bash

# create data directories 
mkdir node-red
mkdir node-red/data
mkdir grafana
mkdir grafana/data

# Copy initial Node-RED data
cp -r ./initial_data/node-red/data/* ./node-red/data/

# Copy initial Grafana data
cp -r ./initial_data/grafana/data/* ./grafana/data/

# create a virtual env
cd Server
python3 -m venv venv
cd ..
