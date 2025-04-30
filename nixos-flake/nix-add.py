import gi
gi.require_version('Gtk', '4.0') # Используем GTK 4
# Если GTK 4 нет, попробуйте '3.0' и адаптируйте код (см. комментарии в коде)
# Добавляем Pango для корректного WrapMode
from gi.repository import Gtk, GLib, Gio, Pango

import subprocess
import json
import os
import sys
import threading
import re

# --- Функция поиска пакетов (ИСПРАВЛЕНА для обработки единого JSON) ---
def search_nix_packages(query):
    """
    Ищет пакеты с помощью 'nix search' и возвращает словарь и сообщение об ошибке.
    Ключ словаря - уникальный сокращенный атрибут пакета.
    Значение - словарь {'display_name': str, 'description': str}.
    """
    print(f"🔍 Поиск пакетов по запросу: '{query}'...")
    packages = {}
    error_message = None
    try:
        result = subprocess.run(
            ['nix', 'search', 'nixpkgs', query, '--json'],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        # --- Отладка: Показываем сырой вывод ---
        print("\n--- RAW STDOUT ---")
        print(repr(result.stdout))
        print("--- END RAW STDOUT ---\n")
        # --- Конец отладки ---

        stdout_processed = result.stdout.strip()
        if not stdout_processed:
             print("--- STDOUT пуст после strip() ---")
             return {}, "Нет вывода от nix search"

        # --- ИСПРАВЛЕНИЕ: Парсим весь вывод как ОДИН JSON объект ---
        try:
            all_pkg_data = json.loads(stdout_processed)
            if not isinstance(all_pkg_data, dict):
                 raise json.JSONDecodeError("Ожидался словарь JSON верхнего уровня", stdout_processed, 0)
            print(f"--- Успешно распарсен основной JSON, найдено ключей (пакетов): {len(all_pkg_data)} ---") # DEBUG
        except json.JSONDecodeError as e:
            error_message = f"Ошибка парсинга основного JSON: {e}"
            print(error_message, file=sys.stderr)
            print(f"Проблемный вывод: {repr(stdout_processed)}", file=sys.stderr)
            return {}, error_message

        # --- ИСПРАВЛЕНИЕ: Итерируем по ключам (атрибутам) полученного словаря ---
        for attr_name, pkg_info in all_pkg_data.items():
            # attr_name - это полный атрибут (напр., legacyPackages.x86_64-linux.plank)
            # pkg_info - это словарь {'description': ..., 'pname': ..., 'version': ...}
            print(f"\n--- Обработка атрибута: {attr_name} ---") # DEBUG
            try:
                # --- Формируем уникальный ключ атрибута (short_attr_key) ---
                # (Логика извлечения short_attr_key остается прежней)
                attr_parts = attr_name.split('.')
                short_attr_key = attr_name # Значение по умолчанию
                if len(attr_parts) > 1:
                     platform_suffix = None
                     for suffix in ['.x86_64-linux', '.aarch64-linux', '.x86_64-darwin', '.aarch64-darwin']:
                          if attr_name.endswith(suffix):
                               platform_suffix = suffix
                               break
                     start_index = 1
                     if len(attr_parts) > 2 and attr_parts[1] == 'legacyPackages':
                         start_index = 2
                     end_index = len(attr_parts)
                     if platform_suffix:
                          num_platform_parts = len(platform_suffix.split('.')) -1
                          end_index = len(attr_parts) - num_platform_parts
                     if start_index < end_index:
                          short_attr_key = '.'.join(attr_parts[start_index:end_index])
                     elif start_index == 1 and len(attr_parts) == 2:
                          short_attr_key = attr_parts[start_index]
                     if not short_attr_key and len(attr_parts) > 1:
                         short_attr_key = attr_parts[-1]
                if not short_attr_key:
                    short_attr_key = attr_name.split('.')[-1] if '.' in attr_name else attr_name

                # Получаем имя и описание из pkg_info
                simple_name = pkg_info.get('pname', short_attr_key)
                description = pkg_info.get('description', 'Нет описания')

                # Добавляем в наш словарь packages
                packages[short_attr_key] = {
                    'display_name': simple_name,
                    'description': description
                }
                print(f"DEBUG: Добавлен ключ: {short_attr_key}, Имя: {simple_name}") # DEBUG

            except (IndexError, KeyError, TypeError) as e: # Ловим ошибки при обработке конкретного пакета
                print(f"ОШИБКА обработки данных для пакета {attr_name}: {e}", file=sys.stderr)
                # Продолжаем со следующим пакетом
                continue

    # --- Обработка ошибок subprocess и других ---
    except FileNotFoundError:
        error_message = "Ошибка: команда 'nix' не найдена. Убедитесь, что Nix установлен."
        print(error_message, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        nix_error = e.stderr.strip()
        if not nix_error:
             nix_error = f"Команда 'nix search' завершилась с кодом {e.returncode}"
        error_message = f"Ошибка при выполнении 'nix search': {nix_error}"
        print(error_message, file=sys.stderr)
        if e.stdout: # Печатаем stdout если он был при ошибке
             print("--- RAW STDOUT (при ошибке CalledProcessError) ---")
             print(repr(e.stdout))
             print("--- END RAW STDOUT ---")
    except Exception as e:
        error_message = f"Неизвестная ошибка при поиске: {e}"
        print(error_message, file=sys.stderr)

    print(f"\nDEBUG: search_nix_packages возвращает {len(packages)} пакетов.")
    return packages, error_message

# --- Класс приложения GTK ---
class NixSearchApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id="com.example.nixsearchapp",
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS, **kwargs)
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = NixSearchWindow(application=self)
        self.window.present()

# --- Класс главного окна ---
class NixSearchWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(title="Поиск пакетов Nix", *args, **kwargs)
        self.set_default_size(600, 450)
        self.search_running = False

        # --- Виджеты ---
        self.search_entry = Gtk.SearchEntry(placeholder_text="Введите название пакета...")
        self.search_button = Gtk.Button(label="Найти")
        self.results_listbox = Gtk.ListBox()
        self.results_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.scrolled_window = Gtk.ScrolledWindow(vexpand=True)
        self.scrolled_window.set_child(self.results_listbox)
        self.status_label = Gtk.Label(label="Введите запрос для поиска.", xalign=0)
        self.add_button = Gtk.Button(label="Добавить выбранный пакет", sensitive=False)

        # --- Компоновка ---
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.append(self.search_entry)
        header_box.append(self.search_button)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        main_box.append(header_box)
        main_box.append(self.scrolled_window)
        main_box.append(self.status_label)
        main_box.append(self.add_button)
        self.set_child(main_box)

        # --- Сигналы ---
        self.search_button.connect("clicked", self.on_search_clicked)
        self.search_entry.connect("activate", self.on_search_clicked)
        self.results_listbox.connect("row-selected", self.on_package_selected)
        # TODO: self.add_button.connect("clicked", self.on_add_package_clicked)

    def on_search_clicked(self, widget):
        query = self.search_entry.get_text().strip()
        if not query or self.search_running:
            return
        self.search_running = True
        self.status_label.set_text(f"🔍 Поиск '{query}'...")
        self.search_button.set_sensitive(False)
        self.search_entry.set_sensitive(False)
        self.results_listbox.set_sensitive(False)
        self.add_button.set_sensitive(False)
        self.clear_results_list()
        thread = threading.Thread(target=self.run_search_thread, args=(query,))
        thread.daemon = True
        thread.start()

    def run_search_thread(self, query):
        packages, error_message = search_nix_packages(query)
        GLib.idle_add(self.update_ui_after_search, packages, error_message)

    def update_ui_after_search(self, packages, error_message):
        if error_message:
            self.status_label.set_text(f"❌ {error_message}")
            self.clear_results_list()
        elif not packages:
            self.status_label.set_text("🚫 Ничего не найдено.")
            self.clear_results_list()
        else:
            self.status_label.set_text(f"✅ Найдено пакетов: {len(packages)}")
            self.populate_results_list(packages)
            self.results_listbox.set_sensitive(True)
        self.search_running = False
        self.search_button.set_sensitive(True)
        self.search_entry.set_sensitive(True)
        # Кнопка добавления активируется при выборе пакета
        # self.add_button.set_sensitive(False) # Не нужно здесь
        return GLib.SOURCE_REMOVE

    def clear_results_list(self):
        child = self.results_listbox.get_first_child()
        while child:
            self.results_listbox.remove(child)
            child = self.results_listbox.get_first_child()

    def populate_results_list(self, packages):
        self.clear_results_list()
        print(f"DEBUG: populate_results_list получила {len(packages)} пакетов.")
        display_name_counts = {}
        for attr_key, pkg_data in packages.items():
            d_name = pkg_data['display_name']
            display_name_counts[d_name] = display_name_counts.get(d_name, 0) + 1
        sorted_package_items = sorted(packages.items(), key=lambda item: item[1]['display_name'])

        for attr_key, pkg_data in sorted_package_items:
            name_to_display = pkg_data['display_name']
            description = pkg_data['description']
            if display_name_counts.get(name_to_display, 1) > 1:
                name_to_display = f"{name_to_display} ({attr_key})"

            row = Gtk.ListBoxRow()
            row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=10, margin_end=10, margin_top=5, margin_bottom=5)
            name_label = Gtk.Label(label=name_to_display, xalign=0, selectable=True)
            name_label.set_tooltip_text(f"Атрибут: {attr_key}\n{description or 'Нет описания'}")
            desc_label = Gtk.Label(xalign=0, wrap=True)
            desc_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            desc_label.set_markup(f"<small><i>{GLib.markup_escape_text(description or 'Нет описания')}</i></small>")
            desc_label.set_tooltip_text(description or 'Нет описания')
            row_box.append(name_label)
            row_box.append(desc_label)
            row.set_child(row_box)
            row.pkg_attr_key = attr_key
            self.results_listbox.append(row)

    def on_package_selected(self, listbox, row):
        if row:
            selected_package_key = row.pkg_attr_key
            try:
                 name_label_widget = row.get_child().get_first_child()
                 if isinstance(name_label_widget, Gtk.Label):
                      selected_package_display = name_label_widget.get_text()
                 else:
                      selected_package_display = selected_package_key
            except AttributeError:
                 selected_package_display = selected_package_key
            self.status_label.set_text(f"Выбран: {selected_package_display} (Атрибут: {selected_package_key})")
            self.add_button.set_sensitive(True)
            print(f"Выбран атрибут: {selected_package_key}")
        else:
            self.status_label.set_text("Выберите пакет из списка.")
            self.add_button.set_sensitive(False)

    # def on_add_package_clicked(self, widget):
    #     # ... (Логика добавления пакета - TODO) ...
    #     pass

# --- Запуск приложения ---
if __name__ == "__main__":
    try:
        subprocess.run(['nix', '--version'], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("Критическая ошибка: команда 'nix' не найдена в PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
         print(f"Критическая ошибка: не удалось выполнить 'nix --version'. Ошибка: {e.stderr}", file=sys.stderr)
         sys.exit(1)

    app = NixSearchApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
