import {
    Request
} from "./request.js";


window.onload = async () => {
    new Sortable.default(document.getElementById('tbody_queue'), {
        draggable: 'tr'
    });

}
export class Machinekit {
    state = {}
    displayedErrors = [];
    page = "controller";

    slowInterval = 2000
    fastInterval = 200;
    interval = 100;

    file_queue = [];
    local_file_queue = [];
    files_on_server = [];
    firstConnect = true;

    constructor() {
        this.request = new Request();
        this.getFilesFromServer();
        this.controlInterval();
    }

    controlInterval() {
        if (document.readyState != "loading") {
            if (this.page == "controller") {
                this.getMachineVitals();
            }
        }
        setTimeout(this.controlInterval.bind(this), this.interval)
    }

    async getMachineVitals() {
        const result = await this.request.get("/machinekit/status");
        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }
        const isSameState = this.controlintervalSpeedAndCompareStates(result);
        this.state = result;

        //Only update the page classes if the states are not exactly the same
        if (!isSameState) {
            this.buildControllerPage();
        }
    }

    controlintervalSpeedAndCompareStates(result) {
        //On first connect there is nothing to compare
        if (this.firstConnect) {
            if (this.file_queue.length > 0) {
                this.request.post("/machinekit/open_file", {
                    "name": this.file_queue[0]
                });
            } else {
                this.request.post("/machinekit/open_file", {
                    "name": ""
                });
            }
            this.firstConnect = false;
        } else {
            //Compare if state of axes is same. If not machine is moving so we want faster data
            const oldState = JSON.stringify(this.state.position);
            const newState = JSON.stringify(result.position);

            if (oldState === newState) {
                if (this.interval != this.slowInterval) {
                    this.interval = this.slowInterval
                }
            } else {
                this.interval = this.fastInterval;
            }
            /*
                Check if in the previous state the machine was running a program vs if it is done now.
                If it is done now remove 1 item from the queue and open the next item in the queue
            */
            if (this.state.program.rcs_state != result.program.rcs_state) {
                if (result.program.rcs_state === "RCS_DONE") {
                    //Remove last item from the queue
                    this.file_queue.splice(0, 1);
                    //Update the queue on the server
                    this.request.post("/server/update_file_queue", {
                        "new_queue": this.file_queue
                    });
                    //Select the first item
                    let file = this.file_queue[0];
                    if (!file) {
                        file = "";
                    }
                    //Open the first item on the machine
                    this.request.post("/machinekit/open_file", {
                        "name": file
                    });
                }
            }

            if (!this.state.program.file && this.file_queue.length > 0) {
                this.request.post("/machinekit/open_file", {
                    "name": this.file_queue[0]
                });
            }
        }

        const wholeState = JSON.stringify(this.state);
        const wholeNewState = JSON.stringify(result);
        return (wholeState === wholeNewState);
    }

    buildControllerPage() {
        const {
            power: {
                enabled,
                estop
            },
            program: {
                file,
                interp_state,
                task_mode,
                feedrate,
                rcs_state,
                tool_change
            },
            spindle: {
                spindle_speed,
                spindle_brake,
                spindle_direction,
                spindlerate,
                spindle_enabled
            },
            values: {
                velocity
            },
            position
        } = this.state;
        document.body.className = "controller no-critical-errors";

        if (tool_change === 0) {
            document.getElementById("modaltoggle-warning").checked = true;
            document.body.classList.add("tool-change");
        } else {
            document.getElementById("modaltoggle-warning").checked = false;
        }

        if (file) {
            document.getElementById("current-file").innerHTML = file;
            document.body.classList.add("file-selected");
        } else {
            document.getElementById("current-file").innerHTML = "";
            document.body.classList.add("no-file-selected");
        }

        if (enabled) {
            document.body.classList.add("power-on");
        } else {
            document.body.classList.add("power-off");
        }

        if (estop) {
            document.body.classList.add("estop-enabled");
        } else {
            document.body.classList.add("estop-disabled");
        }

        document.body.classList.add(interp_state.toLowerCase().replace("_", "-"));
        document.body.classList.add(task_mode.toLowerCase().replace("_", "-"));
        document.body.classList.add(rcs_state.toLowerCase().replace("_", "-"));


        document.getElementById("spindle-speed").innerHTML = spindle_speed;
        let axesHomed = 0;
        const totalAxes = Object.keys(position).length;

        for (const axe in position) {
            let homed = "";
            let color = "error";
            if (position[axe].homed) {
                homed = " (H)";
                color = "success";
                axesHomed++;
            }

            document.getElementsByClassName(axe + "-axe")[0].style.display = "flex";
            document.getElementById(axe + "-axe").innerHTML = position[axe].pos + homed;
            document.getElementById(axe + "-axe").className = color;

        }

        if (totalAxes === axesHomed) {
            document.body.classList.add("homed");
        } else {
            document.body.classList.add("unhomed");
        }

        if (spindle_brake) {
            document.body.classList.add("spindle-brake-engaged");
        } else {
            document.body.classList.add("spindle-brake-disengaged");
        }

        if (spindle_direction == 1) {
            document.body.classList.add("spindle-forward");
        } else if (spindle_direction == -1) {
            document.body.classList.add("spindle-reverse");
        } else {
            document.body.classList.add("spindle-not-moving");
        }

        if (spindle_enabled) {
            document.body.classList.add("spindle-enabled");
        } else {
            document.body.classList.add("spindle-disabled");
        }
        document.getElementById("feed-override").value = Math.round((feedrate * 100));
        document.getElementById("feed-override-output").innerHTML = Math.round((feedrate * 100));

        document.getElementById("spindle-override").value = Math.round((spindlerate * 100));
        document.getElementById("spindle-override-output").innerHTML = Math.round((spindlerate * 100));

        document.getElementById("max-velocity").value = Math.round((velocity * 60));
        document.getElementById("max-velocity-output").innerHTML = Math.round((velocity * 60));
    }

    async getFilesFromServer() {
        const result = await this.request.get("/server/files");
        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }

        this.file_queue = result.file_queue;
        this.files_on_server = result.result;
    }

    async fileManager() {
        document.body.className = "filemanager no-critical-errors";
        await this.getFilesFromServer();
        this.buildFileManagerPage();
    }

    buildFileManagerPage() {
        document.getElementById("tbody_files").innerHTML = "";

        //Render all files from the server
        if (this.files_on_server.length > 0) {
            this.files_on_server.map((item, index) => {
                document.getElementById("tbody_files").innerHTML +=
                    `
                <tr>
                    <td>${item[1]}</td>
                    <td>
                        <button class="warning" onclick="machinekit.addFilesToQueue('${item[1]}')">Add to queue</button>
                    </td>
                </tr>`;
            });
        }

        //Render file_queue
        if (this.file_queue.length > 0) {
            document.getElementById("tbody_queue").innerHTML = "";
            this.file_queue.map((value, index) => {
                document.getElementById("tbody_queue").innerHTML +=
                    `<tr id="${value}" class="test">
                        <td>${value}</td>
                        <td><button class="error" onclick="machinekit.removeFileFromQueue(${index})">remove</button></td>
                    </tr>`;
            });
        }
    }

    errorHandler(error) {
        if (this.displayedErrors.includes(error.message)) {
            return;
        }
        if (error.message == "Machinekit is not running please restart machinekit and then the server!") {
            this.interval = 50000;
            document.body.className = "machinekit-down"
            return;
        }

        if (error.message == "Failed to fetch") {
            this.interval = 50000;
            document.body.className = "server-down";
            return;
        }
        if (error.status == 403) {
            this.interval = 50000;
            document.body.className = "not-authorized"
            return;
        }

        this.displayedErrors.push(error.message);
        this.renderErrors();
    }

    renderErrors() {
        const errorElement = document.getElementById("runtime-errors");
        errorElement.innerHTML = "";
        this.displayedErrors.map((value, index) => {
            errorElement.innerHTML += `<p class="error" id="error_executing">${value}<button class="error" id="error-${index}" onclick="machinekit.deleteError(${index})">x</button></p>`;
        });
    }

    deleteError(index) {
        this.displayedErrors.splice(index, 1);
        this.renderErrors();
    }

    navigation(page) {
        if (page == "controller") {
            this.state.page = "controller";
            this.page = "controller";
            this.getMachineVitals();
        } else {
            this.state.page = "filemanager";
            this.page = "filemanager";
            this.fileManager();
        }
    }


    async clickHandler(url, command) {
        let result;
        if (command == "MDI") {
            result = await this.request.post(url, {
                "command": document.getElementById("mdi-command-input").value
            });
            this.interval = 200;
        } else {
            result = await this.request.post(url, {
                "command": command
            });
        }
        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }
        this.getMachineVitals();
    }

    async controlOverrides(element, url) {
        let value;
        const target = element.id;
        if (target == "max-velocity") {
            value = element.value;
        } else {
            value = (element.value / 100);
        }
        document.getElementById(target + "-output").innerHTML = element.value;

        const result = await this.request.post(url, {
            "command": value
        });

        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }
        this.getMachineVitals();
    }

    async manualControl(input, increment, selectedAxe = null) {
        //Convert axename to number
        const axeWithNumber = {
            x: 0,
            y: 1,
            z: 2,
            a: 3,
            b: 4,
            c: 5,
            u: 6,
            v: 7,
            w: 8
        }
        let axeNumber;
        if (selectedAxe === null) {
            axeNumber = 0;
        } else {
            axeNumber = axeWithNumber[selectedAxe]
        }


        //Object that contains the axenumber, the speed at which it should move and the incrementation.
        let command = {
            "axes": axeNumber,
            "speed": 10,
            "increment": increment
        }
        const result = await this.request.post("/machinekit/position/manual", command);

        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }
        this.getMachineVitals();
    }

    addFilesToQueue(file) {
        this.file_queue.push(file);
        this.renderFileQueue();
    }

    renderFileQueue() {
        document.getElementById("tbody_queue").innerHTML = "";
        this.file_queue.map((value, index) => {
            document.getElementById("tbody_queue").innerHTML +=
                `<tr id="${value}" class="test">
                        <td>${value}</td>
                        <td><button class="error" onclick="machinekit.removeFileFromQueue(${index})">remove</button></td>
                    </tr>`;
        });
    }

    removeFileFromQueue(index) {
        this.file_queue.splice(index, 1);
        this.renderFileQueue();
    }

    getFileForUpload() {
        const fileList = document.getElementById("uploadFile");
        if ("files" in fileList) {
            const file = fileList.files[0];

            if (file == undefined) {
                return this.errorHandler({
                    "message": "Please select a file"
                });
            }

            if (!file.name) {
                return this.errorHandler({
                    "message": "File name cannot be empty"
                });
            }
            const lastDot = file.name.lastIndexOf(".");
            const ext = file.name.substring(lastDot + 1);

            if (ext === "nc" || ext === "gcode") {
                this.file = file;

                return;
            } else {
                return this.errorHandler({
                    "message": "Filetype is not allowed. Please select a file with one of the following types: '.nc, .gcode'"
                });
            }
        }
    }

    async uploadFile() {
        if (this.file == null) {
            return this.errorHandler({
                "message": "Please select a file"
            });
        }
        let formData = new FormData();
        formData.append("file", this.file);

        const result = await this.request.upload("/server/file_upload",
            formData
        );

        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }

        this.getMachineVitals();
    }

    async updateFileQueueOnServer() {
        this.file_queue = [];
        let elements = document.getElementsByClassName("test");

        for (let i = 0; i < elements.length; i++) {
            this.file_queue.push(elements.item(i).id);
        }
        const result = await this.request.post("/server/update_file_queue", {
            "new_queue": this.file_queue
        });
        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }
        this.buildFileManagerPage();
    }

    async toolChange() {
        const result = await this.request.get("/machinekit/toolchange");
        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }
        this.buildFileManagerPage();
    }
}