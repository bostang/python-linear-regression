import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import math

# Tarif listrik PLN R1/1300VA per kWh
TARIFF_RATE = 1444.70

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
        print(f"\n[ERROR] File '{csv_file_path}' tidak ditemukan.")
        raise
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")
        raise

def calculate_cost_and_usage(initial_capacity, target_day, daily_usage_rate):
    """
    Menghitung total pemakaian listrik, sisa kWh, dan estimasi biaya.
    """
    # Hitung sisa listrik menggunakan input pengguna dan rata-rata pemakaian harian
    remaining_kwh_from_user_input = initial_capacity - (daily_usage_rate * (target_day - 1))
    
    # Total pemakaian dihitung berdasarkan rata-rata harian
    total_usage = daily_usage_rate * target_day
    total_usage = max(0, total_usage)
    
    estimated_cost = total_usage * TARIFF_RATE

    # Perhitungan hari habis dari input pengguna
    day_at_zero_from_user_input = initial_capacity / daily_usage_rate
    day_at_zero_rounded = math.floor(day_at_zero_from_user_input)
    
    return remaining_kwh_from_user_input, total_usage, estimated_cost, day_at_zero_rounded

def create_visual_graph(initial_capacity, target_day, csv_file_path):
    """
    Membuat dan menampilkan grafik regresi linear di jendela Matplotlib terpisah.
    """
    try:
        # Dapatkan model dan prediksi dari fungsi utama
        model, df_full, predicted_y_historical, daily_usage_rate, day_at_zero_exact_historical = \
            get_regression_model_and_predictions(csv_file_path, target_day)
        
        # --- PERHITUNGAN UNTUK GARIS ESTIMASI DARI INPUT PENGGUNA ---
        slope_from_historical_model = model.coef_[0]
        c_new = initial_capacity - slope_from_historical_model * 1
        predicted_y_from_user_line = slope_from_historical_model * target_day + c_new
        day_at_zero_exact_user_line = -c_new / slope_from_historical_model
        
        # --- Visualisasi dengan Matplotlib ---
        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot data asli dari CSV
        ax.scatter(df_full['day'], df_full['electricity_kWh_left'], s=100, color='blue', label='Data Asli (Historis)')
        
        # Plot titik awal dari input pengguna
        ax.scatter([1], [initial_capacity], s=150, color='orange', zorder=5, label='Input Kapasitas Awal (Hari ke-1)')
        ax.annotate(f'{initial_capacity:.2f} kWh', (1, initial_capacity),
                     textcoords="offset points", xytext=(0, 10), ha='center',
                     bbox=dict(boxstyle="round,pad=0.3", fc='orange', alpha=0.5))

        # Garis Regresi Historis (untuk referensi)
        max_x_plot_historical = df_full['day'].max() + 5
        line_x_historical = np.linspace(df_full['day'].min(), max_x_plot_historical, 100)
        line_y_historical = model.predict(pd.DataFrame(line_x_historical, columns=['day']))
        ax.plot(line_x_historical, line_y_historical, color='gray', linestyle=':', alpha=0.5, label='Garis Regresi Historis')

        # Garis Estimasi (dari Input Pengguna)
        max_x_user_line = max(target_day, day_at_zero_exact_user_line) * 1.05 if day_at_zero_exact_user_line is not None else target_day + 5
        x_vals_user_line = np.linspace(1, max_x_user_line, 100)
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

    except Exception as e:
        print(f"[ERROR] Tidak dapat membuat grafik: {e}")


def main():
    """
    Fungsi utama untuk menjalankan program dalam mode CLI.
    """
    print("\n=============================================")
    print("ANALISIS DAN PREDIKSI PEMAKAIAN LISTRIK (CLI)")
    print("=============================================\n")

    try:
        # Mengambil input dari pengguna
        initial_capacity = float(input("Masukkan Kapasitas Listrik Hari ke-1 (kWh): "))
        target_day = int(input("Masukkan Hari Prediksi: "))
        csv_file_path = input("Masukkan jalur file data historis (cth: data/electricity_usage.csv): ")

        # Lakukan analisis regresi
        model, df_full, predicted_y_historical, daily_usage_rate, day_at_zero_exact_historical = \
            get_regression_model_and_predictions(csv_file_path, target_day)

        # Lakukan perhitungan biaya dan sisa listrik
        remaining_kwh, total_usage, estimated_cost, day_at_zero_rounded = \
            calculate_cost_and_usage(initial_capacity, target_day, daily_usage_rate)

        # Tampilkan hasil
        print("\n--- HASIL ANALISIS ---")
        print(f"Pemakaian Listrik per Hari (estimasi): {daily_usage_rate:.2f} kWh")
        print(f"Sisa Listrik pada Hari ke-{target_day}: {remaining_kwh:.2f} kWh")
        print(f"Estimasi Biaya ({target_day} hari): Rp {estimated_cost:,.2f}")
        print(f"Listrik diprediksi habis pada hari ke-{day_at_zero_rounded}")
        
        # Opsi untuk menampilkan grafik
        show_graph = input("\nApakah Anda ingin melihat grafik prediksi? (y/n): ")
        if show_graph.lower() == 'y':
            create_visual_graph(initial_capacity, target_day, csv_file_path)

    except ValueError:
        print("\n[ERROR] Masukan tidak valid. Pastikan Anda memasukkan angka yang benar.")
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")

if __name__ == '__main__':
    main()