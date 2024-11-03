import time
from datetime import datetime

import flet as ft
import pyautogui
from pynput import keyboard, mouse


def main(page: ft.Page):
    """Main application function for the event logger and executor.

    Initializes and runs a GUI application that records keyboard and mouse events
    with timestamps, allows saving and loading of recorded events, and provides
    execution capability for recorded events.

    Args:
        page (ft.Page): The Flet page object that represents the GUI.

    Returns:
        None
    """
    # UI Components
    event_log = ft.Column()  # Renamed from events_display

    # State tracking
    recording_state = {
        "is_active": False,
        "start_time": time.time(),
        "active_keys": set(),
        "active_mouse_buttons": set(),
    }

    # State tracking for execution
    execution_state = {
        "is_running": False,
    }

    # Code display for generated code
    code_display = ft.TextField(
        value="",
        multiline=True,
        read_only=True,
        min_lines=10,
        max_lines=20,
        text_size=14,
    )

    def get_timestamp():
        """Get time elapsed since recording start."""
        elapsed = time.time() - recording_state["start_time"]
        return f"+{elapsed:.3f}s"

    def create_input_listeners():
        """Create new keyboard and mouse listeners."""
        mouse_listener = mouse.Listener(on_click=handle_mouse_click)
        keyboard_listener = keyboard.Listener(
            on_press=handle_key_press, on_release=handle_key_release
        )
        return mouse_listener, keyboard_listener

    def toggle_recording(e):
        """Toggle between recording and stopped states."""
        nonlocal mouse_listener, keyboard_listener

        if recording_state["is_active"]:
            # Stop recording
            keyboard_listener.stop()
            mouse_listener.stop()
            recording_state["is_active"] = False
            record_button.text = "Record"
            record_button.icon = "radio_button_checked"
            record_button.tooltip = "Start Recording"
        else:
            # Start recording
            mouse_listener, keyboard_listener = create_input_listeners()
            keyboard_listener.start()
            mouse_listener.start()
            recording_state["is_active"] = True
            record_button.text = "Record"
            record_button.icon = "stop_circle_outlined"
            record_button.tooltip = "Stop Recording"
            # Clear previous code display
            code_display.value = ""
        page.update()

    def log_event(event_data):
        """Add timestamped event to the log display and update generated code."""
        # Get timestamp
        elapsed = time.time() - recording_state["start_time"]
        event_data["timestamp"] = round(elapsed, 3)

        # Create display text
        display_text = create_display_text(event_data, elapsed)

        # Add to display
        event_log.controls.append(ft.Text(display_text))
        event_log.controls[-1].data = event_data
        page.update()

        # Update generated code
        update_generated_code(event_data)

    def create_display_text(event_data, elapsed):
        """Create display text for the event log."""
        if event_data["eventType"] == "Mouse":
            return (
                f"[+{elapsed:.3f}s] Mouse Event - {event_data['button'].capitalize()} button "
                f"{event_data['action']} at ({event_data['coordinates']['x']}, "
                f"{event_data['coordinates']['y']})"
            )
        else:  # Keyboard event
            key_text = event_data["key"]
            if event_data.get("specialKey", False):
                return f"[+{elapsed:.3f}s] Keyboard Event - Special Key {event_data['action']}: {key_text}"
            else:
                return f"[+{elapsed:.3f}s] Keyboard Event - Key {event_data['action']}: {key_text}"

    def update_generated_code(event_data):
        """Update the generated code based on recorded events."""
        code_lines = [
            "import pyautogui",
            "import time",
            "",
            "def run_automation():",
            "    # Wait 2 seconds before starting",
            "    time.sleep(2)",
            "",
        ]

        previous_timestamp = 0  # Initialize previous timestamp
        for event in event_log.controls:
            event_data = event.data
            current_timestamp = event_data["timestamp"]

            # Calculate time difference and wait if necessary
            time_diff = current_timestamp - previous_timestamp
            if previous_timestamp != 0:  # Skip wait for the first event
                rounded_time_diff = round(time_diff, 3)  # Round to 3 decimal places
                code_lines.append(f"    time.sleep({rounded_time_diff})")

            if event_data["eventType"] == "Mouse":
                button = event_data["button"]
                x, y = (
                    event_data["coordinates"]["x"],
                    event_data["coordinates"]["y"],
                )
                if event_data["action"] == "Pressed":
                    code_lines.append(
                        f"    pyautogui.mouseDown(button='{button}', x={x}, y={y})"
                    )
                elif event_data["action"] == "Released":
                    code_lines.append(
                        f"    pyautogui.mouseUp(button='{button}', x={x}, y={y})"
                    )
            elif event_data["eventType"] == "Keyboard":
                key = event_data["key"]
                if event_data["action"] == "Pressed":
                    code_lines.append(f"    pyautogui.keyDown('{key}')")
                elif event_data["action"] == "Released":
                    code_lines.append(f"    pyautogui.keyUp('{key}')")

            previous_timestamp = current_timestamp  # Update previous timestamp

        # Add main guard
        # code_lines.extend(["", "if __name__ == '__main__':", "    run_automation()"])
        code_lines.extend(["", "run_automation()"])

        # Update code display
        code_display.value = "\n".join(code_lines)
        page.update()

    def handle_key_press(key):
        """Handle keyboard press events."""
        if key not in recording_state["active_keys"]:
            recording_state["active_keys"].add(key)
            try:
                # Check for special keys and adjust output
                if key == keyboard.Key.shift:
                    event_data = {
                        "eventType": "Keyboard",
                        "action": "Pressed",
                        "key": "shift",
                        "specialKey": True,
                    }
                elif key == keyboard.Key.alt:
                    event_data = {
                        "eventType": "Keyboard",
                        "action": "Pressed",
                        "key": "option",  # Change to 'option' for macOS
                        "specialKey": True,
                    }
                elif key == keyboard.Key.cmd:
                    event_data = {
                        "eventType": "Keyboard",
                        "action": "Pressed",
                        "key": "command",  # Change to 'command' for macOS
                        "specialKey": True,
                    }
                else:
                    # Handle regular keys
                    event_data = {
                        "eventType": "Keyboard",
                        "action": "Pressed",
                        "key": key.char.lower()
                        if key.char
                        else str(key).replace("Key.", ""),
                    }
            except AttributeError:
                # Handle special keys that don't have a char attribute
                event_data = {
                    "eventType": "Keyboard",
                    "action": "Pressed",
                    "key": str(key).replace("Key.", ""),
                    "specialKey": True,
                }
            log_event(event_data)

    def handle_key_release(key):
        """Handle keyboard release events."""
        if key in recording_state["active_keys"]:
            recording_state["active_keys"].remove(key)
            try:
                # Check for special keys and adjust output
                if key == keyboard.Key.shift:
                    event_data = {
                        "eventType": "Keyboard",
                        "action": "Released",
                        "key": "shift",
                        "specialKey": True,
                    }
                elif key == keyboard.Key.alt:
                    event_data = {
                        "eventType": "Keyboard",
                        "action": "Released",
                        "key": "option",  # Change to 'option' for macOS
                        "specialKey": True,
                    }
                elif key == keyboard.Key.cmd:
                    event_data = {
                        "eventType": "Keyboard",
                        "action": "Released",
                        "key": "command",  # Change to 'command' for macOS
                        "specialKey": True,
                    }
                else:
                    # Handle regular keys
                    event_data = {
                        "eventType": "Keyboard",
                        "action": "Released",
                        "key": key.char.lower()
                        if key.char
                        else str(key).replace("Key.", ""),
                    }
            except AttributeError:
                # Handle special keys that don't have a char attribute
                event_data = {
                    "eventType": "Keyboard",
                    "action": "Released",
                    "key": str(key).replace("Key.", ""),
                    "specialKey": True,
                }
            log_event(event_data)

    def handle_mouse_click(x, y, button, pressed):
        """Handle mouse click events."""
        button_name = str(button).replace("Button.", "").lower()

        # Round coordinates to integers
        x_int = round(x)
        y_int = round(y)

        event_data = {
            "eventType": "Mouse",
            "action": "Pressed" if pressed else "Released",
            "coordinates": {"x": x_int, "y": y_int},
            "button": button_name,
        }

        if pressed and button not in recording_state["active_mouse_buttons"]:
            recording_state["active_mouse_buttons"].add(button)
            log_event(event_data)
        elif not pressed and button in recording_state["active_mouse_buttons"]:
            recording_state["active_mouse_buttons"].remove(button)
            log_event(event_data)

    def save_recording(e):
        """Save RPA code to a Python file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save RPA code to Python file
        rpa_code_filename = f"rpa_code_{timestamp}.py"
        with open(rpa_code_filename, "w", encoding="utf-8") as f:
            f.write(code_display.value)

        snack = ft.SnackBar(content=ft.Text(f"RPA code saved to {rpa_code_filename}"))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def reset_log(e=None):
        """Clear the event log and reset timer."""
        event_log.controls.clear()
        recording_state["start_time"] = time.time()
        code_display.value = ""  # Reset code display
        page.update()

    def execute_rpa_process(e):
        """Execute the recorded RPA process."""
        nonlocal execution_state
        if not execution_state["is_running"]:
            execution_state["is_running"] = True
            execute_button.icon = ft.icons.STOP_CIRCLE_OUTLINED
            execute_button.tooltip = "Stop Execution"

            # Execute the generated code
            try:
                exec_globals = {"pyautogui": pyautogui, "time": time}
                exec(code_display.value, exec_globals)
            except Exception as ex:
                snack = ft.SnackBar(content=ft.Text(f"Execution error: {ex}"))
                page.overlay.append(snack)
                snack.open = True
                page.update()
        else:
            execution_state["is_running"] = False
            execute_button.icon = ft.icons.PLAY_CIRCLE_OUTLINED
            execute_button.tooltip = "Execute RPA Process"
            # Logic to stop the execution if needed
            # stop_execution()  # Placeholder for stopping logic
        page.update()

    # Create UI buttons
    record_button = ft.ElevatedButton(
        "Record", icon="radio_button_checked", on_click=toggle_recording
    )

    reset_button = ft.ElevatedButton(
        "Reset",
        icon=ft.icons.REFRESH,
        on_click=reset_log,
    )

    execute_button = ft.ElevatedButton(
        "Run Code", icon="play_circle_outlined", on_click=execute_rpa_process
    )

    download_button = ft.ElevatedButton(
        "Export Code", icon="download", on_click=save_recording
    )

    # Group buttons by position
    left_buttons = ft.Row(
        controls=[
            record_button,
            reset_button,  # Updated to ElevatedButton
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    right_buttons = ft.Row(
        controls=[
            execute_button,  # Updated execute button
            download_button,  # Updated download button
        ],
        alignment=ft.MainAxisAlignment.END,
    )

    # Main button container
    button_container = ft.Row(
        controls=[left_buttons, right_buttons],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Initialize listeners
    mouse_listener, keyboard_listener = create_input_listeners()

    # Create tabs
    def create_tabs():
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Event Log",
                    content=ft.Container(content=event_log, padding=10),
                ),
                ft.Tab(
                    text="Generated Code",
                    content=code_display,  # Directly use code_display without additional container
                ),
            ],
        )
        return tabs

    # Configure page
    page.scroll = "adaptive"
    page.add(
        button_container,
        create_tabs(),  # Add tabbed interface
    )


# Start the app
ft.app(target=main)
