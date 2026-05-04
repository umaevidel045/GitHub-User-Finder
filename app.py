import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os


# Файл для сохранения избранных пользователей
FAVORITES_FILE = "favorites.json"


class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Загрузка избранных пользователей
        self.favorites = self.load_favorites()

        # Создание интерфейса
        self.create_widgets()

        # Текущие результаты поиска
        self.current_results = []

    def create_widgets(self):
        """Создание всех виджетов интерфейса"""
        # Верхняя рамка для поиска
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)

        # Метка и поле ввода
        ttk.Label(search_frame, text="Поиск пользователя GitHub:").pack(side=tk.LEFT, padx=(0, 10))

        self.search_entry = ttk.Entry(search_frame, width=30, font=("Arial", 12))
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.search_users())

        # Кнопка поиска
        self.search_button = ttk.Button(search_frame, text="Найти", command=self.search_users)
        self.search_button.pack(side=tk.LEFT)

        # Статусная строка
        self.status_label = ttk.Label(search_frame, text="Готов к работе", foreground="gray")
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Рамка для результатов
        results_frame = ttk.LabelFrame(self.root, text="Результаты поиска", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Создание Treeview для отображения результатов
        columns = ("avatar", "username", "user_id", "url")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)

        # Настройка колонок
        self.results_tree.heading("avatar", text="Аватар")
        self.results_tree.heading("username", text="Имя пользователя")
        self.results_tree.heading("user_id", text="ID")
        self.results_tree.heading("url", text="Ссылка")

        self.results_tree.column("avatar", width=80, anchor="center")
        self.results_tree.column("username", width=200)
        self.results_tree.column("user_id", width=80, anchor="center")
        self.results_tree.column("url", width=250)

        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Привязка двойного клика для открытия ссылки
        self.results_tree.bind("<Double-1>", self.open_github_profile)

        # Рамка для действий с пользователем
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        # Кнопки действий
        self.add_favorite_button = ttk.Button(
            action_frame,
            text="⭐ Добавить в избранное",
            command=self.add_to_favorites,
            state=tk.DISABLED
        )
        self.add_favorite_button.pack(side=tk.LEFT, padx=5)

        self.view_favorites_button = ttk.Button(
            action_frame,
            text="Показать избранное",
            command=self.show_favorites
        )
        self.view_favorites_button.pack(side=tk.LEFT, padx=5)

        # Рамка для избранных пользователей
        self.favorites_frame = ttk.LabelFrame(self.root, text="Избранные пользователи", padding="10")
        self.favorites_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Treeview для избранных
        self.favorites_tree = ttk.Treeview(self.favorites_frame, columns=("username", "user_id"), show="headings", height=6)
        self.favorites_tree.heading("username", text="Имя пользователя")
        self.favorites_tree.heading("user_id", text="ID")
        self.favorites_tree.column("username", width=200)
        self.favorites_tree.column("user_id", width=100, anchor="center")

        fav_scrollbar = ttk.Scrollbar(self.favorites_frame, orient=tk.VERTICAL, command=self.favorites_tree.yview)
        self.favorites_tree.configure(yscrollcommand=fav_scrollbar.set)
        self.favorites_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Привязка двойного клика для удаления из избранного
        self.favorites_tree.bind("<Double-1>", self.remove_from_favorites)

        # Кнопка обновления избранных
        self.refresh_favorites_button = ttk.Button(
            self.favorites_frame,
            text=" Обновить",
            command=self.refresh_favorites_display
        )
        self.refresh_favorites_button.pack(side=tk.BOTTOM, pady=5)

        # Обновление отображения избранных
        self.refresh_favorites_display()

    def search_users(self):
        """Поиск пользователей GitHub"""
        query = self.search_entry.get().strip()

        # Проверка корректности ввода
        if not query:
            messagebox.showwarning("Предупреждение", "Поле поиска не может быть пустым!")
            self.status_label.config(text="Ошибка: пустой поисковый запрос", foreground="red")
            return

        self.status_label.config(text="Поиск...", foreground="blue")
        self.search_button.config(state=tk.DISABLED)
        self.root.update()

        try:
            # API запрос к GitHub
            url = f"https://api.github.com/search/users?q={query}&per_page=20"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                users = data.get("items", [])

                if users:
                    self.display_results(users)
                    self.status_label.config(text=f"Найдено пользователей: {len(users)}", foreground="green")
                else:
                    self.clear_results()
                    messagebox.showinfo("Информация", "Пользователи не найдены")
                    self.status_label.config(text="Пользователи не найдены", foreground="orange")

            elif response.status_code == 403:
                messagebox.showerror("Ошибка", "Превышен лимит запросов к API GitHub. Попробуйте позже.")
                self.status_label.config(text="Ошибка API: лимит запросов", foreground="red")
            else:
                messagebox.showerror("Ошибка", f"Ошибка API: {response.status_code}")
                self.status_label.config(text=f"Ошибка API: {response.status_code}", foreground="red")

        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка соединения: {str(e)}")
            self.status_label.config(text="Ошибка соединения", foreground="red")
        finally:
            self.search_button.config(state=tk.NORMAL)

    def display_results(self, users):
        """Отображение результатов поиска в Treeview"""
        self.clear_results()
        self.current_results = users

        for user in users:
            # Получение дополнительной информации о пользователе
            username = user.get("login", "Unknown")
            user_id = user.get("id", "N/A")
            url = user.get("html_url", "#")
            avatar_url = user.get("avatar_url", "")

            # Вставляем в таблицу
            self.results_tree.insert("", tk.END, values=("🖼️", username, user_id, url))

        # Включаем кнопку добавления в избранное
        self.add_favorite_button.config(state=tk.NORMAL)

    def clear_results(self):
        """Очистка результатов поиска"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.current_results = []
        self.add_favorite_button.config(state=tk.DISABLED)

    def get_selected_user(self):
        """Получение выбранного пользователя из результатов поиска"""
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите пользователя из результатов поиска")
            return None

        values = self.results_tree.item(selected[0])["values"]
        if len(values) >= 3:
            return {
                "username": values[1],
                "user_id": values[2],
                "url": values[3] if len(values) > 3 else ""
            }
        return None

    def add_to_favorites(self):
        """Добавление выбранного пользователя в избранное"""
        user = self.get_selected_user()
        if not user:
            return

        # Проверка, не добавлен ли уже пользователь
        if user["user_id"] in [fav["user_id"] for fav in self.favorites]:
            messagebox.showinfo("Информация", f"Пользователь {user['username']} уже в избранном")
            return

        # Добавление в избранное
        self.favorites.append(user)
        self.save_favorites()
        self.refresh_favorites_display()
        messagebox.showinfo("Успех", f"Пользователь {user['username']} добавлен в избранное")
        self.status_label.config(text=f"Добавлен в избранное: {user['username']}", foreground="green")

    def remove_from_favorites(self, event=None):
        """Удаление пользователя из избранного (двойной клик)"""
        selected = self.favorites_tree.selection()
        if not selected:
            return

        values = self.favorites_tree.item(selected[0])["values"]
        if len(values) >= 2:
            username = values[0]
            user_id = values[1]

            # Поиск и удаление пользователя
            for i, fav in enumerate(self.favorites):
                if fav["user_id"] == user_id:
                    del self.favorites[i]
                    break

            self.save_favorites()
            self.refresh_favorites_display()
            messagebox.showinfo("Успех", f"Пользователь {username} удален из избранного")
            self.status_label.config(text=f"Удален из избранного: {username}", foreground="orange")

    def show_favorites(self):
        """Отображение избранных пользователей (просто выделяем рамку)"""
        if not self.favorites:
            messagebox.showinfo("Информация", "Список избранных пользователей пуст")
        else:
            messagebox.showinfo("Информация", f"В избранном {len(self.favorites)} пользователей\n\nДвойной клик для удаления")

    def refresh_favorites_display(self):
        """Обновление отображения избранных пользователей"""
        # Очистка текущего отображения
        for item in self.favorites_tree.get_children():
            self.favorites_tree.delete(item)

        # Заполнение избранными пользователями
        for fav in self.favorites:
            self.favorites_tree.insert("", tk.END, values=(fav["username"], fav["user_id"]))

    def open_github_profile(self, event):
        """Открытие профиля GitHub в браузере"""
        selected = self.results_tree.selection()
        if not selected:
            return

        values = self.results_tree.item(selected[0])["values"]
        if len(values) >= 4 and values[3] != "#":
            import webbrowser
            webbrowser.open(values[3])
            self.status_label.config(text=f"Открыт профиль: {values[1]}", foreground="blue")

    def load_favorites(self):
        """Загрузка избранных пользователей из JSON файла"""
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_favorites(self):
        """Сохранение избранных пользователей в JSON файл"""
        try:
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except IOError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить избранное: {str(e)}")


def main():
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()


if __name__ == "__main__":
    main()