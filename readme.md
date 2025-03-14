# Reef Automatic Dosing Pump
This project is a work in progress for an automatic dosing pump for reef aquariums. It runs on a Raspberry Pi and is designed to help you maintain the perfect balance of nutrients in your reef tank.
![IMG_0695](https://github.com/user-attachments/assets/97f26f6b-104b-410d-89c0-19fd33c77315)

## Requirements
- Raspberry Pi
- 12V Power Supply
- L298N Motor Driver
- 12V to 5V Buck Converter
- Peristaltic Pumps

## Getting Started
1. **Download the Code**:
Clone the repository to your Raspberry Pi:
```shell
git clone https://github.com/facuadrado/dosing_pump.git
cd dosing_pump
```

2. **Modify the Code**:
Update the pin configurations in the code to match your setup.

3. **Build and Run the Docker Container**:
Use Docker Compose to build and run the application:
```shell
docker-compose up --build -d
```
4. **Access the API**:
Once the application is running, you can access the API documentation at:
```http://<raspberry-pi-ip>:8000/docs```

## Future Enhancements
- Creating a user interface & Mobile App
- Integration with AWS Cloud
- Create Calibration Endpoint (hard-coded at the moment)

### Other Useful Docker Commands

Build the docker image
```shell
docker build -t fastapi-doser .
```

Run the Docker Container
```shell
docker run --privileged --mount type=volume,src=doser-mnt,dst=/mnt -p 8000:8000 fastapi-doser
```
Persistent 24/7 run
```shell
docker run --privileged -d --restart unless-stopped --mount type=volume,src=doser-mnt,dst=/mnt -p 8000:8000 fastapi-doser
```

Bash into container
```shell
docker exec -it <container-id> /bin/Bash
```
