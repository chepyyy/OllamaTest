import os
import re
import pdfplumber
import subprocess
from fpdf import FPDF

# === Настройки ===
PDF_FOLDER = "pdf_files"
SUMMARY_FOLDER = "summaries"
MODEL_NAME = "rev"
MAX_CHARS = 5000  # можно увеличить

# === Убедимся, что папка summaries существует ===
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

# === Извлекаем текст из PDF ===
def extract_text(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    return full_text

# === Отправляем текст в Ollama ===
def ask_ollama(text):
    prompt = f"Сделай краткий научный обзор следующего текста:\n{text}"
    result = subprocess.run(
        ["ollama", "run", MODEL_NAME],
        input=prompt,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

# === Генерация имени summary_X.pdf ===
def get_next_summary_filename():
    existing = [f for f in os.listdir(SUMMARY_FOLDER) if re.match(r"summary_\d+\.pdf", f)]
    numbers = [int(re.findall(r"\d+", f)[0]) for f in existing] if existing else []
    next_number = max(numbers, default=0) + 1
    return os.path.join(SUMMARY_FOLDER, f"summary_{next_number}.pdf")

# === Сохраняем результат в PDF ===
def save_to_pdf(summaries, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for title, summary in summaries:
        pdf.set_font("Arial", 'B', 14)
        pdf.multi_cell(0, 10, f"{title}:", align='L')
        pdf.ln(1)

        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, summary, align='L')
        pdf.ln(5)

    pdf.output(output_path)
    print(f"✅ Итог сохранён в файл: {output_path}")

# === Главная функция ===
def summarize_all():
    processed_file = "processed.txt"
    processed = set()

    # Загружаем список обработанных файлов, если есть
    if os.path.exists(processed_file):
        with open(processed_file, "r", encoding="utf-8") as f:
            processed = set(line.strip() for line in f.readlines())

    summaries = []

    for filename in os.listdir(PDF_FOLDER):
        if filename.endswith(".pdf") and filename not in processed:
            filepath = os.path.join(PDF_FOLDER, filename)
            print(f"🔍 Обрабатываем: {filename}")
            text = extract_text(filepath)
            trimmed_text = text[:MAX_CHARS]
            summary = ask_ollama(trimmed_text)
            summaries.append((filename, summary))

            # Сохраняем имя обработанного файла
            with open(processed_file, "a", encoding="utf-8") as f:
                f.write(filename + "\n")

    if summaries:
        output_file = get_next_summary_filename()
        save_to_pdf(summaries, output_file)
    else:
        print("✅ Все файлы уже обработаны — новых PDF нет.")

# === Запуск ===
if __name__ == "__main__":
    summarize_all()
