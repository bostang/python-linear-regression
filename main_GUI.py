import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.linear_model import LinearRegression
import math

# Tarif listrik PLN R1/1300VA per kWh
TARIFF_RATE = 1444.70

# --- Fungsi Logika Inti ---
def get_regression_model_and_predictions(csv_file_path, day_to_predict):
    """
    Memuat data dari CSV, melatih model regresi, dan melakukan prediksi.
    Gradien garis ditentukan HANYA dari data historis.
    """
    try:
        df_csv = pd.read_csv(csv_file_path)
        if 'usage_per_day' in df_csv.columns:
            df_csv = df_csv.drop(columns=['usage_per_day'])
        df_csv = df_csv.dropna()

        if df_csv.empty:
            raise ValueError("File CSV tidak memiliki data yang valid untuk analisis.")

        # Siapkan data untuk model regresi (hanya dari CSV)
        X = df_csv[['day']]
        y = df_csv['electricity_kWh_left']

        # Buat dan latih model regresi linear
        model = LinearRegression()
        model.fit(X, y)

        # Prediksi sisa kWh untuk hari target
        predicted_X = pd.DataFrame([day_to_predict], columns=['day'])
        predicted_y = model.predict(predicted_X)[0]

        # Hitung pemakaian harian (slope dari model)
        daily_usage_rate = -model.coef_[0]

        # Hitung hari saat listrik habis (kWh = 0)
        day_at_zero_exact = None
        if model.coef_[0] != 0:
            day_at_zero_exact = (0 - model.intercept_) / model.coef_[0]
        
        return model, df_csv, predicted_y, daily_usage_rate, day_at_zero_exact

    except FileNotFoundError:
        messagebox.showerror("Error", f"File '{csv_file_path}' tidak ditemukan.")
        raise
    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
        raise

def calculate_estimation_values():
    """
    Mengambil input dari pengguna, melakukan perhitungan, dan menampilkan hasilnya di GUI.
    """
    try:
        initial_capacity = float(entry_initial_capacity.get())
        target_day = int(entry_target_day.get())
        
        if initial_capacity < 0 or target_day < 1:
            messagebox.showerror("Input Invalid", "Kapasitas awal tidak boleh negatif dan hari prediksi harus lebih dari 0.")
            return

        csv_path = entry_csv_path.get()
        
        # Dapatkan model dan prediksi dari fungsi yang diperbaiki
        model, df_full, predicted_y_historical, daily_usage_rate, day_at_zero_exact_historical = \
            get_regression_model_and_predictions(csv_path, target_day)

        # Hitung sisa listrik menggunakan input pengguna dan rata-rata pemakaian harian
        # Kita menggunakan (target_day - 1) karena initial_capacity adalah untuk Hari ke-1, bukan Hari ke-0
        remaining_kwh_from_user_input = initial_capacity - (daily_usage_rate * (target_day - 1))
        
        # Total pemakaian dihitung berdasarkan rata-rata harian (ini sudah benar)
        total_usage = daily_usage_rate * target_day
        total_usage = max(0, total_usage)
        
        estimated_cost = total_usage * TARIFF_RATE

        # Perhitungan hari habis dari input pengguna
        day_at_zero_from_user_input = initial_capacity / daily_usage_rate
        day_at_zero_rounded = math.floor(day_at_zero_from_user_input)
        
        # Menampilkan hasil
        usage_per_day_label.config(text=f"Pemakaian Listrik per Hari (estimasi): {daily_usage_rate:.2f} kWh")
        result_label.config(text=f"Sisa Listrik pada Hari ke-{target_day}: {remaining_kwh_from_user_input:.2f} kWh")
        cost_label.config(text=f"Estimasi Biaya ({target_day} hari): Rp {estimated_cost:,.2f}")
        empty_label.config(text=f"Listrik diprediksi habis pada hari ke-{day_at_zero_rounded}")
        
    except ValueError:
        messagebox.showerror("Input Invalid", "Mohon masukkan angka yang valid.")
    except FileNotFoundError:
        pass # Error ditangani oleh fungsi get_regression_model_and_predictions
    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan: {e}")

