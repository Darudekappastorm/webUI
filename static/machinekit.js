window.onload = async () => {
  timer();
  setInterval(() => {
    timer();
  }, 5000);
  
  const sortable = new Sortable.default(document.querySelectorAll('tbody'), {
    draggable: 'tr'
  });
  sortable.on('sortable:stop', () => {});
};

const api = "http://192.168.1.116:5000";

let machinekit_state = {
  power: {
    enabled: true,
    estop: false
  }
};

let appState = {
  isTimerRunning: true,
  test: true,
  firstRender: true,
  isFileManagerFirstRender: true,
  errors: [],
  displayedErrors: [],
  selectedAxe: "x",
  distanceMultiplier: 1,
  speed: 1,
  api_key: "test_secret"
}

const timer = () => {
  if (localStorage.getItem("page") === "file_manager") {
    appState.isTimerRunning = false;
    document.body.classList.add(`file_manager`);
    document.body.classList.remove(`controller`);
    if (appState.isFileManagerFirstRender) {
      listFilesFromServer();
      appState.isFileManagerFirstRender = false;
      handleErrors();
    }
    if (state.queue.length > 0) {
      document.body.classList.add("files_in_queue");
    }
  } else {
    appState.isTimerRunning = true;
  }
  if (!appState.isTimerRunning) {
    return;
  }

  getMachineStatus();
}

const request = (url, type, data = {}) => {
  let header;

  if (type === "POST") {
    header = {
      method: "POST",
      mode: "cors",
      headers: {
        "Content-Type": "application/json",
        "API_KEY": appState.api_key
      },
      body: JSON.stringify(data)
    }
  } else if (type === "GET") {
    header = {
      method: "GET",
      headers: {
        "API_KEY": appState.api_key
      },
    }
  } else {
    header = {
      method: "POST",
      mode: "cors",
      body: data,
      headers: {
        "API_KEY": appState.api_key
      }
    }
  }

  return fetch(url, header)
    .then(response => {
      return response.json();
    })
    .then(data => {
      if (data.errors == "Machinekit is not running please restart machinekit and then the server") {
        document.body.className = `error_machinekit ${localStorage.getItem("page")}`;
        appState.errors = [];
        return;
      } else {
        return data;
      }
    })
    .catch(error => {
      if (error == "TypeError: Failed to fetch") {
        document.body.className = `error_server_down ${localStorage.getItem("page")}`;
        appState.errors = [];
        return;
      }
    });
}

const setPage = (input) => {
  if (localStorage.getItem("page") === input) {
    return;
  }
  localStorage.setItem("page", input);
  navigationHanlder();
}

const navigationHanlder = () => {
  if (localStorage.getItem("page") === "controller") {
    localStorage.setItem("page", "controller");
    timer();
  } else {
    localStorage.setItem("page", "file_manager");
    timer();
  }
}

const getMachineStatus = async () => {
  const status = await request(api + "/status", "GET");
  if (status == undefined) {
    return;
  }
  machinekit_state = status;
  document.body.className = `success_no_errors controller`;

  handleErrors();
  setBodyClasses();
  checkIfAxesAreHomedAndRenderTable();
}

const handleErrors = () => {
  if (appState.errors.length > 0) {
    document.body.classList.add("error_executing");
    appState.errors.map((value, index) => {
      if (!appState.displayedErrors.includes(value)) {
        document.getElementById("custom_errors").innerHTML += `<p class="error" id="error_executing">${value} <button class="error" id="${index}" onclick="deleteError(${index})">close</button></p>`
        appState.displayedErrors.push(value);
      }
    });
  }
}

const deleteError = (element) => {
  let elem = document.getElementById(element);
  elem.parentNode.remove(elem);
}

const checkAndAddClass = (condition, value) => {
  if (condition) {
    document.body.classList.add(value.true);
  } else {
    document.body.classList.add(value.false)
  }
}

