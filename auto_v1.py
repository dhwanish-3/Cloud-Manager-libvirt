import libvirt
import time
import sys
import socket

# VM details for autoscaling
primary_vm_name = "ubuntu20.04_test1"
primary_vm_ip = "192.168.122.245"
primary_vm_port = 12345

extra_vm_name = "ubuntu20.04_test2"
extra_vm_ip = "192.168.122.86"
extra_vm_port = 12345

# Client config
client_ip = "192.168.122.1"
client_port = 6000

# Function to get CPU usage percentage with detailed stats
def get_cpu_usage(domain_obj, sleep_time=1):
    cpu_stat_1 = domain_obj.getCPUStats(True)[0]
    time.sleep(sleep_time)
    cpu_stat_2 = domain_obj.getCPUStats(True)[0]
    cpu_percent = 100 * ((cpu_stat_2['cpu_time'] - cpu_stat_1['cpu_time']) / 1000000000) / sleep_time
    domain_cpu_cores = len(domain_obj.vcpus()[0])
    return cpu_percent / domain_cpu_cores

# Monitor CPU usage and trigger autoscaling
def monitor_and_autoscale(conn, primary_vm_name, high_cpu_threshold=35.0, low_cpu_threshold=20.0, interval=2, cooldown_time=100):
    primary_domain = conn.lookupByName(primary_vm_name)
    if primary_domain is None:
        print(f"Primary domain {primary_vm_name} not found", file=sys.stderr)
        return

    running_vm = False
    extra_domain = None
    last_vm_start_time = 0

    while True:
        primary_cpu_usage = get_cpu_usage(primary_domain, interval)
        print(f"CPU usage of {primary_vm_name}: {primary_cpu_usage:.2f}%")

        if running_vm and extra_domain:
            extra_cpu_usage = get_cpu_usage(extra_domain, interval)
            print(f"CPU usage of {extra_vm_name}: {extra_cpu_usage:.2f}%")
        else:
            print(f"Extra VM {extra_vm_name} is not running.")

        if primary_cpu_usage > high_cpu_threshold and not running_vm:
            print(f"High CPU usage detected: {primary_cpu_usage:.2f}%. Triggering autoscaling...")
            extra_domain = start_new_vm(conn, extra_vm_name)
            if extra_domain:
                notify_client_of_new_vm(extra_vm_name, extra_vm_ip, extra_vm_port)
                running_vm = True
                last_vm_start_time = time.time()

        elif primary_cpu_usage < low_cpu_threshold and running_vm:
            if time.time() - last_vm_start_time >= cooldown_time:
                print(f"Low CPU usage detected: {primary_cpu_usage:.2f}%. Shutting down extra VM...")
                stop_extra_vm(extra_domain)
                notify_client_vm_removed(extra_vm_name, extra_vm_ip, extra_vm_port)
                running_vm = False
            else:
                print(f"Cooldown in effect. Extra VM will not be shut down yet.")

        time.sleep(interval)

def start_new_vm(conn, vm_name):
    try:
        domain = conn.lookupByName(vm_name)
        if domain.isActive():
            print(f"VM {vm_name} is already running.")
        else:
            domain.create()
            print(f"New VM {vm_name} started successfully.")
            
        # Wait for VM to fully boot (customize this duration as needed)
        print("Waiting for VM to fully boot...")
        time.sleep(15)
        return domain
    except libvirt.libvirtError as e:
        print(f"Error starting new VM {vm_name}: {e}")
        return None

def stop_extra_vm(domain):
    try:
        if domain.isActive():
            domain.destroy()
            print(f"Extra VM stopped successfully.")
        else:
            print(f"Extra VM is not running.")
    except libvirt.libvirtError as e:
        print(f"Error stopping extra VM: {e}")

def notify_client_of_new_vm(vm_name, vm_ip, vm_port):
    message = f"New VM available:{vm_name}:{vm_ip}:{vm_port}"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(message.encode(), (client_ip, client_port))
            print("Client notified of new VM.")
    except ConnectionError as e:
        print(f"Error notifying client: {e}")

def notify_client_vm_removed(vm_name, vm_ip, vm_port):
    message = f"VM removed:{vm_name}:{vm_ip}:{vm_port}"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(message.encode(), (client_ip, client_port))
            print("Client notified of VM removal.")
    except ConnectionError as e:
        print(f"Error notifying client: {e}")

if __name__ == "__main__":
    conn = libvirt.open('qemu:///system')
    if conn is None:
        print("Failed to open connection to qemu:///system", file=sys.stderr)
        sys.exit(1)

    try:
        monitor_and_autoscale(conn, primary_vm_name)
    finally:
        conn.close()

