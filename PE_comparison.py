import threading
import yfinance as yf
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, messagebox


class TickerApp:
    def __init__(self, root):
        self.root = root
        self.tickers = []

        self.root.title("Ticker Input")
        self.root.configure(bg="#f0f8ff")

        # Configure grid layout
        self.root.rowconfigure([0, 1, 2, 3, 4], weight=1)
        self.root.rowconfigure(5, weight=5)
        self.root.columnconfigure(0, weight=1)

        # Style setup
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("Add.TButton", font=("Arial", 16), padding=10, background="lightgreen")
        self.style.map("Add.TButton", background=[("active", "green")], foreground=[("active", "white")])
        self.style.configure("Remove.TButton", font=("Arial", 16), padding=10, background="lightcoral")
        self.style.map("Remove.TButton", background=[("active", "red")], foreground=[("active", "white")])
        self.style.configure("Submit.TButton", font=("Arial", 16), padding=10, background="lightblue")
        self.style.map("Submit.TButton", background=[("active", "blue")], foreground=[("active", "white")])

        # UI Elements
        self.label = tk.Label(root, text="Enter a stock ticker:", font=("Arial", 18, "bold"), bg="#f0f8ff")
        self.label.grid(row=0, column=0, sticky="nsew", pady=10)

        self.entry = tk.Entry(root, font=("Arial", 16), relief="solid", bd=2, justify="center")
        self.entry.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.entry.bind("<Return>", lambda event: self.add_ticker())

        self.add_button = ttk.Button(root, text="Add Ticker", command=self.add_ticker, style="Add.TButton")
        self.add_button.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        self.remove_button = ttk.Button(root, text="Remove Selected", command=self.remove_selected_tickers, style="Remove.TButton")
        self.remove_button.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)

        self.submit_button = ttk.Button(root, text="Plot", command=self.submit_tickers, style="Submit.TButton")
        self.submit_button.grid(row=4, column=0, sticky="nsew", padx=20, pady=10)

        # Label for the Listbox
        self.analyze_label = tk.Label(root, text="Analyze Tickers:", font=("Arial", 18, "bold"), underline=True, bg="#f0f8ff")
        self.analyze_label.grid(row=5, column=0, sticky="nsew", pady=(10, 0))

        self.ticker_listbox = tk.Listbox(
            root, font=("Arial", 18), relief="solid", bd=2, selectmode=tk.MULTIPLE, height=10, exportselection=False
        )
        self.ticker_listbox.grid(row=6, column=0, sticky="nsew", padx=20, pady=10)
        self.ticker_listbox.bind("<<ListboxSelect>>", self.handle_listbox_select)

        # State tracking
        self.selected_tickers = []

    def add_ticker(self):
        """Add a ticker to the list."""
        ticker = self.entry.get().strip().upper()
        if ticker:
            if ticker in self.tickers:
                messagebox.showwarning("Duplicate Entry", "Ticker already added.")
            else:
                self.tickers.append(ticker)
                self.update_ticker_listbox()
            self.entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Input Error", "Please enter a valid ticker.")
        self.entry.focus_set()  # Return focus

    def remove_selected_tickers(self):
        """Remove selected tickers from the list."""
        selected_indices = list(self.ticker_listbox.curselection())
        if not selected_indices:
            messagebox.showwarning("Selection Error", "Please select tickers to remove.")
        else:
            for index in reversed(selected_indices):
                del self.tickers[index]
            self.update_ticker_listbox()
        self.entry.focus_set()  # Return focus

    def update_ticker_listbox(self):
        """Update the listbox to reflect current tickers."""
        self.ticker_listbox.delete(0, tk.END)
        for i, ticker in enumerate(self.tickers):
            self.ticker_listbox.insert(tk.END, f"{i + 1}. {ticker}")

    def handle_listbox_select(self, event):
        """Handle ticker selection."""
        selected_indices = self.ticker_listbox.curselection()
        self.selected_tickers = [self.tickers[i] for i in selected_indices]

    def submit_tickers(self):
        """Submit tickers for processing."""
        if not self.tickers:
            messagebox.showwarning("Input Error", "No tickers added. Please add at least one ticker.")
            self.entry.focus_set()
            return

        # Disable buttons to prevent multiple submissions
        self.add_button["state"] = "disabled"
        self.remove_button["state"] = "disabled"
        self.submit_button["state"] = "disabled"

        def fetch_data():
            """Fetch and process data in a background thread."""
            pe_ratios = self.fetch_pe_ratios(self.tickers)
            self.root.after(0, lambda: self.plot_pe_ratios(pe_ratios))
            self.root.after(0, self.enable_buttons)

        # Start the background thread
        threading.Thread(target=fetch_data, daemon=True).start()

    def enable_buttons(self):
        """Re-enable buttons after processing."""
        self.add_button["state"] = "normal"
        self.remove_button["state"] = "normal"
        self.submit_button["state"] = "normal"
        self.entry.focus_set()

    @staticmethod
    def fetch_pe_ratios(tickers):
        """Fetch both current and forward P/E ratios for a list of stock tickers."""
        pe_ratios = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                current_pe = info.get("trailingPE", None)
                forward_pe = info.get("forwardPE", None)
                pe_ratios[ticker] = {"current": current_pe, "forward": forward_pe}
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                pe_ratios[ticker] = {"current": None, "forward": None}
        return pe_ratios

    @staticmethod
    def plot_pe_ratios(pe_ratios):
        """Create a grouped bar chart to compare current and forward P/E ratios."""
        if not pe_ratios:
            messagebox.showerror("Error", "No data available for plotting.")
            return

        # Filter out tickers with None values
        sorted_ratios = [
            (ticker, values)
            for ticker, values in sorted(pe_ratios.items(), key=lambda item: abs((item[1]["current"] or 0) - (item[1]["forward"] or 0)), reverse=True)
            if values["current"] is not None and values["forward"] is not None
        ]

        if not sorted_ratios:
            messagebox.showerror("Error", "No valid P/E ratio data available for plotting.")
            return

        tickers = [item[0] for item in sorted_ratios]
        current_pe_values = [item[1]["current"] for item in sorted_ratios]
        forward_pe_values = [item[1]["forward"] for item in sorted_ratios]

        plt.figure(figsize=(12, 6))
        width = 0.35
        x = range(len(tickers))

        # Plot bars
        current_bars = plt.bar([pos - width / 2 for pos in x], current_pe_values, width, label="Current P/E", color="skyblue")
        forward_bars = plt.bar([pos + width / 2 for pos in x], forward_pe_values, width, label="Forward P/E", color="lightgreen")

        # Annotate Current P/E values above bars
        for bar, pe in zip(current_bars, current_pe_values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,  # Center of the bar
                bar.get_height() + 0.1,  # Slightly above the bar
                f"{pe:.2f}",  # Format to two decimal places
                ha="center",
                va="bottom",
                fontsize=10,
                color="blue"
            )

        # Annotate Forward P/E values above bars
        for bar, pe in zip(forward_bars, forward_pe_values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,  # Center of the bar
                bar.get_height() + 0.1,  # Slightly above the bar
                f"{pe:.2f}",  # Format to two decimal places
                ha="center",
                va="bottom",
                fontsize=10,
                color="green"
            )

        plt.xlabel("Stock Tickers", fontsize=12)
        plt.ylabel("P/E Ratio", fontsize=12)
        plt.title("Current and Forward P/E Ratios", fontsize=14)
        plt.xticks(x, tickers, rotation=45, ha="right", fontsize=12)
        plt.legend()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = TickerApp(root)
    root.mainloop()
