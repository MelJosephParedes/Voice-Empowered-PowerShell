import subprocess
import os
DEFAULT_PATH = "C:\\Users\\meljo"

#print(f"Current working directory: {os.getcwd()}")

def run_powershell_command(command):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True
        )

        # Debugging outputs
        print(f"[DEBUG] STDOUT: {result.stdout.strip()}")
        print(f"[DEBUG] STDERR: {result.stderr.strip()}")
        print(f"[DEBUG] Exit code: {result.returncode}")

        # If STDOUT contains data, return it, even if exit code is non-zero
        if result.stdout.strip():
            return result.stdout.strip()

        # If no output and exit code is non-zero, handle it as an error
        if result.returncode != 0:
            print(f"[DEBUG]PowerShell command failed with exit code {result.returncode}")
            return None

        return result.stdout.strip()

    except Exception as e:
        print(f"Error in run_powershell_command: {e}")
        return None


def recurse_dir(name):
    try:
        # File containing the base path
        current_path_file = os.path.abspath("current_path.txt")

        # Ensure the file exists
        if not os.path.exists(current_path_file):
            print(f"Error: '{current_path_file}' not found.")
            return None

        # Read the base path from the file
        with open(current_path_file, 'r') as f:
            base_path = f.read().strip()

        if not base_path:
            print("Error: Base path in 'current_path.txt' is empty.")
            return None

        # Ensure the base path uses correct slashes and is quoted
        base_path = base_path.replace("/", "\\")  # Convert forward slashes to backslashes
          # Quote the path for PowerShell compatibility

        # Properly format the base path
        base_path = base_path.replace("/", "\\")  # Use backslashes
        base_path = f'"{base_path}"'  # Add quotes for PowerShell

        # Construct the PowerShell command with error handling
        command = (f'Get-ChildItem -Recurse -Directory -Filter "{name}" '
                   f'-Path {base_path} -ErrorAction SilentlyContinue | '
                   f'Select-Object -ExpandProperty FullName')

        # Debug: Print the generated PowerShell command
        print(f"[DEBUG] Generated PowerShell command: {command}")

        return command

    except Exception as e:
        print(f"Error in recurse_dir: {e}")
        return None


def create_folder(path, name):
    return f'New-Item -Path "{path}" -Name "{name}" -ItemType "Directory"'

def create_file(path, name):
    return f'New-Item -Path "{path}" -Name "{name}" -ItemType "File"'

def open_folder_file(path, name):
    return f'Start-Process "{path}\\{name}"'

def delete_folder(path, name):
    return f'Remove-Item -Path "{path}\\{name}" -Recurse'

def delete_file(path, name):
    return f'Remove-Item -Path "{path}\\{name}"'

def rename_folder_file(path, old_name, new_name):
    return f'Rename-Item -Path "{path}\\{old_name}" -NewName "{new_name}"'

def move_folder_file(path, name, loc):
    return f'Move-Item -Path "{path}\\{name}" -Destination "{loc}"'

def copy_folder_file(path, name, loc):
    return f'Copy-Item -Path "{path}\\{name}" -Destination "{loc}"'

def search_folder_mutiple(name):
    with open('current_path.txt', 'r') as f:
        base_path = f.read().strip()
    return f'Get-ChildItem -Path "{base_path}" -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object {{ $_.Name -like "*{name}*"}} | Select-Object -ExpandProperty FullName'

def search_file_multiple(name):
    with open('current_path.txt', 'r') as f:
        base_path = f.read().strip()
    return f'Get-ChildItem -Path "{base_path}" -Recurse -File -ErrorAction SilentlyContinue | Where-Object {{ $_.Name -like "*{name}*"}} | Select-Object -ExpandProperty Fullname'

def search_folder(name):
    with open('current_path.txt', 'r') as f:
        base_path = f.read().strip()
    
    command = f'Get-ChildItem -Recurse -Directory -Filter "{name}" -Path "{base_path}" -ErrorAction SilentlyContinue |  Select-Object -ExpandProperty FullName'
    print(f"[DEBUG] {command}")
    return command