def generate_graph():
    """
    Membuat dan menampilkan grafik regresi linear di jendela Matplotlib terpisah.
    Ditambahkan garis estimasi sejajar yang melewati titik input pengguna.
    """
    try:
        initial_capacity = float(entry_initial_capacity.get())
        target_day = int(entry_target_day.get())
        csv_path = entry_csv_path.get()

        if initial_capacity < 0 or target_day < 1:
            messagebox.showerror("Input Invalid", "Kapasitas awal tidak boleh negatif dan hari prediksi harus lebih dari 0.")
            return

        # Dapatkan model dan prediksi dari fungsi yang diperbaiki
        model, df_full, predicted_y, daily_usage_rate, day_at_zero_exact_historical = \
            get_regression_model_and_predictions(csv_path, target_day)
        
        # --- PERHITUNGAN BARU UNTUK GARIS ESTIMASI DARI INPUT PENGGUNA ---
        # Gradien diambil dari model historis
        slope_from_historical_model = model.coef_[0]

        # Hitung y-intercept baru agar garis melewati (1, initial_capacity)
        # initial_capacity = slope_from_historical_model * 1 + c_new
        c_new = initial_capacity - slope_from_historical_model * 1

        # Prediksi y untuk target_day menggunakan garis estimasi baru ini
        predicted_y_from_user_line = slope_from_historical_model * target_day + c_new

        # Hitung hari saat listrik habis untuk garis estimasi baru ini
        day_at_zero_exact_user_line = None
        if slope_from_historical_model != 0:
            day_at_zero_exact_user_line = -c_new / slope_from_historical_model
        # --- AKHIR PERHITUNGAN BARU ---

        # --- Visualisasi dengan Matplotlib ---
        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot data asli dari CSV
        ax.scatter(df_full['day'], df_full['electricity_kWh_left'], s=100, color='blue', label='Data Asli (Historis)')
        
        # Plot titik awal dari input pengguna
        ax.scatter([1], [initial_capacity], s=150, color='orange', zorder=5, label='Input Kapasitas Awal (Hari ke-1)')
        ax.annotate(f'{initial_capacity:.2f} kWh', (1, initial_capacity),
                     textcoords="offset points", xytext=(0, 10), ha='center',
                     bbox=dict(boxstyle="round,pad=0.3", fc='orange', alpha=0.5))


        # Buat rentang hari untuk garis regresi utama (dari data historis)
        # Akan digambar di background, tidak langsung dari titik oranye
        max_x_plot_historical = df_full['day'].max() + 5
        if day_at_zero_exact_historical is not None and day_at_zero_exact_historical > max_x_plot_historical:
            max_x_plot_historical = day_at_zero_exact_historical * 1.05
        if target_day > max_x_plot_historical:
            max_x_plot_historical = target_day * 1.05

        # Garis Regresi Historis (digambar di background, tidak terpengaruh input_initial_capacity)
        line_x_historical = np.linspace(df_full['day'].min(), max_x_plot_historical, 100)
        line_y_historical = model.predict(pd.DataFrame(line_x_historical, columns=['day']))
        ax.plot(line_x_historical, line_y_historical, color='gray', linestyle=':', alpha=0.5, label='Garis Regresi Historis')


        # --- GARIS ESTIMASI BARU DARI INPUT PENGGUNA ---
        # Rentang garis estimasi dari input pengguna
        max_x_user_line = max(target_day, day_at_zero_exact_user_line) * 1.05 if day_at_zero_exact_user_line is not None else target_day + 5
        x_vals_user_line = np.linspace(1, max_x_user_line, 100) # Mulai dari Hari ke-1
        y_vals_user_line = slope_from_historical_model * x_vals_user_line + c_new
        ax.plot(x_vals_user_line, y_vals_user_line, color='red', linestyle='--', label='Garis Estimasi (dari Input)')

        # Titik prediksi pada Hari target (dari garis estimasi baru)
        ax.scatter(target_day, predicted_y_from_user_line, s=150, color='green', zorder=5, label=f'Prediksi Hari ke-{target_day}')
        ax.annotate(f'{predicted_y_from_user_line:.2f} kWh', (target_day, predicted_y_from_user_line),
                     textcoords="offset points", xytext=(-15, -20), ha='center',
                     bbox=dict(boxstyle="round,pad=0.3", fc='yellow', alpha=0.5))

        # Titik saat listrik habis (dari garis estimasi baru)
        if day_at_zero_exact_user_line is not None and day_at_zero_exact_user_line >= 0:
            ax.scatter(day_at_zero_exact_user_line, 0, s=150, color='purple', zorder=5, label=f'Hari ke-{math.floor(day_at_zero_exact_user_line)} (0 kWh)')
            ax.annotate(f'Mencapai 0 kWh: Hari ke-{math.floor(day_at_zero_exact_user_line)}', (day_at_zero_exact_user_line, 0),
                         textcoords="offset points", xytext=(0, 10), ha='center',
                         bbox=dict(boxstyle="round,pad=0.3", fc='cyan', alpha=0.5))
        
        ax.set_title('Prediksi Kapasitas Listrik dengan Regresi Linear')
        ax.set_xlabel('Hari ke-')
        ax.set_ylabel('Kapasitas Listrik (kWh)')
        ax.legend()
        ax.grid(True)
        ax.axhline(0, color='black', linewidth=0.5, linestyle='-')
        fig.tight_layout()
        plt.show()

    except FileNotFoundError:
        pass # Error sudah ditangani di fungsi get_regression_model_and_predictions
    except ValueError:
        messagebox.showerror("Input Invalid", "Mohon masukkan angka yang valid untuk kapasitas dan hari.")
    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan saat membuat grafik: {e}")

