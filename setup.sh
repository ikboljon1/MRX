#!/bin/bash

echo "--- Начало установки зависимостей для MRX Project ---"

# --- Шаг 1: Обновление системы и установка системных пакетов ---
echo "--> Обновление списка пакетов..."
sudo apt-get update

echo "--> Установка системных зависимостей..."
sudo apt-get install -y python3-pip python3-venv git portaudio19-dev libasound2-dev libportaudio2 libportaudiocpp0 ffmpeg

# --- Шаг 2: Создание и активация виртуального окружения ---
echo "--> Создание виртуального окружения '.venv'..."
python3 -m venv .venv

echo "--> Активация виртуального окружения..."
source .venv/bin/activate

# --- Шаг 3: Установка Python библиотек ---
echo "--> Обновление pip..."
pip install --upgrade pip

echo "--> Установка библиотек из requirements.txt..."
pip install -r requirements.txt

# --- Шаг 4: Установка PyTorch (специальная команда для RPi) ---
# Стандартная установка torch через pip может не сработать на RPi ARM
echo "--> Установка совместимой версии PyTorch..."
pip install --no-cache-dir torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cpu

echo "--- Установка завершена! ---"
echo "Для запуска проекта используйте следующие команды:"
echo "1. source .venv/bin/activate"
echo "2. python3 main_async.py"