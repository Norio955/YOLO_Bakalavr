import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
from ultralytics import YOLO
import os
import datetime

class RoadSignDetectorApp:
    def __init__(self, root):
        # Налаштування головного вікна програми
        self.root = root
        self.root.title("YOLO Road Signs Detector (Diplom Work)")
        self.root.geometry("1100x750")

        # Змінні для збереження стану програми
        self.model = None
        self.cap = None
        self.is_running = False
        self.is_paused = False
        self.image_path = None
        self.last_frame_to_save = None

        # Створюємо папку для збереження результатів, якщо її ще немає
        if not os.path.exists("saved_results"):
            os.makedirs("saved_results")

        # Намагаємося підтягнути модель автоматично при старті
        try:
            self.model = YOLO("best.pt")
            print("Модель best.pt завантажено автоматично.")
        except:
            print("Модель не знайдено.")
            # Якщо файлу немає поруч, через пів секунди нагадаємо про це користувачу
            self.root.after(500, self.show_startup_warning)

        # Опис елементів інтерфейсу: текстові мітки та екрани для зображень
        tk.Label(root, text="Source (Original)", font=("Arial", 14, "bold")).place(x=150, y=20)
        tk.Label(root, text="Detection Result", font=("Arial", 14, "bold")).place(x=750, y=20)

        self.canvas_before = tk.Canvas(root, width=400, height=400, bg="#e0e0e0", relief="sunken")
        self.canvas_before.place(x=50, y=60)

        self.canvas_after = tk.Canvas(root, width=400, height=400, bg="#e0e0e0", relief="sunken")
        self.canvas_after.place(x=650, y=60)

        # Кнопки для керування відтворенням відео
        self.btn_pause = tk.Button(root, text="⏸ Pause", bg="#ffecb3", font=("Arial", 11), command=self.toggle_pause,
                                   state="disabled")
        self.btn_pause.place(x=500, y=200, width=100, height=40)

        self.btn_stop = tk.Button(root, text="⏹ Stop", bg="#ffcdd2", font=("Arial", 11), command=self.stop_video,
                                  state="disabled")
        self.btn_stop.place(x=500, y=260, width=100, height=40)

        # Секція кнопок для роботи з фотографіями
        tk.Label(root, text="Photo Mode:", font=("Arial", 10, "bold")).place(x=50, y=480)
        btn_upload_photo = tk.Button(root, text="📂 Upload Photo", bg="#b3e5fc", command=self.upload_photo)
        btn_upload_photo.place(x=50, y=510, width=140, height=35)

        btn_process_photo = tk.Button(root, text="▶ Process Photo", bg="#b3e5fc", command=self.process_image)
        btn_process_photo.place(x=200, y=510, width=140, height=35)

        # Секція кнопок для відео та прямого ефіру
        tk.Label(root, text="Video / Live Mode:", font=("Arial", 10, "bold")).place(x=50, y=560)
        btn_upload_video = tk.Button(root, text="🎬 Upload Video", bg="#ffe0b2", command=self.upload_video)
        btn_upload_video.place(x=50, y=590, width=140, height=35)

        btn_go_live = tk.Button(root, text="🎥 Go Live (Cam)", bg="#ffe0b2", command=self.go_live)
        btn_go_live.place(x=200, y=590, width=140, height=35)

        # Кнопка для ручного завантаження файлу моделі
        btn_upload_model = tk.Button(root, text="⚙ Load Model", bg="#c8e6c9", command=self.load_custom_model)
        btn_upload_model.place(x=50, y=650, width=140, height=30)

        # Поле для виведення текстових результатів розпізнавання
        tk.Label(root, text="Logs / Statistics:", font=("Arial", 10)).place(x=650, y=480)
        self.text_results = tk.Text(root, width=50, height=8, bg="#f5f5f5")
        self.text_results.place(x=650, y=510)

        # Кнопка для збереження поточного результату у файл
        btn_save = tk.Button(root, text="💾 Save (Img + Txt)", bg="#cfd8dc", font=("Arial", 10, "bold"),
                             command=self.save_results)
        btn_save.place(x=650, y=660, width=200, height=40)

    def show_startup_warning(self):
        # Виводимо підказку, якщо користувач забув покласти модель у папку
        messagebox.showwarning(
            "Увага",
            "⚠️ Модель не знайдено!\n\nДля початку роботи натисніть кнопку 'Load Model' та оберіть файл .pt."
        )

    def load_custom_model(self):
        # Відкриваємо вікно вибору файлу для завантаження ваг нейромережі
        path = filedialog.askopenfilename(filetypes=[("YOLO Model", "*.pt")])
        if path:
            try:
                self.model = YOLO(path)
                messagebox.showinfo("Успіх", f"Модель успішно завантажено:\n{path.split('/')[-1]}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося завантажити модель:\n{e}")

    def upload_photo(self):
        # Завантажуємо зображення та показуємо його у лівому вікні
        self.stop_video()
        self.image_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if self.image_path:
            img = Image.open(self.image_path)
            img.thumbnail((400, 400))
            self.photo_before = ImageTk.PhotoImage(img)
            self.canvas_before.create_image(200, 200, image=self.photo_before)

            # Очищуємо старі результати перед новим розпізнаванням
            self.canvas_after.delete("all")
            self.text_results.delete(1.0, tk.END)
            self.last_frame_to_save = None

    def process_image(self):
        # Запускаємо нейромережу для аналізу завантаженого фото
        if not self.model:
            messagebox.showerror("Помилка", "Спочатку завантажте модель (Load Model)!")
            return
        if not self.image_path:
            messagebox.showinfo("Інфо", "Спочатку завантажте фото!")
            return

        results = self.model.predict(self.image_path)
        res_plot = results[0].plot()

        # Зберігаємо результат в пам'яті на випадок натискання кнопки "Save"
        self.last_frame_to_save = res_plot

        # Перетворюємо колір з OpenCV (BGR) у формат для інтерфейсу (RGB)
        res_rgb = cv2.cvtColor(res_plot, cv2.COLOR_BGR2RGB)
        res_pil = Image.fromarray(res_rgb)
        res_pil.thumbnail((400, 400))

        self.photo_after = ImageTk.PhotoImage(res_pil)
        self.canvas_after.create_image(200, 200, image=self.photo_after)

        self.log_results(results[0])

    def upload_video(self):
        # Вибираємо відеофайл та готуємо систему до його відтворення
        if not self.model:
            messagebox.showerror("Помилка", "Спочатку завантажте модель (Load Model)!")
            return

        self.stop_video()
        self.canvas_before.delete("all")
        self.canvas_after.delete("all")
        self.text_results.delete(1.0, tk.END)

        video_path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if video_path:
            self.cap = cv2.VideoCapture(video_path)
            self.start_video_loop()

    def go_live(self):
        # Підключаємося до веб-камери для детекції в реальному часі
        if not self.model:
            messagebox.showerror("Помилка", "Спочатку завантажте модель (Load Model)!")
            return

        self.stop_video()
        self.canvas_before.delete("all")
        self.canvas_after.delete("all")
        self.text_results.delete(1.0, tk.END)

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Camera not found!")
            return
        self.start_video_loop()

    def start_video_loop(self):
        # Активуємо кнопки керування та запускаємо цикл обробки кадрів
        self.is_running = True
        self.is_paused = False
        self.btn_pause.config(state="normal", text="⏸ Pause")
        self.btn_stop.config(state="normal")
        self.video_loop()

    def video_loop(self):
        # Основний цикл програми: читаємо кадр, обробляємо його YOLO та оновлюємо екран
        if not self.is_running or not self.cap or not self.cap.isOpened():
            return

        if self.is_paused:
            self.root.after(100, self.video_loop)
            return

        ret, frame = self.cap.read()
        if ret:
            # Обробка кадру моделлю (використовуємо менший розмір для швидкості)
            results = self.model(frame, imgsz=320, conf=0.25, verbose=False)
            annotated_frame = results[0].plot()
            self.last_frame_to_save = annotated_frame

            # Оновлюємо ліве (оригінал) та праве (результат) вікна
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo_in_ref = ImageTk.PhotoImage(self.resize_for_canvas(frame_rgb))
            self.canvas_before.create_image(200, 200, image=self.photo_in_ref)

            annotated_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            self.photo_out_ref = ImageTk.PhotoImage(self.resize_for_canvas(annotated_rgb))
            self.canvas_after.create_image(200, 200, image=self.photo_out_ref)

            # Рекурсивно викликаємо функцію для наступного кадру
            self.root.after(1, self.video_loop)
        else:
            self.stop_video()

    def save_results(self):
        # Зберігаємо скріншот з рамками та текстовий звіт у папку результатів
        if self.last_frame_to_save is None:
            messagebox.showwarning("Warning", "Немає результату для збереження!")
            return

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        base_filename = f"saved_results/result_{timestamp}"

        # Записуємо зображення
        img_filename = base_filename + ".jpg"
        cv2.imwrite(img_filename, self.last_frame_to_save)

        # Записуємо текстовий лог
        txt_filename = base_filename + ".txt"
        log_content = self.text_results.get(1.0, tk.END).strip()

        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(f"Date/Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Image File: {img_filename}\n")
            f.write("-" * 20 + "\n")
            f.write("DETECTED OBJECTS:\n")
            f.write(log_content + "\n")

        messagebox.showinfo("Saved", f"Файли збережено:\n1. {img_filename}\n2. {txt_filename}")

    def toggle_pause(self):
        # Ставимо відео на паузу або відновлюємо відтворення
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.config(text="▶ Resume")
            if self.last_frame_to_save is not None:
                self.text_results.insert(tk.END, "\n[PAUSED]\n")
        else:
            self.btn_pause.config(text="⏸ Pause")

    def stop_video(self):
        # Зупиняємо всі процеси, вимикаємо камеру та блокуємо кнопки
        self.is_running = False
        self.is_paused = False
        if self.cap:
            self.cap.release()
        self.cap = None
        self.btn_pause.config(state="disabled")
        self.btn_stop.config(state="disabled")

    def resize_for_canvas(self, cv_image):
        # Змінюємо розмір картинки так, щоб вона гарно вписалася в рамки інтерфейсу
        pil_img = Image.fromarray(cv_image)
        pil_img.thumbnail((400, 400))
        return pil_img

    def log_results(self, result):
        # Отримуємо назви та впевненість для кожного знайденого об'єкта
        self.text_results.delete(1.0, tk.END)
        if len(result.boxes) == 0:
            self.text_results.insert(tk.END, "No objects detected.")
            return

        self.text_results.insert(tk.END, f"Speed: {result.speed['inference']:.1f}ms\n")
        self.text_results.insert(tk.END, "-" * 20 + "\n")

        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = result.names[cls]
            self.text_results.insert(tk.END, f"{name}: {conf * 100:.1f}%\n")

if __name__ == "__main__":
    # Запуск головного циклу обробки подій вікна
    root = tk.Tk()
    app = RoadSignDetectorApp(root)
    root.mainloop()