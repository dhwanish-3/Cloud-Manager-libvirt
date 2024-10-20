import socket
import threading

# Server config
server_ip = "192.168.122.86"
server_port = 12345

# client config
client_ip = "172.18.56.30"
client_port = 6000

# Matrix config
low_matrix_size = 800
high_matrix_size = 1000

# Number of requests
low_num_requests = 100
high_num_requests = 300

# Client function to send requests to the servers
def send_request(server_ip, server_port, matrix_size):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, server_port))
        
        # Send matrix size to the server
        client.send(str(matrix_size).encode())
        
        # Receive response from the server
        response = client.recv(1024).decode()
        print(f"Response from {server_ip}:{server_port} - {response}")
        
    except ConnectionRefusedError:
        print(f"Connection failed to {server_ip}:{server_port}. Server may not be available.")
        
    finally:
        client.close()

# Function to send requests to multiple servers concurrently
def send_requests_to_servers(servers, matrix_size, num_requests):
    threads = []
    
    for _ in range(num_requests): #issue
        for server_ip, server_port in servers:
            # Create a new thread for each request to a server
            t = threading.Thread(target=send_request, args=(server_ip, server_port, matrix_size))
            threads.append(t)
            t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

# Function to listen for notifications from the autoscaler
def listen_for_autoscaler_notifications(client_ip, client_port, servers):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((client_ip, client_port))
        s.listen()
        print(f"Listening for autoscaler notifications on {client_ip}:{client_port}...")
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                notification = conn.recv(1024)
                if notification:
                    print(f"Notification from autoscaler: {notification.decode()}")
                    # Example: If the notification is about a new server, update the servers list
                    # You can parse the notification to get the new server IP and port
                    new_server_info = notification.decode().split(':')
                    # Check if the notification is about a new server or a removed server
                    if new_server_info[0] == "VM removed":
                        servers = [(server_ip, server_port) for server_ip, server_port in servers if server_ip != new_server_info[2]]
                    elif new_server_info[0] == "New VM available":
                        new_server_ip = new_server_info[2]
                        new_server_port = int(new_server_info[3])
                        servers.append((new_server_ip, new_server_port))  # Add new server to the list



if __name__ == "__main__":
    # List of servers available (IPs and Ports)
    servers = [(server_ip, server_port)]  # Add more servers as they are spawned
    
    # Start listening for autoscaler notifications in a separate thread
    notification_thread = threading.Thread(target=listen_for_autoscaler_notifications, args=(client_ip, client_port, servers))
    notification_thread.start()

    # Simulation of scaling:
    while True:
        mode = input("Enter new mode (low/high): ").strip().lower()
        if mode == "low":
            matrix_size = low_matrix_size
            num_requests = low_num_requests
        elif mode == "high":
            matrix_size = high_matrix_size
            num_requests = high_num_requests
        else:
            print("Invalid mode. Exiting.")
            break
        
        # Send updated requests to the servers
        send_requests_to_servers(servers, matrix_size, num_requests)
