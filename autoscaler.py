import libvirt
import time
import sys
import socket

#! DO UPDATE THESE VARIABLES
# VM details for autoscaling
primary_vm_name = "ubuntu0"
primary_vm_ip = "192.168.122.86"
primary_vm_port = 12345

extra_vm_name = "ubuntu1"
extra_vm_ip = "192.168.122.125"
extra_vm_port = 12345

# Client config
client_ip = "172.18.56.30"
client_port = 6000

# Function to get CPU usage percentage with detailed stats
def get_cpu_usage(domain_obj, sleep_time=1):
    """
    Calculate CPU usage for the given domain over a period.
    :param domain_obj: The domain (VM) object.
    :param sleep_time: Time interval to measure CPU usage in seconds.
    :return: CPU usage percentage.
    """
    # First CPU stats
    cpu_stat_1 = domain_obj.getCPUStats(True)[0]
    time.sleep(sleep_time)
    # Second CPU stats
    cpu_stat_2 = domain_obj.getCPUStats(True)[0]

    # Calculate CPU usage percentage
    cpu_percent = 100 * ((cpu_stat_2['cpu_time'] - cpu_stat_1['cpu_time']) / 1000000000) / sleep_time
    domain_cpu_cores = len(domain_obj.vcpus()[0])

    # Return CPU usage normalized over all CPU cores
    return cpu_percent / domain_cpu_cores

# Monitor CPU usage and trigger autoscaling
def monitor_and_autoscale(conn, primary_vm_name, high_cpu_threshold=35.0, low_cpu_threshold=20.0, interval=2):
    primary_domain = conn.lookupByName(primary_vm_name)
    if primary_domain is None:
        print(f"Primary domain {primary_vm_name} not found", file=sys.stderr)
        return

    running_vm = False  # Flag to track if extra VM is running
    extra_domain = None

    while True:
        # Calculate CPU usage of the primary VM
        primary_cpu_usage = get_cpu_usage(primary_domain, interval)
        print(f"CPU usage of {primary_vm_name}: {primary_cpu_usage:.2f}%")

        # If extra VM is running, calculate its CPU usage as well
        if running_vm and extra_domain:
            extra_cpu_usage = get_cpu_usage(extra_domain, interval)
            print(f"CPU usage of {extra_vm_name}: {extra_cpu_usage:.2f}%")
        else:
            print(f"Extra VM {extra_vm_name} is not running.")

        # Check if CPU usage is above the high threshold and no extra VM is running
        if primary_cpu_usage > high_cpu_threshold and not running_vm:
            print(f"High CPU usage detected: {primary_cpu_usage:.2f}%. Triggering autoscaling...")
            # Start a new VM (autoscale logic)
            extra_domain = start_new_vm(conn, extra_vm_name)
            if extra_domain:
                notify_client_of_new_vm(extra_vm_name + ":" + extra_vm_ip + ":" + str(extra_vm_port))  # Pass the new VM name
                running_vm = True  # Update flag to indicate extra VM is running

        # Check if CPU usage is below the low threshold and extra VM is running
        elif primary_cpu_usage < low_cpu_threshold and running_vm:
            print(f"Low CPU usage detected: {primary_cpu_usage:.2f}%. Shutting down extra VM...")
            # Shut down the extra VM (autoscale down logic)
            stop_extra_vm(extra_domain)
            notify_client_vm_removed(extra_vm_name + ":" + extra_vm_ip + ":" + str(extra_vm_port))  # Pass the extra VM name
            running_vm = False  # Update flag to indicate extra VM is stopped

        # Wait for next monitoring interval
        time.sleep(interval)

# Function to start a new VM
def start_new_vm(conn, vm_name):
    """
    Starts a new VM by looking it up and booting it.
    """
    try:
        domain = conn.lookupByName(vm_name)
        if domain.isActive():
            print(f"VM {vm_name} is already running.")
        else:
            domain.create()  # Start the VM
            print(f"New VM {vm_name} started successfully.")
        return domain
    except libvirt.libvirtError as e:
        print(f"Error starting new VM {vm_name}: {e}")
        return None

# Function to stop an extra VM
def stop_extra_vm(domain):
    """
    Shuts down the extra VM by stopping it.
    """
    try:
        if domain.isActive():
            domain.destroy()  # Shut down the VM
            print(f"Extra VM stopped successfully.")
        else:
            print(f"Extra VM is not running.")
    except libvirt.libvirtError as e:
        print(f"Error stopping extra VM: {e}")

# Function to notify the client of a new VM (e.g., via a socket)
def notify_client_of_new_vm(vm_name):
    message = f"New VM available: {vm_name}"

    try:
        # Create a socket to send the notification to the client
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(message.encode(), (client_ip, client_port))
            print("Client notified of new VM.")
    except ConnectionError as e:
        print(f"Error notifying client: {e}")

# Function to notify the client that a VM has been removed
def notify_client_vm_removed(vm_name):
    message = f"VM removed: {vm_name}"

    try:
        # Create a socket to send the notification to the client
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(message.encode(), (client_ip, client_port))
            print("Client notified of VM removal.")
    except ConnectionError as e:
        print(f"Error notifying client: {e}")
if __name__ == "__main__":
    # Connect to the hypervisor
    conn = libvirt.open('qemu:///system')
    if conn is None:
        print("Failed to open connection to qemu:///system", file=sys.stderr)
        sys.exit(1)

    try:
        # Start monitoring and autoscaling based on CPU usage
        monitor_and_autoscale(conn, primary_vm_name)
    finally:
        conn.close()