def search_file(name):
    with open('current_path.txt', 'r') as f:
        base_path = f.read().strip()
    
    command = f'Get-ChildItem -Recurse -File -Filter "{name}" -Path "{base_path}" -ErrorAction SilentlyContinue |  Select-Object -ExpandProperty FullName'
    print(f"[DEBUG] {command}")
    return command

def handle_create_command(current_path, command_parts): 

    dir_loc = None

    if len(command_parts) == 2:
        name = command_parts[1]

    elif len(command_parts) == 3:
        name = command_parts[1]
        dir_loc = command_parts[2]

    if "." in name: # file, working
        if dir_loc:
            
            create_path_output = recurse_dir(dir_loc)
            powershell_create_path = run_powershell_command(f"{create_path_output} | Select-Object -First 1")

            output = powershell_create_path.splitlines()
            output_path = output[0]
            create_file_command = create_file(output_path, name)
            execute_command = run_powershell_command(f"{create_file_command} | Select-Object -First 1")

            print(f'Create File command: {execute_command}')
            print(f'Create File named: {name} in {powershell_create_path}')
            return f'Create file named: {name} in {output_path}'

        else: # working
            create_file_command = create_file(current_path, name)
            execute_command = run_powershell_command(create_file_command)

            print(f'Create File command: {execute_command}')
            print(f'Created file name: {name} in {current_path}')
            return f'Created File named: {name} in {current_path}'
    
    else: #folder 
        if dir_loc: # working
            
            create_path_output = recurse_dir(dir_loc)
            powershell_create_path = run_powershell_command(f"{create_path_output} | Select-Object -First 1")

            output = powershell_create_path.splitlines()
            output_path = output[0]
            create_folder_command = create_folder(output_path, name)
            execute_command = run_powershell_command(f"{create_folder_command} | Select-Object -First 1")

            print(f'Create folder command: {execute_command}')
            print(f'Create folder name: {name} in {powershell_create_path}')
            return f'Create folder name: {name} in {output_path}'

        else: # working
            create_folder_command = create_folder(current_path, name)
            execute_command = run_powershell_command(create_folder_command)

            print(f'create folder command: {execute_command}')
            print(f'Create folder name: {name} in {current_path}')
            return f'Create folder name: {name} in {current_path}'

def handle_open_command(current_path, command_parts):

    dir_loc = None

    if len(command_parts) == 2:
        name = command_parts[1]

    elif len(command_parts) == 3:
        name = command_parts[1]
        dir_loc = command_parts[2]

    if "." in name: # File, working
        if dir_loc:

            open_path_output = recurse_dir(dir_loc)
            powershell_open_path = run_powershell_command(f"{open_path_output} | Select-Object -First 1")

            output = powershell_open_path.splitlines()
            output_path = output[0]
            open_file_path = open_folder_file(output_path, name)
            execute_command = run_powershell_command(f"{open_file_path} | Select-Object -First 1")

            print(f'open command: {execute_command}')
            print(f'open file named: {name} in {powershell_open_path}')
            return f'Open file named : {name} in {output_path}'    
            
        
        else: # working 
            open_file_command = open_folder_file(current_path, name)
            execute_command = run_powershell_command(open_file_command)
            
            print(f'Open command: {execute_command}')
            print(f'open file named: {name} in {current_path}')
            return f'Open file named: {name} in {current_path}'
            
    else: #folder
        if dir_loc: # working

            open_path_output = recurse_dir(dir_loc)
            powershell_open_path = run_powershell_command(f'{open_path_output} | Select-Object -First 1') 

            output = powershell_open_path.splitlines()
            output_path = output[0]
            open_folder_path = open_folder_file(output_path, name)
            execute_command = run_powershell_command(f"{open_folder_path} | Select-Object -First 1")

            print(f'open folder named: {name} in {powershell_open_path}')
            return f'Open folder named: {name} in {output_path}'
            
        else: # working
            open_folder_command = open_folder_file(current_path, name)
            execute_command = run_powershell_command(open_folder_command)

            print(f'open folder named: {name} in {current_path}')
            return f'Open folder named: {name} in {current_path}'

