class Request {
    api = "http://192.168.1.116:5000";
    api_key = "test_secret";

    get(url) {
        return fetch(this.api + url, {
                method: "GET",
                headers: {
                    "API_KEY": this.api_key
                }
            })
            .then((response) => response.json())
            .then((data) => data)
            .catch((err) => console.log(err));
    }
    post(url, data) {
        return fetch(this.api + url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "API_KEY": this.api_key,
                },
                mode: "cors",
                body: JSON.stringify(data)
            })
            .then((response) => response.json())
            .then((data) => data)
            .catch((err) => console.log(err));
    }
    update() {

    }
}

class Machinekit {
    state = {}
    displayedErrors = [];
    page = "controller";
    interval = 2000;
    isIntervalRunning = false;
    saveState = 1;
    constructor() {
        this.request = new Request();
        this.controlInterval();
    }

    async getMachineVitals() {
        const result = await this.request.get("/machinekit/status");
        if ("errors" in result) {
            return this.errorHandler(result.errors);
        }
        this.state = result;

        this.buildControllerPage();
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
                task_mode
            },
            spindle: {
                spindle_speed,
                spindle_brake,
                spindle_direction
            },
            position
        } = this.state;
        document.body.className = "controller no-critical-errors";

        if (file) {
            document.getElementById("current-file").innerHTML = file;
            document.body.classList.add("file-selected");

        } else {
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

        switch (interp_state) {
            case "INTERP_IDLE":
                document.body.classList.add("interp-idle");
                break;
            case "INTERP_PAUSED":
                document.body.classList.add("interp-paused");
                break;
            case "INTERP_WAITING":
                document.body.classList.add("interp-waiting");
                break;
            case "INTERP_READING":
                document.body.classList.add("interp-reading");
                break;
        }

        switch (task_mode) {
            case "MODE_MDI":
                document.body.classList.add("mode-mdi");
                break;
            case "MODE_MANUAL":
                document.body.classList.add("mode-manual");
                break;
            case "MODE_AUTO":
                document.body.classList.add("mode-auto");
                break;
        }

        document.getElementById("spindle-speed").innerHTML = spindle_speed;
        let axesHomed = 0;
        const totalAxes = Object.keys(position).length;

        if (totalAxes === 3) {
            for (const axe in position) {
                let homed = "";
                let color = "error";
                if (position[axe].homed) {
                    homed = " (H)";
                    color = "success";
                    axesHomed++;
                }
                if (axe == "x") {
                    document.getElementById("x-axe").innerHTML = position[axe].pos + homed;
                    document.getElementById("x-axe").className = color;
                } else if (axe == "y") {
                    document.getElementById("y-axe").innerHTML = position[axe].pos + homed;
                    document.getElementById("y-axe").className = color;
                } else {
                    document.getElementById("z-axe").innerHTML = position[axe].pos + homed;
                    document.getElementById("z-axe").className = color;
                }
            }
        } else {
            console.log("render custom table for axes");
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

    }

    fileManager() {
        console.log("Render the file manager");
        document.body.className = "filemanager no-critical-errors";
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
        if (error.status == 403) {
            console.log("slowing interval. User not authorized");
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
        console.log(page);
        localStorage.setItem("page", page);
        this.page = page;

        if (page == "controller") {
            this.getMachineVitals();
        } else {
            this.fileManager();
        }
    }

    controlInterval() {
        if (!this.isIntervalRunning) {
            this.isIntervalRunning = true;
        }
        if (this.page == "controller") {
            this.getMachineVitals();
            if (this.saveState == 1) {
                if (this.oldState !== JSON.stringify(this.state.position) && this.oldState != undefined) {
                    this.interval = 200;
                } else {
                    if (this.interval != 2000) {
                        this.interval = 2000;
                    }
                }
                this.oldState = JSON.stringify(this.state.position);
                this.saveState = 0;
            }
            this.saveState++;
        }
        console.log(this.interval);
        setTimeout(this.controlInterval.bind(this), this.interval)
    }

    /*ALL BUTTON CLICK HANDLERS*/
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
}

let machinekit = new Machinekit();