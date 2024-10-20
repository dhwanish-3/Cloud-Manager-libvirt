import socket
import threading
import numpy as np
import os

# Server config
# Server IP address is obtained using the hostname command
server_port = 12345

# Function to simulate a CPU-intensive task - Matrix Multiplication
def matrix_multiplication_task(size):
    # Create two random matrices
    matrix_a = np.random.rand(size, size)
    matrix_b = np.random.rand(size, size)
    
    # Perform matrix multiplication
    result_matrix = np.dot(matrix_a, matrix_b)
    
    return result_matrix

# Function to handle each client request
def handle_client(data, addr, server_socket):
    try:
        # Receive request from client (matrix size)
        request = data.decode()
        print(f"Received request for matrix size: {request} from {addr}")
        
        matrix_size = int(request)
        
        # Perform the CPU-intensive task of matrix multiplication
        result = matrix_multiplication_task(matrix_size)
        
        # Sending response back to client (matrix multiplication done)
        response = f"Matrix multiplication of size {matrix_size} completed"
        server_socket.sendto(response.encode(), addr)
        
    except Exception as e:
        print(f"Error handling client {addr}: {e}")

# Server setup to handle multiple client connections
def server_thread(server_ip, server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))
    print(f"Server listening on {server_ip}:{server_port}")

    while True:
        data, addr = server_socket.recvfrom(1024)
        # Handle each client in a separate thread
        client_handler = threading.Thread(target=handle_client, args=(data, addr, server_socket))
        client_handler.start()

if __name__ == "__main__":
    # Get the IP address of the server
    server_ip = os.popen('hostname -I | awk \'{print $1}\'').read().strip()
    server_thread(server_ip, server_port)
