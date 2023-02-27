# DiffCSP on Android Emulators

## Prerequisite
1. `Python` (3 are supported).
2. The current logged user must have kvm permission (https://stackoverflow.com/questions/37300811/android-studio-dev-kvm-device-permission-denied)

## How to install
1. Run the following script to accept all the licenses.
```shell
./cmdline-tools/latest/bin/sdkmanager --licenses
```

2. Next, run the following script to update the command line tools

```shell
./cmdline-tools/latest/bin/sdkmanager --update
```

3. After that, run the following script to download the necessary packages
```shell
./cmdline-tools/latest/bin/sdkmanager platform-tools emulator
```

4. Finally, we need to run the following script to create the emulators.

```shell
python cmd-emulators.py -method init -num_devices 30
```

| Parameter  | Description |
| ------------- | ------------- |
| -method  | init  |
| -num_devices  | The numbers of emulator devices |

## How to run the test
1. First, we now start our emulators up by the following script.

```shell
python cmd-emulators.py -method start -num_devices 30
```
| Parameter  | Description |
| ------------- | ------------- |
| -method  | start  |
| -num_devices  | The number of emulators devices should be less than or equal to the number of devices created in the initialization step.|

2. Second, we install the mobile browser app that we need to test. The following script shows how to install the Firefox browser app.

```shell
python cmd-emulators.py -method install -apk_file fenix-98.2.0-x86.apk -package_name org.mozilla.firefox
```

| Parameter  | Description |
| ------------- | ------------- |
| -method  | install  |
| -apk_file  | The path to the apk file of the browser app  |
| -package_name  | The package name of the browser app  |

3. Third, following the instruction to setup the client and the servers.
