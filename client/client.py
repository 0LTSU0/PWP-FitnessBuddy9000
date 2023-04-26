"""
Client to use fitnessbuddy api with
"""

import json
import threading
import pathlib
import tkinter as tk
from datetime import datetime
import requests as req
from pika_listener import STATS, listen_notifications

API = "http://127.0.0.1:5000/api/users/" #api entrypoint
API_ADDR = "http://127.0.0.1:5000/" #plain address for use with hypermedia controls
USER = None
HREFS = None

class SampleApp(tk.Tk):
    """
    Main tkinter implementation, based on https://stackoverflow.com/a/49325719
    """
    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.switch_frame(StartPage)

    def switch_frame(self, frame_class):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack()


class StartPage(tk.Frame):
    """
    Start frame for user selection
    """
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="FitnesbuddyAPI Client",
                 font=("Arial", 25, "bold")).pack(side="top", fill="x", pady=20)
        tk.Label(self, text="Select user:").pack()

        # To do anything with the api, a user needs to be specified
        self.users = {}
        self.error_visible = False
        users_get = req.get(API).json()
        for user in users_get.get("users"):
            self.users[user.get("name")] = user.get("id")
        sframe = tk.Frame(self)
        listbox = tk.Listbox(
            sframe,
            listvariable=tk.Variable(value=list(self.users.keys())),
            height=6,
            selectmode=tk.SINGLE
        )
        listboxscroll = tk.Scrollbar(sframe, orient=tk.VERTICAL)
        listboxscroll.config(command=listbox.yview)
        listboxscroll.pack(side=tk.RIGHT, fill=tk.Y)
        sframe.pack()
        listbox.pack()

        tk.Button(self, text="Select",
                  command=lambda: self.select_user(listbox,
                  listbox.curselection())).pack(side="top", pady=10)

    def select_user(self, listbox, selection):
        """
        Figure out the id of user selected by name
        """
        if not selection and not self.error_visible:
            tk.Label(self, text="Select user to continue").pack(pady=10)
            self.error_visible = True
        elif selection:
            global USER
            USER = self.users.get(listbox.get(selection))
            self.master.switch_frame(StatsPage)


class StatsPage(tk.Frame):
    """
    Main stats viewing page
    """
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="Stats", font=("Arial", 25, "bold")).pack(side="top", fill="x", pady=20)

        # Back to start and update stats buttons as well as frame for worker stats
        sframe = tk.Frame(self)
        statframe = tk.Frame(self)
        tk.Button(sframe, text="Return to start",
                  command=lambda: master.switch_frame(StartPage)).pack(side="left", padx=10)
        tk.Button(sframe, text="Update stats",
                  command=lambda: self.update_stats(statframe)).pack(side="left", padx=10)
        sframe.pack()
        tk.Label(statframe, text="Click 'Update stats' to get your stats").pack()
        statframe.pack(pady=40)

        #Use hypermedia to find hrefs for adding measurements and exercises
        global HREFS
        HREFS = self.find_hrefs(["fitnessbuddy:add-exercise",
                                 "fitnessbuddy:add-measurement", "fitnessbuddy:stats"])

        #Add buttons for the actions
        aframe = tk.Frame(self)
        tk.Button(aframe, text="Add Exercise",
                  command=lambda: master.switch_frame(AddExercise)).pack(padx=10, side="left")
        tk.Button(aframe, text="Add Measurement",
                  command=lambda: master.switch_frame(AddMeasurement)).pack(padx=10, side="left")
        aframe.pack()


    def update_stats(self, statframe):
        '''
        Callback for update stats button
        '''
        for child in statframe.winfo_children():
            child.destroy()

        res = req.get( API_ADDR + HREFS.get("fitnessbuddy:stats").get("href") )

        if res.status_code == 202: #need to wait for stats
            tk.Label(statframe, text="Waiting for stats...").pack(pady=20)
            statframe.after(10, lambda : self.draw_stats(statframe))
        else: #something is wrong
            tk.Label(statframe, text="Stat request failed. Please try again later").pack(pady=20)


    def draw_stats(self, statframe):
        '''
        Function to keep calling in the backgroud until stats arrive from pika listener
        '''
        if STATS.qsize() == 0:
            statframe.after(10, self.draw_stats, statframe)
        else:
            stats = STATS.get()
            for child in statframe.winfo_children():
                child.destroy()
            for key, value in stats.items():
                sframe = tk.Frame(statframe)
                tk.Label(sframe, text=key, width=20).pack(side="left")
                tk.Label(sframe, text=value, width=25).pack(side="left")
                sframe.pack()


    def find_hrefs(self, targets):
        """
        Loop controls to find desired targets
        """
        ret = {}
        controls = req.get(f"{API}{USER}/").json().get("@controls")
        for control in controls.values():
            if not control.get("method") or control.get("method") == "GET":
                res = req.get(API_ADDR + control.get("href")).json().get("@controls")
                for target in targets:
                    if target in res.keys():
                        ret[target] = res.get(target)
                        targets.remove(target)
            if not targets:
                break
        return ret


