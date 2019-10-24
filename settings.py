def init():
    global machinekit_running
    global controller
    global file_queue
    global UPLOAD_FOLDER
    machinekit_running = False
    controller = False
    file_queue = ["smile.nc", "smile.nc"]
    UPLOAD_FOLDER = '/home/machinekit/devel/webUI/files'
