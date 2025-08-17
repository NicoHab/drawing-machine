import serial
import time

def test_virtual_ports():
    """Test that COM10 and COM11 are connected"""
    try:
        print("Testing virtual serial ports COM20 ⟷ COM21...")
        
        # Open both ports
        port1 = serial.Serial('COM20', 9600, timeout=2)
        port2 = serial.Serial('COM21', 9600, timeout=2)
        
        print("✅ Both ports opened successfully")
        
        # Send data from port1 to port2
        test_message = b"Hello Virtual Ports!"
        print(f"Sending: {test_message.decode()}")
        
        port1.write(test_message)
        port1.flush()
        
        # Read from port2
        received = port2.read(len(test_message))
        print(f"Received: {received.decode()}")
        
        port1.close()
        port2.close()
        
        if received == test_message:
            print("✅ Virtual serial ports working correctly!")
            return True
        else:
            print("❌ Virtual serial ports not working correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ports: {e}")
        return False

if __name__ == "__main__":
    test_virtual_ports()