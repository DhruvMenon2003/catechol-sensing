import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import os
from test_INTEGRATEDFULL import *

# Configure the modern look and feel
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

CURRENT_FILE = "/home/plaksha/touchscreen_app/current.txt"


class CatecholApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Plaksha Waste Water Monitor")

        # Set full screen mode
        self.attributes('-fullscreen', True)

        # Configure root grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create pages
        self.pages = {}
        for F in (WelcomePage, SamplePage, BufferPage, CalibrationPage):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_page("WelcomePage")

    def show_page(self, page_name):
        page = self.pages[page_name]
        page.tkraise()

        # If moving to calibration page, trigger the auto-read loop
        if page_name == "CalibrationPage":
            page.start_auto_read()


class WelcomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill='both')

        lbl_title = ctk.CTkLabel(container,
                                 text="Welcome to Plaksha",
                                 font=('Arial', 32, 'bold'))

        lbl_subtitle = ctk.CTkLabel(container,
                                    text="Industrial treated Waste Water Quality Monitoring App\n"
                                         "Based on the recommended exposure levels to catechol by EPA",
                                    justify='center',
                                    font=('Arial', 18))

        btn_start = ctk.CTkButton(container,
                                  text="Start",
                                  font=('Arial', 18, 'bold'),
                                  width=200, height=50,
                                  command=lambda: controller.show_page("SamplePage"))

        lbl_title.pack(pady=(150, 20))
        lbl_subtitle.pack(pady=20)
        btn_start.pack(pady=40)


class SamplePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill='both')

        lbl_question = ctk.CTkLabel(container,
                                    text="Have you inserted the sample?",
                                    font=('Arial', 28, 'bold'))

        btn_yes = ctk.CTkButton(container,
                                text="Yes",
                                font=('Arial', 18, 'bold'),
                                width=200, height=50,
                                command=lambda: controller.show_page("BufferPage"))

        btn_back = ctk.CTkButton(self,
                                 text="Back",
                                 font=('Arial', 16),
                                 width=120, height=40,
                                 fg_color="gray",
                                 hover_color="darkgray",
                                 command=lambda: controller.show_page("WelcomePage"))

        lbl_question.pack(pady=(200, 40))
        btn_yes.pack(pady=20)
        btn_back.place(relx=0.05, rely=0.95, anchor='sw')


class BufferPage(ctk.CTkFrame):
    # pH is accepted inside a tolerance band. Comparing a float to 6.5 with `==` almost never
    # succeeds (the operator would have to type exactly "6.5"), which made this page a dead end.
    TARGET_PH = 6.5
    PH_TOLERANCE = 0.1

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill='both')

        lbl_question = ctk.CTkLabel(container,
                                    text="Add ABS+PBS buffer?",
                                    font=('Arial', 28, 'bold'))

        btn_yes = ctk.CTkButton(container,
                                text="Yes",
                                font=('Arial', 18, 'bold'),
                                width=200, height=50,
                                command=self.show_ph_input)

        self.btn_back = ctk.CTkButton(self,
                                      text="Back",
                                      font=('Arial', 16),
                                      width=120, height=40,
                                      fg_color="gray",
                                      hover_color="darkgray",
                                      command=lambda: self.controller.show_page("SamplePage"))

        # pH Input Section (Hidden by default)
        self.ph_frame = ctk.CTkFrame(container, fg_color="transparent")

        lbl_ph = ctk.CTkLabel(self.ph_frame,
                              text="Kindly input displayed measured pH by the pH sensor",
                              font=('Arial', 18))

        self.entry_ph = ctk.CTkEntry(self.ph_frame,
                                     font=('Arial', 18),
                                     width=200, height=40,
                                     justify="center")

        btn_submit = ctk.CTkButton(self.ph_frame,
                                   text="Submit",
                                   font=('Arial', 16, 'bold'),
                                   width=150, height=40,
                                   command=self.check_ph)

        self.lbl_message = ctk.CTkLabel(self.ph_frame,
                                        text="",
                                        font=('Arial', 16),
                                        text_color="#ff6b6b")  # Soft red

        # Layout
        lbl_question.pack(pady=(100, 20))
        btn_yes.pack(pady=20)
        self.btn_back.place(relx=0.05, rely=0.95, anchor='sw')

        lbl_ph.pack(pady=20)
        self.entry_ph.pack(pady=10)
        btn_submit.pack(pady=20)
        self.lbl_message.pack(pady=10)

    def show_ph_input(self):
        self.ph_frame.pack(expand=True, fill='both', pady=20)

    def check_ph(self):
        try:
            ph = float(self.entry_ph.get())
            if abs(ph - self.TARGET_PH) <= self.PH_TOLERANCE:
                self.lbl_message.configure(text="")
                self.controller.show_page("CalibrationPage")
            else:
                self.lbl_message.configure(
                    text=f"Add more buffer and wait until pH settles to "
                         f"{self.TARGET_PH} (+/- {self.PH_TOLERANCE})")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric pH value")