def handle_delete_command(current_path, command_parts):

    dir_loc = None
    if len(command_parts) == 2:

        name = command_parts[1]

    elif len(command_parts) == 3:

        name = command_parts[1]
        dir_loc = command_parts[2]

    if "." in name:
        if dir_loc: # working

            delete_path_output = recurse_dir(dir_loc)
            powershell_delete_path = run_powershell_command(f"{delete_path_output} | Select-Object -First 1")

            output = powershell_delete_path.splitlines()
            output_path = output[0]
            delete_file_path = delete_file(output_path, name)
            execute_command = run_powershell_command(delete_file_path)

            
            print(f'Delete file named: {name} in {powershell_delete_path}')
            return f'Delete file named: {name} in {output_path}'

        else: # working
            delete_file_command = delete_file(current_path, name)
            execute_command = run_powershell_command(delete_file_command)

            print(f'Delete file named: {name} in {current_path}')
            return f'Delete file named: {name} in {current_path}'
        
    else:
        if dir_loc: # working

            delete_path_output = recurse_dir(dir_loc)
            powershell_delete_path = run_powershell_command(f"{delete_path_output} | Select-Object -First 1")

            output = powershell_delete_path.splitlines()
            output_path = output[0]
            delete_folder_path = delete_folder(output_path, name)
            execute_command = run_powershell_command(delete_folder_path)

            print(f'Delete command: {execute_command}')
            print(f'Delete folder named: {name} in {powershell_delete_path}')
            return f'Delete folder named: {name} in {output_path}'

        else: # working
            delete_folder_command = delete_folder(current_path, name)
            run_powershell_command(delete_folder_command)
            
            print(f'Delete folder named: {name} in {current_path}')
            return f'Delete folder named: {name} in {current_path}'

def handle_rename_command(current_path, command_parts):

    dir_loc = None
    if len(command_parts) == 3:
        old_name = command_parts[1]
        new_name = command_parts[2]
    
    elif len(command_parts) == 4:

        old_name = command_parts[1]
        new_name = command_parts[2]
        dir_loc = command_parts[3]

    if "." in old_name:
        if dir_loc: # working

            rename_path_output = recurse_dir(dir_loc)
            powershell_rename_path = run_powershell_command(f"{rename_path_output} | Select-Object -First 1")

            output = powershell_rename_path.splitlines()
            output_path = output[0]
            rename_file_path = rename_folder_file(output_path, old_name, new_name)
            execute_command = run_powershell_command(rename_file_path)

            print(f'Rename file: {old_name} to {new_name} in {powershell_rename_path}')
            return f'Rename file: {old_name} to {new_name} in {output_path}'
        
        else: # working
            rename_file_command = rename_folder_file(current_path, old_name, new_name)
            execute_command = run_powershell_command(rename_file_command)

            print(f'Rename file: {old_name} to {new_name} in {current_path}')
            return f'Rename file: {old_name} to {new_name} in {current_path}'
    
    else: # folder
        if dir_loc: # working

            rename_path_output = recurse_dir(dir_loc)
            powershell_rename_path = run_powershell_command(f"{rename_path_output} | Select-Object -First 1")

            output = powershell_rename_path.splitlines()
            output_path = output[0]
            rename_folder_path = rename_folder_file(output_path, old_name, new_name)
            execute_command = run_powershell_command(rename_folder_path)

            print(f'Rename folder: {old_name} to {new_name} in {powershell_rename_path}')
            return f'Rename folder: {old_name} to {new_name} in {output_path}'
        
        else: # working
            rename_folder_command = rename_folder_file(current_path, old_name, new_name)
            execute_command = run_powershell_command(rename_folder_command)

            print(f'Rename folder: {old_name} to {new_name} in {current_path}')
            return f'Rename folder: {old_name} to {new_name} in {current_path}'

