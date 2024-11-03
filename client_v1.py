import socket
import threading
import time
import matplotlib.pyplot as plt

# delay between requests
delay_between_requests_low = 0.1
delay_between_requests_high = 0.05

# Server config
server_ip = "192.168.122.86"
server_port = 12345

# client config
client_ip = "192.168.122.1"
client_port = 6000

# Matrix config
low_matrix_size = 600
high_matrix_size = 1000

# Number of requests
low_num_requests = 100
high_num_requests = 160

# List of servers available (IPs and Ports)
servers = [(server_ip, server_port)]

# Lock for thread-safe access to the servers list
servers_lock = threading.Lock()

# Global round-robin pointer for distributing requests
server_pointer = 0

latency_data = [0]
time_data = [0]

plt.ion()
fig, ax = plt.subplots()
ax.clear()
ax.plot(time_data, latency_data, label="Latency")
ax.legend()
ax.set_xlabel('Time (s)')
ax.set_ylabel('Latency (s)')
ax.set_xlim([-100, 0])
ax.set_ylim([0, 0.1])
plt.pause(0.01)

def send_request(server_ip, server_port, matrix_size, latency_data):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(1)  # Set timeout to 1 second
    latency = time.time()
    try:
        client.sendto(str(matrix_size).encode(), (server_ip, server_port))
        response, _ = client.recvfrom(1024)
        response_time = time.time()
        latency = response_time - latency
        # Take average of latest 100 values in latency_data
        if len(latency_data) > 9:
            avg_latency = (sum(latency_data[-9:]) + latency) / 10
        else:
            avg_latency = (sum(latency_data) + latency) / len(latency_data)
        latency_data.append(avg_latency)
        print(f"Response from {server_ip}:{server_port} - {response.decode()} with latency {latency} (avg: {avg_latency})")
    except socket.timeout:
        latency_data.append(latency_data[-1])
    finally:
        client.close()

def send_requests_to_servers(matrix_size, num_requests, delay_between_requests):
    global server_pointer
    threads = []
    
    for _ in range(num_requests):
        with servers_lock:
            if not servers:
                print("No servers available!")
                break
            current_servers = list(servers)
            num_servers = len(current_servers)
        next_sleep_time = time.time() + delay_between_requests
        server_ip, server_port = current_servers[server_pointer % num_servers]
        print(f"Server_ip is : {server_ip}")
        server_pointer = server_pointer + 1
	
        t = threading.Thread(target=send_request, args=(server_ip, server_port, matrix_size, latency_data))
        threads.append(t)
        t.start()
        t.join()

        # Plotting
        current_time = time.time()
        time_data.append(current_time)
        ax.clear()
        # Adjust time data to show the last 100 seconds
        adjusted_time_data = [(t - current_time) for t in time_data[-1000:]]
        ax.plot(adjusted_time_data, latency_data[-1000:], label="Latency")
        ax.legend()
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Average Latency (s)')
        ax.set_xlim([-100, 0])
        ax.set_ylim([0, 0.1])
        plt.pause(0.01)

        if time.time() < next_sleep_time:
            time.sleep(next_sleep_time - time.time())

    for t in threads:
        t.join()
        

def listen_for_autoscaler_notifications(client_ip, client_port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((client_ip, client_port))
        
        while True:
            notification, _ = s.recvfrom(1024)
            if notification:
                print(f"Notification from autoscaler: {notification.decode()}")
                new_server_info = notification.decode().split(':')
                global servers
                if new_server_info[0] == "VM removed":
                    with servers_lock:
                        servers = [(server_ip, server_port) for server_ip, server_port in servers if server_ip != new_server_info[2]]
                    print(f"VM removed. Available servers: {len(servers)}")
                elif new_server_info[0] == "New VM available":
                    new_server_ip = new_server_info[2]
                    new_server_port = int(new_server_info[3])
                    with servers_lock:
                        servers.append((new_server_ip, new_server_port))
                    print(f"New VM added. Available servers: {len(servers)}")



if __name__ == "__main__":
    matrix_size = 0
    delay_between_requests = 1000000
    num_requests = 0
    notification_thread = threading.Thread(target=listen_for_autoscaler_notifications, args=(client_ip, client_port))
    notification_thread.start()
    print(f"Listening for autoscaler notifications on {client_ip}:{client_port}...")

    while True:
        mode = input("Enter new mode (low/high): ").strip().lower()
        if mode == "low":
            matrix_size = low_matrix_size
            num_requests = low_num_requests
            delay_between_requests = delay_between_requests_low
        elif mode == "high":
            matrix_size = high_matrix_size
            num_requests = high_num_requests
            delay_between_requests = delay_between_requests_high
        elif mode == "exit":
            print("Exiting...")
            break
        else:
            print("Invalid mode. Please enter 'low' or 'high' or 'exit' to quit.")
            continue
        send_requests_to_servers(matrix_size, num_requests, delay_between_requests)