class CalibrationPage(ctk.CTkFrame):
    """
    Live monitoring page.

    Reads the measured current from current.txt (written by test_INTEGRATEDFULL.startCV) and
    converts it into a concentration using the SHARED calibration function
    get_concentration_from_current(), imported from test_INTEGRATEDFULL. There is deliberately
    no calibration arithmetic in this file any more - a single source of truth means the
    touchscreen app and the development interface can never drift apart.

    Two operator controls:
      * Calibration mode  - "Piecewise Linear" (default) or "Linear"
      * Dilution factor   - multiplied into the reported concentration. Always visible, and
                            highlighted when a reading comes back OUT OF RANGE.
    """

    SUBSTANCE = 'Catechol'

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.is_reading = False
        self.dilution_factor = 1.0
        self.setup_ui()

    # ------------------------------------------------------------------ UI ---
    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill='both')

        lbl_title = ctk.CTkLabel(container,
                                 text="Calibration Curve & Live Safety Monitor",
                                 font=('Arial', 28, 'bold'))

        self.btn_back = ctk.CTkButton(self,
                                      text="Back",
                                      font=('Arial', 16),
                                      width=120, height=40,
                                      fg_color="gray",
                                      hover_color="darkgray",
                                      command=self.stop_and_go_back)

        # ---------------- Calibration Graph ----------------
        graph_frame = ctk.CTkFrame(container)
        graph_frame.pack(expand=True, fill='both', padx=50, pady=(20, 10))

        try:
            # CustomTkinter uses CTkImage to handle high-DPI and scaling safely
            img = Image.open("calibration.png")
            self.graph_img = ctk.CTkImage(light_image=img, dark_image=img, size=(800, 380))
            lbl_graph = ctk.CTkLabel(graph_frame, image=self.graph_img, text="")
            lbl_graph.pack(expand=True, pady=10)
        except FileNotFoundError:
            ctk.CTkLabel(graph_frame,
                         text="Calibration Graph Not Found (calibration.png)",
                         font=("Arial", 16)).pack(expand=True)

        # ---------------- Operator controls ----------------
        controls_frame = ctk.CTkFrame(container)
        controls_frame.pack(pady=(5, 5), padx=50, fill='x')

        # Calibration method selector
        ctk.CTkLabel(controls_frame,
                     text="Calibration method:",
                     font=('Arial', 15)).grid(row=0, column=0, padx=(15, 8), pady=12, sticky='e')

        self.calib_mode = ctk.CTkSegmentedButton(
            controls_frame,
            values=["Piecewise Linear", "Linear"],
            font=('Arial', 14),
            command=self.on_calibration_mode_change)
        self.calib_mode.set("Piecewise Linear")
        self.calib_mode.grid(row=0, column=1, padx=(0, 30), pady=12, sticky='w')

        # Dilution factor entry
        ctk.CTkLabel(controls_frame,
                     text="Dilution factor:",
                     font=('Arial', 15)).grid(row=0, column=2, padx=(15, 8), pady=12, sticky='e')

        self.entry_dilution = ctk.CTkEntry(controls_frame,
                                           font=('Arial', 15),
                                           width=110, height=36,
                                           justify="center")
        self.entry_dilution.insert(0, "1")
        self.entry_dilution.grid(row=0, column=3, padx=(0, 8), pady=12)

        self.btn_apply_dilution = ctk.CTkButton(controls_frame,
                                                text="Apply",
                                                font=('Arial', 14, 'bold'),
                                                width=90, height=36,
                                                command=self.apply_dilution_factor)
        self.btn_apply_dilution.grid(row=0, column=4, padx=(0, 15), pady=12)

        self.lbl_dilution_note = ctk.CTkLabel(
            controls_frame,
            text="True concentration = measured concentration x dilution factor",
            font=('Arial', 13, 'italic'),
            text_color="gray")
        self.lbl_dilution_note.grid(row=1, column=0, columnspan=5, pady=(0, 10))

        # ---------------- Status & Result ----------------
        status_frame = ctk.CTkFrame(container, fg_color="transparent")
        status_frame.pack(pady=(5, 15))

        self.lbl_current_reading = ctk.CTkLabel(status_frame,
                                                text="Reading sensor data...",
                                                font=('Arial', 16, 'italic'))
        self.lbl_current_reading.pack(pady=(0, 8))

        # Big result display box
        self.lbl_result = ctk.CTkLabel(status_frame,
                                       text="Awaiting Data...",
                                       font=('Arial', 22, 'bold'),
                                       width=900, height=110,
                                       corner_radius=10,
                                       wraplength=860,
                                       justify='center',
                                       fg_color="#333333",  # Dark grey default
                                       text_color="white")
        self.lbl_result.pack()

        # Layout
        lbl_title.pack(pady=(20, 0))
        self.btn_back.place(relx=0.05, rely=0.95, anchor='sw')

    # ------------------------------------------------------- control logic ---
    def use_piecewise(self):
        """True when the operator has selected piecewise linear calibration."""
        return self.calib_mode.get() == "Piecewise Linear"

    def on_calibration_mode_change(self, _value=None):
        """Re-annotate immediately; the next poll re-evaluates the reading with the new method."""
        self.lbl_current_reading.configure(
            text=f"Calibration switched to {self.calib_mode.get()}. Re-evaluating...")

    def apply_dilution_factor(self):
        """Read, validate and store the dilution factor entered by the operator."""
        raw = self.entry_dilution.get().strip()
        try:
            df = float(raw)
            if df <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error",
                "Dilution factor must be a positive number.\n\n"
                "Example: a 1-in-10 dilution (1 mL sample + 9 mL buffer) has a "
                "dilution factor of 10.")
            return

        self.dilution_factor = df
        self.lbl_dilution_note.configure(
            text=f"Dilution factor {df:g} applied - reported concentration = "
                 f"measured concentration x {df:g}",
            text_color="#4dabf7")

    # --------------------------------------------------------- read loop -----
    def start_auto_read(self):
        """Starts the background loop to read current.txt when the page is opened."""
        self.is_reading = True
        self.read_current_loop()

    def stop_and_go_back(self):
        """Stops the loop before going back to prevent memory leaks or overlapping loops."""
        self.is_reading = False
        self.controller.show_page("BufferPage")

    def read_current_loop(self):
        """Automatically reads current.txt every 2000 ms (2 seconds)."""
        if not self.is_reading:
            return  # Stop loop if we navigated away

        try:
            if not os.path.exists(CURRENT_FILE):
                raise FileNotFoundError

            with open(CURRENT_FILE, "r") as f_current:
                content = f_current.read().strip()
                if content:
                    current = float(content)
                    self.lbl_current_reading.configure(
                        text=f"Live Current Reading: {current:.4f} uA   |   "
                             f"{self.calib_mode.get()} calibration   |   "
                             f"Dilution factor: {self.dilution_factor:g}")
                    self.process_safety(current)
                else:
                    self.lbl_current_reading.configure(text="current.txt is empty. Waiting...")

        except FileNotFoundError:
            self.lbl_current_reading.configure(text="Error: current.txt not found. Retrying...")
            self.lbl_result.configure(text="Sensor Disconnected", fg_color="#333333")
        except ValueError:
            self.lbl_current_reading.configure(text="Error: Invalid data in current.txt. Retrying...")
            self.lbl_result.configure(text="Data Error", fg_color="#333333")

        # Trigger the next sweep, then schedule the next read in 2000 ms
        startCV()
        self.after(2000, self.read_current_loop)

    # ----------------------------------------------------- interpretation ----
    def process_safety(self, current):
        """
        Convert the measured current into a concentration using the SHARED calibration
        function, apply the operator's dilution factor, and colour-code the verdict.
        """
        cal = get_concentration_from_current(
            current,
            substance=self.SUBSTANCE,
            use_piecewise=self.use_piecewise(),
            dilution_factor=self.dilution_factor
        )

        # ---------- OUT OF RANGE: no verdict, instruct the operator to dilute ----------
        if not cal['in_range']:
            i_min, i_max = calibration_current_window(self.SUBSTANCE, self.use_piecewise())
            self.lbl_result.configure(
                text=("OUT OF RANGE, PERFORM SUCCESSIVE DILUTIONS UNTIL YOU ACHIEVE A CURRENT "
                      "READING THAT IS IN RANGE. MULTIPLY THE CORRESPONDING CONCENTRATION BY "
                      "THE DILUTION FACTOR TO OBTAIN THE TRUE CONCENTRATION.\n"
                      f"Calibrated window: {i_min:.2f} to {i_max:.2f} uA"),
                fg_color="#455a64")  # blue-grey: deliberately NOT a safety colour

            self.lbl_dilution_note.configure(
                text="Dilute the sample, then enter the dilution factor above and press Apply.",
                text_color="#ffa94d")
            return

        # ---------- IN RANGE: report and classify ----------
        concentration = cal['concentration']      # already multiplied by the dilution factor
        raw_conc = cal['raw_concentration']       # concentration of the solution as measured
        safety = classify_safety(concentration)

        if cal['method'] == 'piecewise' and cal['segment_index'] >= 0:
            method_line = f"Piecewise segment {cal['segment_index'] + 1}"
        else:
            method_line = "Linear calibration"

        if self.dilution_factor != 1.0:
            conc_line = (f"Measured: {raw_conc:.2f} uM  x  DF {self.dilution_factor:g}  =  "
                         f"True Concentration: {concentration:.2f} uM")
        else:
            conc_line = f"Est. Concentration: {concentration:.2f} uM"

        self.lbl_result.configure(
            text=f"{conc_line}\n{safety['status']}\n({method_line})",
            fg_color=safety['color'])


if __name__ == "__main__":
    app = CatecholApp()
    app.mainloop()
