# WWTP/init_data.sh
#!/bin/bash

# Copy initial Node-RED data
cp -r ./initial_data/node-red/data/* ./node-red/data/

# Copy initial Grafana data
cp -r ./initial_data/grafana/data/* ./grafana/data/
