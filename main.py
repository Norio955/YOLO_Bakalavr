import os
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO

# Імпорти для локального логування
from logger_config import app_logger, get_user_error_message


class RoadSignDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Road Signs Detector (Diplom Work)")
        self.root.geometry("1100x750")

        self.model = None
        self.cap = None
        self.is_running = False
        self.is_paused = False
        self.image_path = None
        self.last_frame_to_save = None

        if not os.path.exists("saved_results"):
            os.makedirs("saved_results")

        # Перехоплення помилок при старті
        try:
            app_logger.debug("Спроба автоматичного завантаження best.pt")
            self.model = YOLO("best.pt")
            app_logger.info("Модель best.pt завантажено автоматично.")
        except FileNotFoundError as e:
            self.handle_error("ERR-MDL-201", f"Файл моделі не знайдено: {e}")
            self.root.after(500, self.show_startup_warning)
        except Exception as e:
            self.handle_error("ERR-SYS-500", f"Помилка при ініціалізації моделі: {e}")

        # Інтерфейс
        tk.Label(root, text="Source (Original)", font=("Arial", 14, "bold")).place(x=150, y=20)
        tk.Label(root, text="Detection Result", font=("Arial", 14, "bold")).place(x=750, y=20)

        self.canvas_before = tk.Canvas(root, width=400, height=400, bg="#e0e0e0", relief="sunken")
        self.canvas_before.place(x=50, y=60)
        self.canvas_after = tk.Canvas(root, width=400, height=400, bg="#e0e0e0", relief="sunken")
        self.canvas_after.place(x=650, y=60)

        self.btn_pause = tk.Button(
            root, text="⏸ Pause", bg="#ffecb3", font=("Arial", 11), command=self.toggle_pause, state="disabled"
        )
        self.btn_pause.place(x=500, y=200, width=100, height=40)
        self.btn_stop = tk.Button(
            root, text="⏹ Stop", bg="#ffcdd2", font=("Arial", 11), command=self.stop_video, state="disabled"
        )
        self.btn_stop.place(x=500, y=260, width=100, height=40)

        tk.Label(root, text="Photo Mode:", font=("Arial", 10, "bold")).place(x=50, y=480)
        tk.Button(root, text="📂 Upload Photo", bg="#b3e5fc", command=self.upload_photo).place(
            x=50, y=510, width=140, height=35
        )
        tk.Button(root, text="▶ Process Photo", bg="#b3e5fc", command=self.process_image).place(
            x=200, y=510, width=140, height=35
        )

        tk.Label(root, text="Video / Live Mode:", font=("Arial", 10, "bold")).place(x=50, y=560)
        tk.Button(root, text="🎬 Upload Video", bg="#ffe0b2", command=self.upload_video).place(
            x=50, y=590, width=140, height=35
        )
        tk.Button(root, text="🎥 Go Live (Cam)", bg="#ffe0b2", command=self.go_live).place(
            x=200, y=590, width=140, height=35
        )

        tk.Button(root, text="⚙ Load Model", bg="#c8e6c9", command=self.load_custom_model).place(
            x=50, y=650, width=140, height=30
        )

        tk.Label(root, text="Logs / Statistics:", font=("Arial", 10)).place(x=650, y=480)
        self.text_results = tk.Text(root, width=50, height=8, bg="#f5f5f5")
        self.text_results.place(x=650, y=510)

        tk.Button(
            root, text="💾 Save (Img + Txt)", bg="#cfd8dc", font=("Arial", 10, "bold"), command=self.save_results
        ).place(x=650, y=660, width=200, height=40)

    def handle_error(self, error_code, technical_details):
        # 1. Лог для розробника (у файл та консоль)
        app_logger.error(f"[{error_code}] {technical_details}")

        # 2. Локалізоване повідомлення для користувача
        user_msg = get_user_error_message(error_code)
        messagebox.showerror("Помилка додатка", f"{user_msg}\n\nКод: {error_code}")

    def show_startup_warning(self):
        messagebox.showwarning(
            "Увага", "⚠️ Модель не знайдено!\n\nДля початку роботи натисніть кнопку 'Load Model' та оберіть файл .pt."
        )

    def load_custom_model(self):
        path = filedialog.askopenfilename(filetypes=[("YOLO Model", "*.pt")])
        if path:
            try:
                app_logger.debug(f"Ручне завантаження моделі: {path}")
                self.model = YOLO(path)
                app_logger.info("Кастомна модель успішно завантажена.")
                messagebox.showinfo("Успіх", f"Модель успішно завантажено:\n{path.split('/')[-1]}")
            except Exception as e:
                self.handle_error("ERR-MDL-201", f"Збій завантаження кастомної моделі: {e}")

    def upload_photo(self):
        self.stop_video()
        self.image_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if self.image_path:
            try:
                app_logger.debug(f"Завантаження фото: {self.image_path}")
                img = Image.open(self.image_path)
                img.thumbnail((400, 400))
                self.photo_before = ImageTk.PhotoImage(img)
                self.canvas_before.create_image(200, 200, image=self.photo_before)

                self.canvas_after.delete("all")
                self.text_results.delete(1.0, tk.END)
                self.last_frame_to_save = None
            except Exception as e:
                self.handle_error("ERR-IMG-301", f"Не вдалося прочитати зображення: {e}")

    def process_image(self):
        if not self.model:
            messagebox.showerror("Помилка", "Спочатку завантажте модель (Load Model)!")
            return
        if not self.image_path:
            messagebox.showinfo("Інфо", "Спочатку завантажте фото!")
            return

        try:
            app_logger.info("Запуск розпізнавання фото...")
            results = self.model.predict(self.image_path)
            res_plot = results[0].plot()

            self.last_frame_to_save = res_plot

            res_rgb = cv2.cvtColor(res_plot, cv2.COLOR_BGR2RGB)
            res_pil = Image.fromarray(res_rgb)
            res_pil.thumbnail((400, 400))

            self.photo_after = ImageTk.PhotoImage(res_pil)
            self.canvas_after.create_image(200, 200, image=self.photo_after)

            self.log_results(results[0])
            app_logger.info("Фото успішно оброблено.")
        except Exception as e:
            self.handle_error("ERR-SYS-500", f"Збій під час інференсу (process_image): {e}")

    def upload_video(self):
        if not self.model:
            messagebox.showerror("Помилка", "Спочатку завантажте модель (Load Model)!")
            return

        self.stop_video()
        self.canvas_before.delete("all")
        self.canvas_after.delete("all")
        self.text_results.delete(1.0, tk.END)

        video_path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if video_path:
            try:
                app_logger.debug(f"Запуск відео: {video_path}")
                self.cap = cv2.VideoCapture(video_path)
                if not self.cap.isOpened():
                    raise ValueError("OpenCV не зміг відкрити відеофайл.")
                self.start_video_loop()
            except Exception as e:
                self.handle_error("ERR-VID-401", f"Помилка відкриття відео: {e}")

    def go_live(self):
        if not self.model:
            messagebox.showerror("Помилка", "Спочатку завантажте модель (Load Model)!")
            return

        self.stop_video()
        self.canvas_before.delete("all")
        self.canvas_after.delete("all")
        self.text_results.delete(1.0, tk.END)

        try:
            app_logger.info("Підключення до веб-камери...")
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.handle_error("ERR-CAM-001", "cv2.VideoCapture(0) повернув False.")
                return
            self.start_video_loop()
        except Exception as e:
            self.handle_error("ERR-CAM-001", f"Апаратна помилка камери: {e}")

    def start_video_loop(self):
        self.is_running = True
        self.is_paused = False
        self.btn_pause.config(state="normal", text="⏸ Pause")
        self.btn_stop.config(state="normal")
        self.video_loop()

    def video_loop(self):
        if not self.is_running or not self.cap or not self.cap.isOpened():
            return

        if self.is_paused:
            self.root.after(100, self.video_loop)
            return

        try:
            ret, frame = self.cap.read()
            if ret:
                results = self.model(frame, imgsz=320, conf=0.25, verbose=False)  # type: ignore
                annotated_frame = results[0].plot()
                self.last_frame_to_save = annotated_frame

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.photo_in_ref = ImageTk.PhotoImage(self.resize_for_canvas(frame_rgb))
                self.canvas_before.create_image(200, 200, image=self.photo_in_ref)

                annotated_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                self.photo_out_ref = ImageTk.PhotoImage(self.resize_for_canvas(annotated_rgb))
                self.canvas_after.create_image(200, 200, image=self.photo_out_ref)

                self.root.after(1, self.video_loop)
            else:
                app_logger.info("Відео потік завершився.")
                self.stop_video()
        except Exception as e:
            self.handle_error("ERR-SYS-500", f"Помилка в циклі обробки кадру: {e}")
            self.stop_video()

    def save_results(self):
        if self.last_frame_to_save is None:
            messagebox.showwarning("Warning", "Немає результату для збереження!")
            return

        try:
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            base_filename = f"saved_results/result_{timestamp}"

            img_filename = base_filename + ".jpg"
            cv2.imwrite(img_filename, self.last_frame_to_save)

            txt_filename = base_filename + ".txt"
            log_content = self.text_results.get(1.0, tk.END).strip()

            with open(txt_filename, "w", encoding="utf-8") as f:
                f.write(f"Date/Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Image File: {img_filename}\n")
                f.write("-" * 20 + "\n")
                f.write("DETECTED OBJECTS:\n")
                f.write(log_content + "\n")

            app_logger.info(f"Збережено результати: {img_filename}")
            messagebox.showinfo("Saved", f"Файли збережено:\n1. {img_filename}\n2. {txt_filename}")
        except Exception as e:
            self.handle_error("ERR-SYS-500", f"Помилка запису файлів на диск: {e}")

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        app_logger.debug(f"Стан відео змінено: {'Пауза' if self.is_paused else 'Відтворення'}")
        if self.is_paused:
            self.btn_pause.config(text="▶ Resume")
            if self.last_frame_to_save is not None:
                self.text_results.insert(tk.END, "\n[PAUSED]\n")
        else:
            self.btn_pause.config(text="⏸ Pause")

    def stop_video(self):
        self.is_running = False
        self.is_paused = False
        if self.cap:
            self.cap.release()
        self.cap = None
        self.btn_pause.config(state="disabled")
        self.btn_stop.config(state="disabled")
        app_logger.info("Відео/камеру зупинено.")

    def resize_for_canvas(self, cv_image):
        pil_img = Image.fromarray(cv_image)
        pil_img.thumbnail((400, 400))
        return pil_img

    def log_results(self, result):
        self.text_results.delete(1.0, tk.END)
        if len(result.boxes) == 0:
            self.text_results.insert(tk.END, "No objects detected.")
            return

        inference_time = result.speed["inference"]
        self.text_results.insert(tk.END, f"Speed: {inference_time:.1f}ms\n")
        self.text_results.insert(tk.END, "-" * 20 + "\n")

        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = result.names[cls]
            self.text_results.insert(tk.END, f"{name}: {conf * 100:.1f}%\n")

            # Локальне логування в консоль/файл
            app_logger.debug(f"Знайдено: {name} ({conf * 100:.1f}%)")


if __name__ == "__main__":
    app_logger.info("--- ЗАПУСК ДОДАТКУ ---")
    main_window = tk.Tk()
    app = RoadSignDetectorApp(main_window)
    main_window.mainloop()
