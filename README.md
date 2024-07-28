### Setup Instructions

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
4. **Build Docker Images**
   ```sh
   docker-compose build
5. **Deploy the Containers**
   ```sh
   docker-compose up -d