const checkIfAxesAreHomedAndRenderTable = () => {
  const {
    position,
  } = machinekit_state;

  if (machinekit_state.program.tool_change === 0) {
    document.getElementById("modaltoggle_warning").checked = true;
  } else {
    document.getElementById("modaltoggle_warning").checked = false;
  }

  let totalAxes = 0;
  let axesHomed = 0;
  for (const key in position) {
    let homed = position[key].homed;
    if (homed) {
      axesHomed++;
    }
    totalAxes++;
  }

  if (totalAxes == 3) {
    document.body.classList.add("standard_xyz_table");
    document.getElementById("tbody_axes").innerHTML = "";
    for (const key in position) {
      let isHomed = "";
      if (position[key].homed) {
        isHomed = "(H)";
      }
      document.getElementById("tbody_axes").innerHTML += `<td>${position[key].pos}${isHomed}</td>`;
    }
  } else {
    document.body.classList.add("custom_table");
    const thead = document.getElementById("c_thead_axes");
    const tbody = document.getElementById("c_tbody_axes");
    const radio = document.getElementById("manual_control_radio_custom");

    thead.innerHTML = "";
    tbody.innerHTML = "";

    for (const key in position) {
      let isHomed = "";
      if (position[key].homed) {
        isHomed = "(H)";
      }
      if (key == "x") {
        thead.insertCell(0).innerHTML = key;
        tbody.insertCell(0).innerHTML = position[key].pos + isHomed;
      } else if (key == "y") {
        thead.insertCell(1).innerHTML = key;
        tbody.insertCell(1).innerHTML = position[key].pos + isHomed;
      } else if (key == "z") {
        thead.insertCell(2).innerHTML = key;
        tbody.insertCell(2).innerHTML = position[key].pos + isHomed;
      } else {
        thead.innerHTML += `<th>${key}</th>`;
        tbody.innerHTML += `<td>${position[key].pos}${isHomed}</td>`;
      }
      if (appState.firstRender) {
        radio.innerHTML += `
        <li>
          <input type="radio" name="radio" id="radiox" data="${key}"
            onclick="manualControlSelector(this)" />
          <label for="radiox">${key}</label>
        </li>`;
      }
    }

  }
  checkAndAddClass(totalAxes === axesHomed, {
    true: "all_homed",
    false: "not_homed"
  });

  appState.firstRender = false;
}

const setBodyClasses = () => {
  const {
    power: {
      enabled,
      estop
    },
    spindle: {
      spindle_brake,
      spindle_direction,
      spindle_enabled,
      spindlerate
    },
    program: {
      interp_state,
      task_mode,
      feedrate,
      file
    },
    values: {
      max_velocity
    }
  } = machinekit_state;

  checkAndAddClass(enabled, {
    true: "power_on",
    false: "power_off"
  });

  checkAndAddClass(estop, {
    true: "estop",
    false: "no_estop"
  });

  let value;

  switch (interp_state) {
    case "INTERP_IDLE":
      value = "INTERP_IDLE";
      break;
    case "INTERP_READING":
      value = "INTERP_READING";
      break;
    case "INTERP_PAUSED":
      value = "INTERP_PAUSED";
      break;
    case "INTERP_WAITING":
      value = "INTERP_WAITING";
      break;
    default:
      break;
  }

  document.body.classList.add(value);


  switch (task_mode) {
    case "MODE_MANUAL":
      value = "MODE_MANUAL";
      break;
    case "MODE_AUTO":
      value = "MODE_AUTO";
      break;
    case "MODE_MDI":
      value = "MODE_MDI";
      break;
    default:
      break;
  }
  document.body.classList.add(value);

  checkAndAddClass(spindle_brake, {
    true: "SPINDLE_BRAKE_ON",
    false: "SPINDLE_BRAKE_OFF"
  });

  if (spindle_direction == -1) {
    document.body.classList.add("SPINDLE_BACKWARD");
  } else {
    document.body.classList.add("SPINDLE_FORWARD");
  }

  checkAndAddClass(spindle_enabled, {
    true: "SPINDLE_ENABLED",
    false: "SPINDLE_DISABLED"
  });

  document.getElementById("feed_override").value = (feedrate * 100);
  document.getElementById("feed_override_output").innerHTML = (feedrate * 100);

  document.getElementById("spindle_override").value = (spindlerate * 100);
  document.getElementById("spindle_override_output").innerHTML = (spindlerate * 100);

  document.getElementById("max_velocity").value = (max_velocity);
  document.getElementById("max_velocity_output").innerHTML = (max_velocity);
  document.getElementById("file").innerHTML = file;
}

const toggleEstop = async () => {
  document.getElementById("toggleEstopBtn").disabled = true;
  setTimeout(function () {
    document.getElementById("toggleEstopBtn").disabled = false;
  }, 1000);

  await request(
    api + "/set_machine_status",
    "POST", {
      command: "estop"
    }
  );
  getMachineStatus();
};

const togglePower = async () => {
  document.getElementById("togglePowerBtn").disabled = true;
  setTimeout(function () {
    document.getElementById("togglePowerBtn").disabled = false;
  }, 1000);

  const result = await request(
    api + "/set_machine_status",
    "POST", {
      command: "power"
    },
  );
  if (result.errors) {
    appState.errors.push(result.errors);
  }
  getMachineStatus();
};