def handle_move_command(current_path, command_parts):

    dir_loc = None
    
    with open('current_path.txt', 'r') as f:
        current_path = f.read().strip()

    if len(command_parts) == 3:
        
        name = command_parts[1]
        destination = command_parts[2]
    
    elif len(command_parts) == 4:
        name = command_parts[1]
        dir_loc = command_parts[2]
        destination = command_parts[3]

    if "." in name: # file 
        if len(command_parts) == 3: # current path: without directory location, working

            move_path_output = recurse_dir(destination)
            powershell_destination_path = run_powershell_command(f"{move_path_output} | Select-Object -First 1")

            move_file_name = move_folder_file(current_path, name, powershell_destination_path) # destination: without directory location
            execute_command = run_powershell_command(move_file_name)

            print(f'Move file named: {name} from {current_path} to {powershell_destination_path}')
            return f'Move file named: {name} from {current_path} to {powershell_destination_path}'

        else: # file, with directory location, working
            
            move_path_output = recurse_dir(dir_loc)
            powershell_move_path = run_powershell_command(f"{move_path_output} | Select-Object -First 1")
            output = powershell_move_path.splitlines()
            output_path = output[0]

            destination_path_output = recurse_dir(destination)
            powershell_destination_output = run_powershell_command(f"{destination_path_output} | Select-Object -First 1")
            output_destination = powershell_destination_output.splitlines()
            output_destination = output_destination[0]

            move_file_name = move_folder_file(output_path, name, output_destination)
            execute_command = run_powershell_command(f"{move_file_name} | Select-Object -First 1")

            print(f'Move file named: {name} from {powershell_move_path} to {destination}')
            return f'Move file named: {name} from {output_path} to {output_destination}'

    else: 
        if len(command_parts) == 3: # folder, without directory location, working
            
            move_path_output = recurse_dir(destination)
            powershell_destination_path = run_powershell_command(move_path_output)

            move_folder_name = move_folder_file(current_path, name, powershell_destination_path) # destination: without directory location
            execute_command = run_powershell_command(move_folder_name)

            print(f'Move folder named: {name} from {current_path} to {destination}')
            return f'Move folder named: {name} from {current_path} to {powershell_destination_path}'
        
        else: # folder, with directory location, working

            move_path_output = recurse_dir(dir_loc)
            powershell_move_path = run_powershell_command(f"{move_path_output} | Select-Object -First 1")
            output = powershell_move_path.splitlines()
            output_path = output[0]

            destination_path_output = recurse_dir(destination)
            powershell_destination_output = run_powershell_command(f"{destination_path_output} | Select-Object -First 1")
            output_destination = powershell_destination_output.splitlines()
            output_destination = output_destination[0]

            move_folder_name = move_folder_file(output_path, name, output_destination)
            execute_command = run_powershell_command(move_folder_name)

            print(f'Move folder named: {name} from {powershell_move_path} to {output_destination}')
            return f'Move folder named: {name} from {output_path} to {output_destination}'

def handle_copy_command(current_path, command_parts):

    dir_loc = None

    with open('current_path.txt', 'r') as f:
        current_path = f.read().strip()

    if len(command_parts) == 3:

        name = command_parts[1]
        destination = command_parts[2]
        
    elif len(command_parts) == 4:
        
        name = command_parts[1]
        dir_loc = command_parts[2]
        destination = command_parts[3]

    if "." in name: # file 
        if len(command_parts) == 3: # current path: without directory location, working

            copy_path_output = recurse_dir(destination)
            powershell_copy_path = run_powershell_command(f"{copy_path_output} | Select-Object -First 1")
            
            copy_file_name = copy_folder_file(current_path, name, powershell_copy_path) # destination: without directory location
            execute_command = run_powershell_command(f"{copy_file_name} | Select-Object -First 1")

            print(f'Copy file named: {name} from {current_path} to {powershell_copy_path}')
            return f'Copy file named: {name} from {current_path} to {powershell_copy_path}'

        else: # file, with directory location, working 
            
            copy_path_output = recurse_dir(dir_loc)
            powershell_copy_path = run_powershell_command(f"{copy_path_output} | Select-Object -First 1")
            output = powershell_copy_path.splitlines()
            output_path = output[0]

            destination_path_output = recurse_dir(destination)
            powershell_destination_output = run_powershell_command(f"{destination_path_output} | Select-Object -First 1")
            output_destination = powershell_destination_output.splitlines()
            output_destination = output_destination[0]

            copy_file_name = copy_folder_file(output_path, name, output_destination)
            execute_command = run_powershell_command(copy_file_name)

            print(f'Copy file named: {name} from {output_path} to {output_destination}')
            return f'Copy file named: {name} from {output_path} to {output_destination}'

    else: 
        if len(command_parts) == 3: # folder, without directory location, working

            copy_path_output = recurse_dir(destination)
            powershell_copy_path = run_powershell_command(f"{copy_path_output} | Select-Object -First 1")
            output_path = powershell_copy_path.splitlines()
            output_destination = output_path[0]

            copy_folder_name = copy_folder_file(current_path, name, output_destination) # destination: without directory location
            execute_command = run_powershell_command(f"{copy_folder_name} -Recurse | Select-Object -First 1")

            print(f'Copy folder named: {name} from {current_path} to {output_destination}')
            return f'Copy folder named: {name} from {current_path} to {output_destination}'
            
        else: # folder, with directory location, working

            copy_path_output = recurse_dir(dir_loc)
            powershell_copy_path = run_powershell_command(f"{copy_path_output} | Select-Object -First 1")
            output = powershell_copy_path.splitlines()
            output_path = output[0]

            destination_path_output = recurse_dir(destination)
            powershell_destination_output = run_powershell_command(f"{destination_path_output} | Select-Object -First 1")
            output_destination = powershell_destination_output.splitlines()
            output_destination = output_destination[0]
            
            copy_folder_name = copy_folder_file(output_path, name, output_destination)
            execute_command = run_powershell_command(f"{copy_folder_name} -Recurse | Select-Object -First 1")

            print(f'Copy folder named: {name} from {output_path} to {output_destination}')
            return f'Copy folder named: {name} from {output_path} to {output_destination}'

