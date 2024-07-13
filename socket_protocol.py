serverSocket = socket.socket()
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

serverSocket.bind(("0.0.0.0", ROBOT_SOCKET_PORT))
serverSocket.listen(5)

while not state.stop_threads:
    try:
        if state.robotInfo["is_simulated"] or not autoconnect_enabled or autoconnect.wifi_connected:   
            clientConnection, clientAddress = serverSocket.accept() # Execution will stop here until something is received.
            data_received = False
            while not state.stop_threads and not data_received:
                data, binary_mode = recv_msg(clientConnection)
                data_received = True                    
                reply = None
                function_name = None
                
                if binary_mode == 0: # JSON command
                    function_name = data['function']
                    parameters = data['parameters']
                elif binary_mode == 1: # Connection ckeck
                    pass
                elif binary_mode == 2:
                    function_name = "binarytestA" 
                    parameters = [data]
                elif binary_mode == 3:
                    function_name = "binarytestB" 
                    parameters = [data]
                elif binary_mode == 10:
                    function_name = "receiveFile" 
                    parameters = [data]
                else:
                    printerr("Message received with unknown binary mode.")

                if function_name:
                    try:
                        reply = getattr(nao_comp, function_name)(*parameters)
                    except AttributeError as e:
                        traceback.print_exc()
                        printerr("ERROR: function " + function_name + " not found")
                    #mutexSocket.acquire()
                    send_msg(clientConnection, reply)
                    #mutexSocket.release()
    except IOError as e:
        if e.errno != errno.EINTR:
            printerr(exception=e)
        #else:
        #    printerr(exception=e)
    except Exception as e:
        printerr(exception=e)


serverSocket.close()

def send_msg(sock, msg, binary_mode=0):
    m = msg
    if binary_mode == 0:
        # Serializing the message to JSON and then encoding it to UTF-8
        m = json.dumps(msg).encode('utf-8')
    # Prefix each message with a 5-byte length (network byte order)
    m = struct.pack('>IB', len(m), binary_mode) + m
    sock.sendall(m)


def recv_msg(sock):
    # Read message length and unpack it into an integer
    header = recvall(sock, 5)
    if not header:
        return None, None
    msglen, binary_mode = struct.unpack('>IB', header)
    # Read the message data
    data = recvall(sock, msglen)
    if data is None:
        return data, binary_mode
    if binary_mode == 0: # JSON mode (not binary)
        data = json.loads(data.decode('utf-8'))
    return data, binary_mode


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    verb = False
    if n >= MIN_BYTES_TO_PRINT_PROGRESS:
        verb = True
    data = bytearray()
    bytes_processed = 0
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            if verb:
                print("\n")
            return None
        if verb:
            bytes_processed = bytes_processed + len(data)
            print("Received " + str(bytes_processed) + " / " + str(n) + " bytes\r"),  # The comma avoids the final newline. \r Returns to the start of the line.
        data.extend(packet)
    if verb:
        print("\n")
    return data
