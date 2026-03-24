from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import sys

def create_numbered_pdfs(max_number=100):
    width, height = A4
    font_size = 200  # 大きなフォントサイズで番号を表示

    output_dir = "output_pdfs"
    os.makedirs(output_dir, exist_ok=True)

    for number in range(1, max_number + 1):
        filename = os.path.join(output_dir, f"{number}.pdf")
        c = canvas.Canvas(filename, pagesize=A4)
        c.setFont("Helvetica-Bold", font_size)

        text = str(number)
        text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
        x = (width - text_width) / 2
        y = (height - font_size) / 2

        c.drawString(x, y, text)
        c.showPage()
        c.save()
        print(f"Created: {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            max_number = int(sys.argv[1])
        except ValueError:
            print("数字を入力してください。例: python make_pdfs.py 50")
            sys.exit(1)
    else:
        max_number = 100

    create_numbered_pdfs(max_number)

