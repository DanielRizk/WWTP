## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python**: The project is developed with Python. You must have Python installed to run the Python scripts. Visit [Python's official site](https://www.python.org/downloads/) for installation instructions.
  
- **Pip**: Install pip if not installed
   ```sh
   sudo apt install python3-pip
   ```sh
   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
   
- **build-essential**: Install build-essential and other required packages:
   ```sh
   sudo apt install python3-pip
   ```
-**Docker**: Docker is used for building and running the application in an isolated environment. Download and install Docker from [Docker's official site](https://www.docker.com/get-started).

- **Docker Compose**: This tool is used for defining and running multi-container Docker applications. After installing Docker, you can install Docker Compose by following the instructions on the [official Docker Compose page](https://docs.docker.com/compose/install/).

   ### or
   ```sh
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.3.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

## Installation

1. **Clone the Repository**
   ```sh
   git clone https://github.com/DanielRizk/WWTP.git
   cd WWTP
2. **Make init_data.sh Executable**
   ```sh
   sudo chmod +x init_data.sh
3. **Run the Initialization Script**
   ```sh
   ./init_data.sh

## Usage

1. **Build Docker Images**
   ```sh
   docker-compose build
2. **Deploy the Containers**
   ```sh
   docker-compose up -d
