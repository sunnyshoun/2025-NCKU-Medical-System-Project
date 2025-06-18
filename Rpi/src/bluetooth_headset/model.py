class Device:
    def __init__(self, device_name: str, mac_address: str):
        self.device_name = device_name
        self.mac_address = mac_address
    
    def __eq__(self, other):
        if not isinstance(other, Device):
            return False
        return self.mac_address == other.mac_address