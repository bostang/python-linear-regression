import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import math

# Tarif listrik PLN R1/1300VA per kWh
TARIFF_RATE = 1444.70

def perform_regression_and_predict(df, day_to_predict):
    """
    Memproses data, melatih model regresi, dan melakukan prediksi.
    
    Mengembalikan model terlatih dan semua nilai yang diprediksi.
    """
    # Pastikan data tidak kosong
    if df.empty:
        raise ValueError("Dataframe tidak memiliki data yang valid untuk analisis.")

    # Siapkan data untuk model
    X = df[['day']]
    y = df['electricity_kWh_left']

    # Buat dan latih model regresi linear
    model = LinearRegression()
    model.fit(X, y)

    # Prediksi sisa kWh untuk hari yang ditentukan
    predicted_X = pd.DataFrame([day_to_predict], columns=['day'])
    predicted_y = model.predict(predicted_X)[0]

    # Hitung hari saat listrik habis (kWh = 0)
    day_at_zero_exact = None
    if model.coef_[0] != 0:
        day_at_zero_exact = (0 - model.intercept_) / model.coef_[0]
    
    return model, predicted_y, day_at_zero_exact

def calculate_cost_and_usage(model, predicted_y, day_to_predict):
    """
    Menghitung total pemakaian listrik dan estimasi biaya.
    """
    # Total pemakaian = (Kapasitas Awal) - (Kapasitas Sisa)
    initial_capacity = model.intercept_
    total_usage = initial_capacity - predicted_y
    
    # Hitung estimasi biaya
    estimated_cost = total_usage * TARIFF_RATE
    
    return total_usage, estimated_cost

def create_visual_graph(df, model, predicted_y, day_to_predict, day_at_zero_exact):
    """
    Membuat grafik visual dari hasil regresi.
    """
    plt.figure(figsize=(12, 8))

    # Plot data asli
    plt.scatter(df['day'], df['electricity_kWh_left'], s=100, color='blue', label='Data Asli')

    # Buat rentang hari untuk garis regresi
    max_x_plot = day_to_predict + 5
    if day_at_zero_exact is not None and day_at_zero_exact > max_x_plot:
        max_x_plot = day_at_zero_exact * 1.05

    line_x = np.linspace(df['day'].min(), max_x_plot, 100)
    line_y = model.predict(pd.DataFrame(line_x, columns=['day']))
    plt.plot(line_x, line_y, color='red', linestyle='--', label='Garis Regresi')

    # Plot titik prediksi untuk hari yang ditentukan
    plt.scatter(day_to_predict, predicted_y, s=150, color='green', zorder=5, label=f'Prediksi Hari ke-{day_to_predict}')
    plt.annotate(f'{predicted_y:.2f} kWh', (day_to_predict, predicted_y),
                 textcoords="offset points", xytext=(-15, -20), ha='center',
                 bbox=dict(boxstyle="round,pad=0.3", fc='yellow', alpha=0.5))

    # Plot titik saat listrik habis
    if day_at_zero_exact is not None and day_at_zero_exact >= 0:
        plt.scatter(day_at_zero_exact, 0, s=150, color='purple', zorder=5, label=f'Hari ke-{day_at_zero_exact:.2f} (0 kWh)')
        plt.annotate(f'Mencapai 0 kWh: Hari ke-{math.floor(day_at_zero_exact)}', (day_at_zero_exact, 0),
                     textcoords="offset points", xytext=(0, 10), ha='center',
                     bbox=dict(boxstyle="round,pad=0.3", fc='cyan', alpha=0.5))

    # Pengaturan grafik
    plt.title('Prediksi Kapasitas Listrik dengan Regresi Linear')
    plt.xlabel('Hari ke-')
    plt.ylabel('Kapasitas Listrik (kWh)')
    plt.legend()
    plt.grid(True)
    plt.axhline(0, color='black', linewidth=0.5, linestyle='-')
    plt.tight_layout()
    plt.show()

# --- Fungsi Utama ---
def main():
    """
    Fungsi utama untuk menjalankan seluruh analisis.
    """
    csv_file_path = 'data/electricity_usage.csv'
    day_to_predict = 20

    try:
        df = pd.read_csv(csv_file_path)
        if 'usage_per_day' in df.columns:
            df = df.drop(columns=['usage_per_day'])
        df = df.dropna()

        # Panggil fungsi untuk regresi dan prediksi
        model, predicted_y, day_at_zero_exact = perform_regression_and_predict(df, day_to_predict)

        # Panggil fungsi untuk menghitung biaya
        total_usage, estimated_cost = calculate_cost_and_usage(model, predicted_y, day_to_predict)

        # Panggil fungsi untuk membuat grafik
        create_visual_graph(df, model, predicted_y, day_to_predict, day_at_zero_exact)

        # Tampilkan hasil di konsol
        print(f"Prediksi sisa kapasitas listrik pada hari ke-{day_to_predict} adalah: {predicted_y:.2f} kWh")
        if day_at_zero_exact is not None and day_at_zero_exact >= 0:
            print(f"Kapasitas listrik diprediksi akan mencapai 0 kWh pada hari ke: {math.floor(day_at_zero_exact)}")
        print(f"Estimasi total pemakaian listrik selama {day_to_predict} hari adalah: {total_usage:.2f} kWh")
        print(f"Estimasi biaya listrik selama {day_to_predict} hari adalah: Rp {estimated_cost:,.2f}")

    except (FileNotFoundError, ValueError) as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == '__main__':
    main()