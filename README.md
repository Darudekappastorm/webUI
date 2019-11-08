# webUI
Webinterface and API to control a CNC machine with the linuxcnc/machinekit software

# Getting started
If you are running this on a beaglebone with machinekit installed then you should be able to run this without issues.
If however you do not have access to machinekit or a beaglebone it is still possible to run the mock variant.

All the dependencies are in the Pipfile so we are going to install them now. 
Run the following commands:
    - pip install pipenv
    - pipenv install 
    - pipenv shell

This should install all dependencies in a virtual environment so that you can run the application with this environment.
Go to the default.ini settings and set mock to true if you do not have a beaglebone with machinekit. 
Set ip_authentication_enabled to false if you are just testing. If you want to use this setting you have to whitelist your ip to be able to control the machine.
Set the host and port to your liking in the .ini file.

If you are all set start the server with: python server.py

# Unit tests
To successfully run the unit tests make sure to either have mock set to true or have linuxcnc running. 
run the unit tests with the following command:

Be warned that these tests will actually move the machine if you decide to run it on a working environment!
The following movements will be done:
  - Home
  - Move x/y/z to 1
  - Move x to 2 at the speed of 10mm/s
  - Move x/y/z to 0
  - Move spindle forwards/backwards and increase/decrease the speed
  - Brake the spindle
  - Turn the spindle off

To run the test type:
  - python -m unittests/test
