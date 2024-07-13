
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
