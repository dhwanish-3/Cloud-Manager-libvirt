# Cloud Computing - Assignment

- Programming Assignment 2 - Build your own auto-scaling client server application using the libvirt API

### Solution Details and Results

- Features:
    - Real time CPU utilization graph
    - Increase the number of server VM's in case of overload
    - Decrease the number of server VM's in case of low load
    - Inform the client program (which plays the role of load balancer) in case of VM failures

- CPU utilization graph plotted in real time by the autoscaler
    - The part to the right of `0` on the x-axis is the deciding factor for the action taken by the autoscaler 


- To run/test the program
    1. Create a VM in Virtual Machine Manager and put the `server.py` code in it.
    2. Configure the VM to autostart the `server.py` program as soon as the OS boots.
    3. Create extra VM and follow a proper naming convention. The numbering should start from 0
        - Example: `AnyPrefix-0000`, `AnyPrefix-0001`
    4. Launch the first VM - `AnyPrefix-0000`
    5. Open terminal and run `client.py`, `autoscaler.py`
    7. View the realtime graph plotted by the `autoscaler.py` to get an insight into the working of the autoscaler

### Useful Commands

```sh
# virsh is the main interface for managing virsh guest domains.
virsh -V
virsh -c qemu:///system list   # connect locally as root to the daemon supervising QEMU and KVM domains
virsh -c qemu:///session list  # connect locally as a normal user to his own set of QEMU and KVM domains

# ---

# libvirt internals
cd /var/lib/libvirt
ls -l images
ls -l /etc/libvirt/libvirt.conf
cp /etc/libvirt/libvirt.conf ~/.config/libvirt/

# ---

# Network commands
virsh dumpxml ubuntu18.04
virsh net-list
virsh net-dhcp-leases default
virsh domifaddr ubuntu18.04-1
route

```


### References

- **Installation**
    - https://help.ubuntu.com/community/KVM/Installation
      ```sh
      # Commands used on Linux Mint 20
      sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager
      sudo adduser `id -un` libvirt  # sudo adduser $USER libvirt  # sudo usermod -aG libvirt $USERNAME
      sudo adduser `id -un` kvm      # sudo adduser $USER kvm      # sudo usermod -aG kvm $USERNAME

      # Probably reboot/restart needed

      # Check the installation
      virsh -c qemu:///system list
      sudo ls -la /var/run/libvirt/libvirt-sock
      ls -l /dev/kvm
      service libvirtd status
      ```
    - To install libvirt python library in virtual environment/conda
        - https://stackoverflow.com/questions/45473463/pip-install-libvirt-python-fails-in-virtualenv
            - `sudo apt-get install libvirt-dev`
        - https://pypi.org/project/libvirt-python/
            - `pip install libvirt-python`
    - https://unix.stackexchange.com/questions/599651/whats-the-purpose-of-kvm-libvirt-and-libvirt-qemu-groups-in-linux
- **Introduction**
    - https://ubuntu.com/server/docs/virtualization-libvirt
    - https://youtu.be/qr3d-4ctZk4
    - https://youtu.be/HfNKpT2jo7U
    - https://youtu.be/6435eNKpyYw
- **libvirt**
    - https://libvirt.org/docs.html
    - https://libvirt.org/downloads.html
    - https://libvirt.org/html/index.html (Good)
    - https://libvirt.org/html/libvirt-libvirt-domain.html (Good)
- **Client Server Programming**
    - https://uynguyen.github.io/2018/04/30/Big-Endian-vs-Little-Endian/
    - https://stackoverflow.com/questions/21017698/converting-int-to-bytes-in-python-3
        - https://docs.python.org/2/library/struct.html#struct.pack
    - https://stackoverflow.com/questions/34009653/convert-bytes-to-int
    - https://www.geeksforgeeks.org/python-convert-string-to-bytes/
    - https://tutorialedge.net/python/udp-client-server-python/
        - https://www.geeksforgeeks.org/udp-server-client-implementation-c/
        - https://stackoverflow.com/questions/1593946/what-is-af-inet-and-why-do-i-need-it
    - https://www.studytonight.com/network-programming-in-python/working-with-udp-sockets
    - https://pythontic.com/modules/socket/udp-client-server-example
- **Other references**
    - https://www.machinelearningplus.com/python/python-logging-guide/
    - https://stackoverflow.com/questions/40468370/what-does-cpu-time-represent-exactly-in-libvirtvirsh
    - https://stackoverflow.com/questions/19057915/libvirt-fetch-ipv4-address-from-guest
    - https://unix.stackexchange.com/questions/33191/how-to-find-the-ip-address-of-a-kvm-virtual-machine-that-i-can-ssh-into-it
    - https://www.cyberciti.biz/faq/find-ip-address-of-linux-kvm-guest-virtual-machine/
    - https://github.com/fenilgmehta/CS695-Assignment-2