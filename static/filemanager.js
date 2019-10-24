let state = {
    file: null,
    queue: [],
}

const listFilesFromServer = async () => {
    const result = await request(api + "/return_files", "GET");
    if (result === undefined) {
        return;
    }
    document.body.className = `success_no_errors file_manager`;
    state.queue = result.file_queue

    if (state.queue.length > 0) {
        document.body.classList.add("files_in_queue");
        selectFile(state.queue[0]);
    }
    renderQueue();

    document.getElementById("tbody_files").innerHTML = "";
    result.result.map((item, index) => {
        // <td><button class="primary" onclick="selectFile('${item[2] + "/" + item[1]}')">Select</button></td>
        document.getElementById("tbody_files").innerHTML += `
        <tr><td>${item[1]}</td>
        <td><button class="warning" onclick="addToQueue('${item[1]}')">Add to queue</button></td></tr>`;
    });
}

const getFile = () => {
    const fileList = document.getElementById("uploadFile");
    if ("files" in fileList) {
        const file = fileList.files[0];

        if (file.length == 0) {
            appState.errors.push("Please select a file");
            handleErrors();
            return;
        }

        if (!file.name) {
            appState.errors.push("File must have a name.");
            return handleErrors();
        }

        const ext = getFileExt(file.name);

        if (ext === "nc") {
            state.file = file;
            return;
        } else {
            appState.errors.push("Filetype is not allowed. Please select a file with the type '.nc' ");
            return handleErrors();
        }
    }
}

const getFileExt = (file) => {
    const lastDot = file.lastIndexOf(".");
    const ext = file.substring(lastDot + 1);
    return ext;
}

const fUpload = async () => {
    if (state.file == null) {
        appState.errors.push("Please select a file");
        return handleErrors();
    }
    let formData = new FormData();
    formData.append("file", state.file);
    const result = await request(api + "/file_upload", "UPLOAD", formData);

    if (result.errors) {
        appState.errors.push(result.errors);
        handleErrors();
        return;
    }
    listFilesFromServer();
}

const selectFile = async (path) => {
    const result = await request(api + "/open_file", "POST", {
        "path": path
    });
    if (result.errors) {
        appState.errors.push(result.errors);
        return handleErrors();
    }
}

const addToQueue = (file) => {
    document.body.classList.add("files_in_queue");
    state.queue.push(file);
    renderQueue();
}

const removeFromQueue = (index) => {
    state.queue.splice(index, 1);
    renderQueue();
}

const renderQueue = () => {
    document.getElementById("tbody_queue").innerHTML = "";
    state.queue.map((value, index) => {
        document.getElementById("tbody_queue").innerHTML += `<tr id="${value}" class="test"><td>${value}</td><td><button class="error" onclick="removeFromQueue(${index})">remove</button></td></tr>`;
    });
}

const getNewQueue = async () => {
    state.queue = [];
    let elements = document.getElementsByClassName("test");
    for (let i = 0; i < elements.length; i++) {
        state.queue.push(elements.item(i).id);
    }
    await request(api + "/update_file_queue", "POST", {
        "new_queue": state.queue
    });

    listFilesFromServer();
}