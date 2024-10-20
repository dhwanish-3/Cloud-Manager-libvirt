import socket
import threading
import numpy as np
import os

# Server config
# Server ip address is obtained using the hostname command
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
def handle_client(client_socket):
    try:
        # Receive request from client (matrix size)
        request = client_socket.recv(1024).decode()
        print(f"Received request for matrix size: {request}")
        
        matrix_size = int(request)
        
        # Perform the CPU-intensive task of matrix multiplication
        result = matrix_multiplication_task(matrix_size)
        
        # Sending response back to client (matrix multiplication done)
        response = f"Matrix multiplication of size {matrix_size} completed"
        client_socket.send(response.encode())
        
    finally:
        client_socket.close()

# Server setup to handle multiple client connections
def server_thread(server_ip, server_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, server_port))
    server.listen(5)
    print(f"Server listening on {server_ip}:{server_port}")

    while True:
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")
        
        # Handle each client in a separate thread
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    # Get the IP address of the server
    server_ip = os.popen('hostname -I | awk \'{print $1}\'').read().strip()
    server_thread(server_ip, server_port)
