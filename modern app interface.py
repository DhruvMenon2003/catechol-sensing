import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import os

# Configure the modern look and feel
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

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
            if ph == 6.5:
                self.controller.show_page("CalibrationPage")
                self.lbl_message.configure(text="")
            else:
                self.lbl_message.configure(text="Add more buffer and wait until pH settles to 6.5")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric pH value")


class CalibrationPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.is_reading = False
        self.setup_ui()

    def setup_ui(self):
        # Main container
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

        # Calibration Graph
        graph_frame = ctk.CTkFrame(container)
        graph_frame.pack(expand=True, fill='both', padx=50, pady=(20, 10))
        
        try:
            # CustomTkinter uses CTkImage to handle high-DPI and scaling safely
            img = Image.open("calibration.png")
            self.graph_img = ctk.CTkImage(light_image=img, dark_image=img, size=(800, 450))
            lbl_graph = ctk.CTkLabel(graph_frame, image=self.graph_img, text="")
            lbl_graph.pack(expand=True, pady=10)
        except FileNotFoundError:
            ctk.CTkLabel(graph_frame, text="Calibration Graph Not Found (calibration.png)", font=("Arial", 16)).pack(expand=True)

        # Status & Result Display
        status_frame = ctk.CTkFrame(container, fg_color="transparent")
        status_frame.pack(pady=20)

        self.lbl_current_reading = ctk.CTkLabel(status_frame, 
                                                text="Reading sensor data...", 
                                                font=('Arial', 16, 'italic'))
        self.lbl_current_reading.pack(pady=(0, 10))

        # Big result display box
        self.lbl_result = ctk.CTkLabel(status_frame, 
                                       text="Awaiting Data...", 
                                       font=('Arial', 24, 'bold'), 
                                       width=400, height=100,
                                       corner_radius=10,
                                       fg_color="#333333",  # Dark grey default
                                       text_color="white")
        self.lbl_result.pack()

        # Layout
        lbl_title.pack(pady=(20, 0))
        self.btn_back.place(relx=0.05, rely=0.95, anchor='sw')

    def start_auto_read(self):
        """Starts the background loop to read current.txt when the page is opened."""
        self.is_reading = True
        self.read_current_loop()

    def stop_and_go_back(self):
        """Stops the loop before going back to prevent memory leaks or overlapping loops."""
        self.is_reading = False
        self.controller.show_page("BufferPage")

    def read_current_loop(self):
        """Automatically reads current.txt every 2000ms (2 seconds)."""
        if not self.is_reading:
            return  # Stop loop if we navigated away

        try:
            if not os.path.exists("current.txt"):
                raise FileNotFoundError
            
            with open("current.txt", "r") as f:
                content = f.read().strip()
                if content:
                    current = float(content)
                    self.lbl_current_reading.configure(text=f"Live Current Reading: {current:.4f} μA")
                    self.process_safety(current)
                else:
                    self.lbl_current_reading.configure(text="current.txt is empty. Waiting...")
                    
        except FileNotFoundError:
            self.lbl_current_reading.configure(text="Error: current.txt not found. Retrying...")
            self.lbl_result.configure(text="Sensor Disconnected", fg_color="#333333")
        except ValueError:
            self.lbl_current_reading.configure(text="Error: Invalid data in current.txt. Retrying...")
            self.lbl_result.configure(text="Data Error", fg_color="#333333")

        # Schedule the next read in 2000 ms (2 seconds)
        self.after(2000, self.read_current_loop)

    def process_safety(self, current):
        # Calculate concentration
        concentration = (current + 0.150204) / 0.106015
        
        ACUTE_LIMIT = 10.0  # uM
        CHRONIC_LIMIT = 181.0  # uM

        if concentration > CHRONIC_LIMIT:
            result_text = f"Est. Concentration: {concentration:.2f} μM\nUNSAFE TOXIC!"
            self.lbl_result.configure(text=result_text, fg_color="#d32f2f") # Red
            
        elif concentration > ACUTE_LIMIT:
            result_text = f"Est. Concentration: {concentration:.2f} μM\nHEALTH RISK!"
            self.lbl_result.configure(text=result_text, fg_color="#f57c00") # Orange (Standard warning color)
            
        else:
            result_text = f"Est. Concentration: {concentration:.2f} μM\nSAFE!"
            self.lbl_result.configure(text=result_text, fg_color="#388e3c") # Green

if __name__ == "__main__":
    app = CatecholApp()
    app.mainloop()