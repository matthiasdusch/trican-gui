import matplotlib
matplotlib.use('TkAgg')  # noqa
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as tkagg

import numpy as np
import pandas as pd

import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog
from tkinter import messagebox, simpledialog

from trican import io


class MainApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self._frame = None
        self.title_font = tkfont.Font(family='Helvetica',
                                      size=18, weight="bold", slant="italic")
        self.title('Tree Ring Chronology Altitude Normalization')
        self.switch_frame(Correction)

    def switch_frame(self, frame_class):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack(fill='both', expand=True)

    def select_tr_series(self, child):
        filename = filedialog.askopenfilename(
            initialdir='../../testdaten',
            title='Select a tree ring series',
            filetypes=(('Heidelberg Format', '*.fh'), ('all files', '*.*')))
        child.series = io.read_heidelberg(filename, seriestype='Series')

        for tree in child.series:
            child.ax.plot(np.arange(tree.begin, tree.end+1), tree.data,
                    linestyle='--',
                    label=tree.key)
        child.ax.legend()
        child.ax.autoscale()
        child.canvas.draw()

    def select_correction(self, child):

        filename = filedialog.askopenfilename(
            initialdir='../../testdaten',
            title='Select a file containing the correction parameters',)
            #filetypes=(('all files', '*.*')))

        cordf = pd.read_csv(filename, delim_whitespace=True, index_col=0)
        if 'factor' not in cordf.columns:
            cordf['factor'] = np.ones(len(cordf))
        if 'offset' not in cordf.columns:
            cordf['offset'] = np.zeros(len(cordf))+0.4

        child.cordf = cordf

    def enter_parameters(self, child):

        if not hasattr(child, 'series'):
            messagebox.showinfo("Warning",
                                "Tree ring series must be loaded before " +
                                "parameters can be entered")
        else:
            cordf = pd.DataFrame([], columns=['factor', 'offset', 'name'])
            for i, ser in enumerate(child.series):
                cordf.loc[i, 'name'] = ser.key
                fac = simpledialog.askfloat(
                    'Correction Factor',
                    'Enter correction factor for %s:' % ser.key,
                    initialvalue=1.0)
                off = simpledialog.askfloat(
                    'Correction Offset',
                    'Enter correction offset for %s:' % ser.key,
                    initialvalue=0.0)
                cordf.loc[i, 'factor'] = fac
                cordf.loc[i, 'offset'] = off
            cordf.index = cordf.name
            cordf.drop('name', axis=1, inplace=True)
            child.cordf = cordf

    def write_correction(self, child, method=None):

        filename = filedialog.asksaveasfilename(
            initialdir='../../testdaten',
            title='Save %s tree ring series' % method,
            filetypes=(('Heidelberg Format', '*.fh'), ('all files', '*.*')))

        io.write_heidelberg(child.series, filename=filename)

    def init_title(self, child, title):
        frame = tk.Frame(child, relief=tk.RAISED, borderwidth=1)
        frame.pack(fill=tk.X)

        label = tk.Label(frame, text=title,
                         font=('Helvetica, 20'))
        label.pack(side='left', padx=10, pady=20)

        if 'Correction' in child.__class__.__name__:
            # Button to Chronology fitting
            btn = tk.Button(frame,
                            text="Go to chronology fitting",
                            command=lambda: self.switch_frame(Fitting))
            btn.pack(side='right', padx=10)

        elif 'Fitting' in child.__class__.__name__:
            # Button to Series correction
            btn = tk.Button(frame,
                            text="Go to series correction",
                            command=lambda: self.switch_frame(Correction))
            btn.pack(side='right', padx=10)

    def init_series(self, child):
        frame = tk.Frame(child)
        frame.pack(fill=tk.X)

        # Button to select series
        label1 = tk.Label(frame, text="1. Select tree ring series",
                          font=('Helvetica, 13'))
        label1.pack(side='left', padx=20)

        readseries = tk.Button(frame,
                               text="Select tree ring series",
                               command=lambda: self.select_tr_series(child))
        readseries.pack(side='right', padx=100)


    def init_write_series(self, child):
        # Button to write the
        frame = tk.Frame(child)
        frame.pack(fill=tk.X)

        label1 = tk.Label(frame, text="4. Write output to file",
                          font=('Helvetica, 13'))
        label1.pack(side='left', padx=20)

        if 'Correction' in child.__class__.__name__:
            btn = tk.Button(frame,
                            text="Write corrected series",
                            command=lambda:
                            self.write_correction(child,
                                                method='corrected'))
            btn.pack(side='right', padx=100)

        elif 'Fitting' in child.__class__.__name__:
            btn = tk.Button(frame,
                            text="Write fitted series",
                            command=lambda:
                            self.write_correction(child,
                                                    method='fitted'))
            btn.pack(side='right', padx=100)

    def init_graphic(self, child):
        frame = tk.Frame(child)
        frame.pack(fill=tk.BOTH, expand=True)

        # Graphics
        fig = plt.Figure(figsize=(8, 3))
        child.ax = fig.add_subplot(111)
        child.ax.plot(0, 0, '.w')

        child.canvas = tkagg.FigureCanvasTkAgg(fig, frame)
        child.canvas.show()
        child.canvas.get_tk_widget().pack(fill='both', expand=True, side='top')
        nav = tkagg.NavigationToolbar2TkAgg(child.canvas, frame)
        nav.pack(side='bottom')