class AddExercise(tk.Frame):
    '''
    Screen for posting exercises
    '''
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="Add exercise",
                 font=("Arial", 25, "bold")).pack(side="top", fill="x", pady=20)

        #Generate form based on schema
        inputframe = tk.Frame(self)
        inputframe = generate_form(inputframe, HREFS.get("fitnessbuddy:add-exercise"))
        inputframe.pack()

        sframe = tk.Frame(self)
        self.errframe = tk.Frame(self)
        tk.Button(sframe, text="Back to stats",
            command=lambda: master.switch_frame(StatsPage)).pack(pady=20, padx=10, side="left")
        tk.Button(sframe, text="Submit",
            command=lambda: self.submit(inputframe,
            HREFS.get("fitnessbuddy:add-exercise"))).pack(pady=20, padx=10, side="left")
        sframe.pack()
        self.errframe.pack()

    def submit(self, inputframe, href):
        """
        Handler for submit button
        """
        success, response = submit(inputframe, href)

        #Clear possible error messages
        for child in self.errframe.winfo_children():
            child.destroy()

        #Flash new message
        if not success:
            response = response.get("message").replace("\n", "")
            tk.Label(self.errframe, text=response, fg='#ff1100',
                     wraplength=self.winfo_width()).pack(padx=20)
        else:
            tk.Label(self.errframe, text="Exercise added successfully",
                     fg='#00EB00', wraplength=self.winfo_width()).pack(padx=20)


class AddMeasurement(tk.Frame):
    '''
    Screen for posting measurements
    '''
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="Add measurements",
                 font=("Arial", 25, "bold")).pack(side="top", fill="x", pady=20)

        #Generate form based on schema
        inputframe = tk.Frame(self)
        inputframe = generate_form(inputframe, HREFS.get("fitnessbuddy:add-measurement"))
        inputframe.pack()

        sframe = tk.Frame(self)
        self.errframe = tk.Frame(self)
        tk.Button(sframe, text="Back to stats",
            command=lambda: master.switch_frame(StatsPage)).pack(pady=20, padx=10, side="left")
        tk.Button(sframe, text="Submit",
            command=lambda: self.submit(inputframe,
            HREFS.get("fitnessbuddy:add-measurement"))).pack(pady=20, padx=10, side="left")
        sframe.pack()
        self.errframe.pack()

    def submit(self, inputframe, href):
        """
        Handler for submit button
        """
        success, response = submit(inputframe, href)

        #Clear possible error messages
        for child in self.errframe.winfo_children():
            child.destroy()

        #Flash new message
        if not success:
            response = response.get("message").replace("\n", "")
            tk.Label(self.errframe, text=response, fg='#ff1100',
                     wraplength=self.winfo_width()).pack(padx=20)
        else:
            tk.Label(self.errframe, text="Measurements added successfully",
                fg='#00EB00', wraplength=self.winfo_width()).pack(padx=20)


def submit(inputframe, href):
    """
    Makes a post request to specified href based on stuff in inputframe
    """

    i = 0
    prev_label = None
    post = {}
    for frame in inputframe.winfo_children():
        #frame is constructed so that label, entry, label, entry,...
        for item in frame.winfo_children():
            if i % 2 == 0: #label
                stripped = item.cget("text").strip(" ").strip("(*):")
                post[stripped] = None
                prev_label = stripped
            else: #user inputted value
                val = item.get()
                if href.get("schema").get("properties").get(prev_label).get("type") == "number":
                    try:
                        val = float(val)
                    except ValueError:
                        pass #api will give error message so just ignore for now
                post[prev_label] = val
            i += 1

    res = req.post(API_ADDR + href.get("href"), json=post)
    if res.status_code != 201:
        return False, json.loads(res.content.decode())
    
    return True, ""


def generate_form(iframe, instr):
    """
    Generates measurement/exercise adding screen based on stuff in schema
    """

    labels = list(instr.get("schema").get("properties").keys())

    for item in instr.get("schema").get("required"): #first add required fields
        sframe = tk.Frame(iframe)
        label = item + "(*): "
        labels.remove(item)
        tk.Label(sframe, text=label.ljust(30, " ")).pack(side="left")
        tinput = tk.Entry(sframe, width = 30)
        if item == "date": #prefill date because format
            tinput.insert(0, datetime.now().isoformat())
        tinput.pack(side="left")
        sframe.pack()
    for item in labels: #then optional
        sframe = tk.Frame(iframe)
        label = item + ": "
        tk.Label(sframe, text=label.ljust(30, " ")).pack(side="left")
        tk.Entry(sframe, width = 30).pack(side="left")
        sframe.pack()

    return iframe


if __name__ == "__main__":
    #pika listener
    credential_path = pathlib.Path(__file__).parent.joinpath("pikacredentials.json")
    with open(credential_path, "r", encoding="utf-8") as f:
        cred = json.load(f)
        pikath = threading.Thread(target=listen_notifications,
                    args=(cred.get("user"), cred.get("password")), daemon=True)
        pikath.start()

    #client
    app = SampleApp()
    app.geometry("400x500")
    app.mainloop()
