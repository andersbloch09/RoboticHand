import sys
from pathlib import Path
from motor_MX_64 import MX_64 as Motor
from dynamixel_sdk import PortHandler, Protocol2PacketHandler as PacketHandler

class Controller:

    # Serial configuration settings
    BAUD_RATE = 9600
    PORT_USB = '/dev/ttyUSB0'

    # Communication protocol settings
    COMM_SUCCESS = 0
    port_Handler: PortHandler = None
    packet_Handler: PacketHandler = None
    # Motor control settings
    motors:dict[int,Motor] = {}

    def __init__(self, n_motors: int, port = PORT_USB, baud_rate = BAUD_RATE) -> None:
        self.n_motors = n_motors
        
        if not self.begin(port, baud_rate):
            print("[ERROR]: Failed to initialize the controller!")
            sys.exit()
        
    # Serial communication setup
    def begin(self, port = PORT_USB, baud_rate = BAUD_RATE) -> bool:
        if self.port_Handler is not None and self.port_Handler.is_open():
            self.port_Handler.closePort()
        
        self.port_Handler = PortHandler(port)
        self.packet_Handler = PacketHandler()

        if not self.port_Handler.openPort():
            print("[ERROR]: Failed to open the port!")
            sys.exit()
        if not self.port_Handler.setBaudRate(baud_rate):
            print("[ERROR]: Failed to set the baud rate!")
            sys.exit()
        if not self.find_motors():
            print("[ERROR]: Failed to find motors!")
            sys.exit()
        
        print(f"[INFO]: Port {port} opened and baud rate {baud_rate} set successfully.")
        return True
    
    # Motor discovery and initialization
    def find_motors(self) -> bool:
        while len(self.motors) < self.n_motors:
            dxl_data_list, _ = self.packet_Handler.broadcastPing(self.port_Handler)
            # Get the path to the JSON config file relative to this file
            json_path = str(Path(__file__).parent / "DynamixelJSON/MX64.json")
            self.motors = {dxl_id: Motor(dxl_id, self, 
                            json_path, 
                            protocol=2, control_table_protocol=None) for dxl_id in sorted(dxl_data_list.keys())}

            if self.motors:
                print(f"[INFO]: Found motor IDs {list(self.motors.keys())}.")
            else:
                print("[WARNING]: No motors found. Retrying...")
        return True
    
    def __check_error(self, protocol, dxl_comm_result, dxl_error):
        """Prints the error message when not successful"""
        if dxl_comm_result != self.COMM_SUCCESS:
            print("%s" % self.packet_Handler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("%s" % self.packet_Handler.getRxPacketError(dxl_error))

    def write_control_table(self, protocol, dxl_id, value, address, size):
        """Writes a specified value to a given address in the control table"""
        dxl_comm_result = 0
        dxl_error = 0

        # the following has to be done inelegantly due to the dynamixel sdk having separate functions per packet size.
        # future versions of this library may replace usage of the dynamixel sdk to increase efficiency and remove this
        # bulky situation.
        if size == 1:
            dxl_comm_result, dxl_error = self.packet_Handler.write1ByteTxRx(self.port_Handler, dxl_id,
                                                                                          address, value)
        elif size == 2:
            dxl_comm_result, dxl_error = self.packet_Handler.write2ByteTxRx(self.port_Handler, dxl_id,
                                                                                          address, value)
        elif size == 4:
            dxl_comm_result, dxl_error = self.packet_Handler.write4ByteTxRx(self.port_Handler, dxl_id,
                                                                                          address, value)
        self.__check_error(protocol, dxl_comm_result, dxl_error)

    def read_control_table(self, protocol, dxl_id, address, size):
        """Returns the held value from a given address in the control table"""
        ret_val = 0
        dxl_comm_result = 0
        dxl_error = 0

        # the following has to be done inelegantly due to the dynamixel sdk having separate functions per packet size.
        # future versions of this library may replace usage of the dynamixel sdk to increase efficiency and remove this
        # bulky situation.
        if size == 1:
            ret_val, dxl_comm_result, dxl_error = self.packet_Handler.read1ByteTxRx(self.port_Handler,
                                                                                                  dxl_id, address)
        elif size == 2:
            ret_val, dxl_comm_result, dxl_error = self.packet_Handler.read2ByteTxRx(self.port_Handler,
                                                                                                  dxl_id, address)
        elif size == 4:
            ret_val, dxl_comm_result, dxl_error = self.packet_Handler.read4ByteTxRx(self.port_Handler,
                                                                                                  dxl_id, address)
        self.__check_error(protocol, dxl_comm_result, dxl_error)
        return ret_val