def handle_search_command(current_path, command_parts):

    multiple = None    

    if len(command_parts) == 2:
        name = command_parts[1]
    
    elif len(command_parts) == 3:

        name = command_parts[1]
        multiple = command_parts[2]

    with open('paths.txt', 'w') as f:
        pass

    if "." in name:
        if multiple: # working

            search_file_name = search_file_multiple(name)
            execute_command = run_powershell_command(search_file_name)

            
            with open('paths.txt', 'a') as f:
                for line in execute_command.splitlines():
                    f.write(f"{line}\n")

            print(f'Search file: {name} in {execute_command}')
            return f'Search file named: {name}'
        
        else: # working

            search_file_name = search_file(name)
            execute_command = run_powershell_command(f"{search_file_name} | Select-Object -First 1")
            
            
            output = execute_command.splitlines()
            output_one = output[0]
            with open('paths.txt', 'w') as f:
                f.write(output_one)

            print(f'Search command: {execute_command}')
            #print(f'search file: {name} in {powershell_search_path}')
            return f'Search file named: {name} in {output_one}'

    else: # folder
        if multiple: # working

            search_file_name = search_folder_mutiple(name)
            execute_command = run_powershell_command(search_file_name)

            with open('paths.txt', 'a') as f:
                for line in execute_command.splitlines():
                    f.write(f"{line}\n")

            print(f'Search folder: {name} in {execute_command}')
            return f'Search folder named: {name}'

        else: # working

            search_file_name = search_folder(name)
            execute_command = run_powershell_command(f"{search_file_name} | Select-Object -First 1")

            output = execute_command.splitlines()
            output_one = output[0]
            with open('paths.txt', 'w') as f:
                f.write(output_one)
            print(f'Search folder: {name} in {output_one}')
            return f'Search folder named: {name} in {output_one}'

def handle_change_dir_command(current_path, command_parts):
    try: # working
        if len(command_parts) < 2:
            print("Error: No directory name specified.")
            return

        # The directory name to search for
        dir_name = command_parts[1]

        # Generate the PowerShell command to find the directory
        powershell_command = recurse_dir(dir_name)
        if not powershell_command:
            print("Error: Failed to generate PowerShell command.")
            return

        # Execute the PowerShell command and capture its output
        output = run_powershell_command(f'{powershell_command} | Select-Object -First 1')

        print(f'change_dir: {output}')
        if output:
            # Split the output into paths (one per line)
            paths = output.splitlines()
            if not paths:
                print(f"No directories found matching '{dir_name}'.")
                return

            # Use the first result (or customize handling for multiple results)
            found_path = paths[0]
            print(f"Found path: {found_path}")

            # Update `current_path.txt` with the found path
            with open('current_path.txt', 'w') as f:
                f.write(found_path)
            print(f"Updated current_path.txt with: {found_path}")
            return f"Updated current_path.txt with: {found_path}"
        else:
            print(f"Error: No output from PowerShell command for '{dir_name}'.")
            return f"Error: No output from PowerShell command for '{dir_name}'."
    except Exception as e:
        print(f"Error in handle_change_dir_command: {e}")
        return f"Error in handle_change_dir_command: {e}"