def browse_csv_file():
    """Membuka dialog untuk memilih file CSV."""
    filename = filedialog.askopenfilename(
        title="Pilih file CSV",
        filetypes=(("CSV files", "*.csv"), ("all files", "*.*"))
    )
    if filename:
        entry_csv_path.delete(0, tk.END)
        entry_csv_path.insert(0, filename)

# --- Pengaturan GUI Utama ---
root = tk.Tk()
root.title("Estimasi Pemakaian Listrik")
root.geometry("600x600") # Ukuran jendela disesuaikan
root.resizable(True, True)

# Bingkai untuk input
input_frame = tk.LabelFrame(root, text="Input Data", padx=10, pady=10)
input_frame.pack(pady=10, padx=10, fill="x")

# Input Kapasitas Hari ke-1
tk.Label(input_frame, text="Kapasitas Listrik Hari ke-1 (kWh):").grid(row=0, column=0, sticky="w", pady=5)
entry_initial_capacity = tk.Entry(input_frame)
entry_initial_capacity.insert(0, "23.86") # Nilai default
entry_initial_capacity.grid(row=0, column=1, sticky="ew")

# Input Hari Prediksi
tk.Label(input_frame, text="Hari Prediksi:").grid(row=1, column=0, sticky="w", pady=5)
entry_target_day = tk.Entry(input_frame)
entry_target_day.insert(0, "20") # Nilai default
entry_target_day.grid(row=1, column=1, sticky="ew")

# Input Path File CSV
tk.Label(input_frame, text="File Data Historis (CSV):").grid(row=2, column=0, sticky="w", pady=5)
entry_csv_path = tk.Entry(input_frame)
entry_csv_path.insert(0, "data/electricity_usage.csv") # Nilai default
entry_csv_path.grid(row=2, column=1, sticky="ew")
browse_button = tk.Button(input_frame, text="Browse", command=browse_csv_file)
browse_button.grid(row=2, column=2, sticky="ew")

input_frame.grid_columnconfigure(1, weight=1) # Agar kolom input melebar

# Tombol untuk memulai perhitungan
calculate_button = tk.Button(root, text="Hitung Estimasi", command=calculate_estimation_values)
calculate_button.pack(pady=5, padx=10, fill="x")

# Tombol untuk generate grafik
graph_button = tk.Button(root, text="Generate Grafik", command=generate_graph)
graph_button.pack(pady=5, padx=10, fill="x")

# Bingkai untuk output
output_frame = tk.LabelFrame(root, text="Hasil Analisis", padx=10, pady=10)
output_frame.pack(pady=10, padx=10, fill="x")

# Label untuk hasil prediksi
usage_per_day_label = tk.Label(output_frame, text="", font=("Helvetica", 11), anchor="w")
usage_per_day_label.pack(pady=2, fill="x")

result_label = tk.Label(output_frame, text="", font=("Helvetica", 11), anchor="w")
result_label.pack(pady=2, fill="x")

cost_label = tk.Label(output_frame, text="", font=("Helvetica", 11), anchor="w")
cost_label.pack(pady=2, fill="x")

empty_label = tk.Label(output_frame, text="", font=("Helvetica", 11), anchor="w")
empty_label.pack(pady=2, fill="x")

# Jalankan program
root.mainloop()