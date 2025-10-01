#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Emaktab Auto - Главный файл приложения
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from emaktab_auto import EmaktabAutoApp

if __name__ == '__main__':
    try:
        app = EmaktabAutoApp()
        app.run()
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        sys.exit(1)