const homeAllAxes = async (data) => {
  let command = {
    "command": "home"
  }
  if (data) {
    command = {
      "command": "unhome"
    }
  }
  const result = await request(api + "/set_home", "POST", command);
  if (result.errors) {
    appState.errors.push(result.errors);
  }
  getMachineStatus();
}

const manualControlSelector = (element) => {
  appState.selectedAxe = element.getAttribute("data");
}

const manualControlDistance = (element, option) => {
  const value = element.value;
  const target = element.id;
  if (option === "distance") {
    appState.distanceMultiplier = value;
    document.getElementById(target + "_output").innerHTML = value;
  } else {
    appState.speed = value;
    document.getElementById(target + "_output").innerHTML = value;
  }

}

const manualControl = async (input, increment) => {
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
  const axeNumber = axeWithNumber[appState.selectedAxe];

  let command = {
    "axes": axeNumber,
    "speed": parseFloat(appState.speed),
    "increment": 0
  }

  if (input == "increment") {
    command.increment = increment * appState.distanceMultiplier;
  } else {
    command.increment = increment * appState.distanceMultiplier;
  }

  const result = await request(api + "/manual", "POST", command);
  if (result.errors) {
    appState.errors.push(result.errors);
  }
  setTimeout(() => {
    getMachineStatus();
  }, 750);
}

const programControl = async (input) => {
  let command = {
    "command": ""
  }
  switch (input) {
    case "start":
      command.command = "start";
      break;
    case "pause":
      command.command = "pause";
      break;
    case "resume":
      command.command = "resume";
      break;
    case "stop":
      command.command = "stop";
      break;
    default:
      break;
  }

  const result = await request(api + "/control_program", "POST", command);
  if (result.errors) {
    appState.errors.push(result.errors);
  }
  getMachineStatus();
}

const spindleControl = async (input) => {
  let command = {
    "command": {
      "spindle_direction": ""
    }
  }
  switch (input) {
    case "forward":
      command.command.spindle_direction = "spindle_forward"
      break;
    case "off":
      command.command.spindle_direction = "spindle_off"
      break;
    case "reverse":
      command.command.spindle_direction = "spindle_reverse"
      break;
    case "brake":
      command = {
        "command": {
          "spindle_brake": ""
        }
      }
      if (machinekit_state.spindle.spindle_brake == 0) {
        command.command.spindle_brake = 1;
      } else {
        command.command.spindle_brake = 0;
      }
      break;
    default:
      break;
  }
  const result = await request(api + "/spindle", "POST", command);
  if (result.errors) {
    appState.errors.push(result.errors);
  }
  getMachineStatus();
}

const spindleSpeedControl = async (input) => {
  let command = {
    "command": {
      "spindle_direction": ""
    }
  }
  if (input == "increment") {
    command.command.spindle_direction = "spindle_increase";
  } else {
    command.command.spindle_direction = "spindle_decrease";
  }
  const result = await request(api + "/spindle", "POST", command);
  if (result.errors) {
    appState.errors.push(result.errors);
  }
  getMachineStatus();
}

const controlFeedOverride = async (element) => {
  const value = (element.value / 100);
  const target = element.id;
  document.getElementById(target + "_output").innerHTML = element.value;
  if (target == "feed_override") {
    const result = await request(api + "/feed", "POST", {
      "feedrate": value
    });
    if (result.errors) {
      appState.errors.push(result.errors);
    }
  } else if (target == "spindle_override") {
    const result = await request(api + "/spindle", "POST", {
      "command": {
        "spindle_override": value
      }
    });
    if (result.errors) {
      appState.errors.push(result.errors);
    }
  } else {
    const result = await request(api + "/maxvel", "POST", {
      "velocity": value * 100
    });
    if (result.errors) {
      appState.errors.push(result.errors);
    }
  }

  getMachineStatus();
}

const sendMdiCommand = async () => {
  const command = document.getElementById("mdi_command_input").value.toUpperCase();

  const result = await request(api + "/send_command", "POST", {
    "mdi_command": command
  });

  if (result.errors) {
    appState.errors.push(result.errors);
  }

  setTimeout(() => {
    getMachineStatus();
  }, 750);
}

const nav = (ipage) => {
  page = ipage;
  getMachineStatus();
}

const toolChanged = async () => {
  const result = await request(api + "/tool_change", "GET");
  getMachineStatus();
}