def handle_go_back_home_command(current_path, command_parts):
    command_home_back = command_parts[1]

    if command_home_back == 'home' or command_home_back == 'home.' or command_home_back == 'home!': # working
        try:
            with open('current_path.txt', 'w') as f:
                f.write(DEFAULT_PATH)
            print("Updated current_path.txt to default path.")
            return "Updated current_path.txt to default path."
        except FileNotFoundError:
            print("Error: current_path.txt not found.")
            return "Error: current_path.txt not found."

    elif command_home_back == 'back' or command_home_back == 'back!' or command_home_back == "back." or command_home_back == "buck." or command_home_back == "buck!": # working
        try:
            with open('current_path.txt', 'r') as file:
                current_path = file.read().strip()
                # Ensure it's a valid path
                if not os.path.isdir(current_path):
                    print(f"Error: {current_path} is not a valid directory.")
                    return f"Error: {current_path} is not a valid directory."
        except FileNotFoundError:
            print("Error: current_path.txt not found.")
            return "Error: current_path.txt not found."

        try:
            # Ensure the current path is valid
            if os.path.isdir(current_path):
                # Move up one directory level
                execute_cd_back = f'Set-Location "{current_path}"; Set-Location ..; Get-Location'
                new_path = run_powershell_command(execute_cd_back)

                if new_path:
                    # Clean the returned path to remove unwanted text (like "Path    ----    ")
                    cleaned_path = new_path.split('\n')[-1].strip()  # Take the last line and strip spaces

                    # Debug print to check the returned new path
                    print(f"New path from PowerShell: '{cleaned_path}'")

                    if os.path.isdir(cleaned_path):
                        try:
                            with open('current_path.txt', 'w') as file:
                                file.write(cleaned_path)
                            print(f"Moved up one level to: {cleaned_path}")
                            return f"Moved up one level to: {cleaned_path}"
                        except IOError as e:
                            print(f"Error writing to current_path.txt: {e}")
                            return f"Error writing to current_path.txt: {e}"
                    else:
                        print(f"Error: {cleaned_path} is not a valid directory.")
                        return f"Error: {cleaned_path} is not a valid directory."
                else:
                    print("Error: Could not retrieve the new directory.")
                    return "Error: Could not retrieve the new directory."
            else:
                print("Error: Current path is not a valid directory.")
                return "Error: Current path is not a valid directory."
        except Exception as e:
            print(f"Exception while handling 'back' command: {e}")
            return f"Exception while handling 'back' command: {e}"

# Define a mapping of command keywords to handler functions
command_handlers = {
    "create": handle_create_command, 
    "open": handle_open_command, 
    "delete": handle_delete_command,  
    "rename": handle_rename_command, 
    "move": handle_move_command, 
    "copy": handle_copy_command,
    "kopieren": handle_copy_command, 
    "search": handle_search_command, 
    "change": handle_change_dir_command, 
    "go": handle_go_back_home_command 
}

def main(input_string):
    with open('current_path.txt', 'r') as f:
        current_path = f.read().strip()

    print(f"Current directory: {current_path}")
    
    # Split the input string into words
    command_parts = input_string.lower().split()

    if "." in command_parts[-1]:
       command_parts[-1] =  command_parts[-1].rstrip('.')

    if "?" in command_parts[-1]:
        command_parts[-1] = command_parts[-1].rstrip('?')

    print(f'commands parts[-1]: {command_parts[-1]}')
    print(f"Command parts: {command_parts}")

    # Iterate through the command handlers and check for a match
    for keyword, handler in command_handlers.items():
        if keyword.lower() in [part.lower() for part in command_parts]:
            # If the keyword is found, call the corresponding handler function
            result = handler(current_path, command_parts)  # Handler returns a result
            return result  # Return the result of the handler

    return "Command not found."  # If no keyword is matched, return this message

#if __name__ == "__main__":
    #input_string = input("Enter command: ")
    #main(input_string)

    # create 
    # go home, go back, working
    