class Correction(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # title frame
        title = "Altitude correction of tree ring series"
        parent.init_title(self, title)
        parent.init_series(self)
        self.init_parameters(parent)
        self.init_correction()
        parent.init_write_series(self)
        parent.init_graphic(self)

    def init_parameters(self, parent):
        frame = tk.Frame(self)
        frame.pack(fill=tk.X)

        label1 = tk.Label(frame, text='2. Select correction parameter',
                          font=('Helvetica, 13'))
        label1.pack(side='left', padx=20)

        btn1 = tk.Button(frame,
                         text="Select file with correction parameters",
                         command=lambda: parent.select_correction(self))
        btn1.pack(side='right', padx=100)

        frame2 = tk.Frame(self)
        frame2.pack(fill=tk.X)
        btn2 = tk.Button(frame2,
                               text="Insert parameters manually",
                               command=lambda: parent.enter_parameters(self))
        btn2.pack(side='right', padx=100)

    def init_correction(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.X)

        label1 = tk.Label(frame, text='3. Calculate correction',
                          font=('Helvetica, 13'))
        label1.pack(side='left', padx=20)

        btn = tk.Button(frame,
                        text="Calculate the correction",
                        command=lambda: self.calc_correction())
        btn.pack(side='right', padx=100)

    def calc_correction(self):

        for tree in self.series:
            tree.altitude_correction(factor=self.cordf.loc[tree.key].factor,
                                     offset=self.cordf.loc[tree.key].offset)

            self.ax.plot(np.arange(tree.begin, tree.end+1),
                          tree.corrected_data,
                          linestyle='-',
                          linewidth=2,
                          label=tree.key + ' corrected')
        self.ax.legend()
        self.ax.autoscale()
        self.canvas.draw()


class Fitting(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # title frame
        title = "Chronology fitting of tree ring series"
        parent.init_title(self, title)
        parent.init_series(self)
        self.init_chronology(parent)
        self.init_fitting()
        parent.init_write_series(self)
        parent.init_graphic(self)

    def init_chronology(self, parent):
        frame = tk.Frame(self)
        frame.pack(fill=tk.X)

        label1 = tk.Label(frame, text='2. Select tree ring chronology',
                          font=('Helvetica, 13'))
        label1.pack(side='left', padx=20)

        btn1 = tk.Button(frame,
                         text="Select chronology file",
                         command=lambda: self.select_chronology())
        btn1.pack(side='right', padx=100)

    def init_fitting(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.X)

        label1 = tk.Label(frame, text='3. Fit series to chronology',
                          font=('Helvetica, 13'))
        label1.pack(side='left', padx=20)

        btn = tk.Button(frame,
                        text="Fitting",
                        command=lambda: self.calc_fitting())
        btn.pack(side='right', padx=100)

    def calc_fitting(self):
        for tree in self.series:
            tree.altitude_fitting(self.chrono)

            self.ax.plot(np.arange(tree.begin, tree.end+1),
                         tree.fitted_data,
                         linestyle='-',
                         linewidth=2,
                         label=tree.key + ' fitted')
        self.ax.legend()
        self.ax.autoscale()
        self.canvas.draw()


    def select_chronology(self):

        filename = filedialog.askopenfilename(
            initialdir='../../testdaten',
            title='Select a file containing the chronology',
            filetypes=(('Heidelberg format', '*.fh'), ('all files', '*.*')))

        self.chrono = io.read_heidelberg(filename, seriestype='Chronology')

        self.ax.plot(np.arange(self.chrono.begin, self.chrono.end+1),
                     self.chrono.data,
                     linestyle='-',
                     color='k',
                     linewidth=2,
                     label=self.chrono.key + ' (Chronology)',
                     zorder=1)
        self.ax.legend()
        self.ax.autoscale()
        self.canvas.draw()


def main():
    app = MainApp()
    app.geometry('800x800+100+100')
    app.mainloop()


if __name__ == '__main__':
    main()