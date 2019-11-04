def init():
    global machinekit_running
    global controller
    global file_queue
    machinekit_running = False
    controller = None
    file_queue = []
